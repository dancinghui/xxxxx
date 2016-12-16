#include "stdafx.h"
#include "base/lock.h"
#include "base/HelperFuncs.h"
#include "jobq.h"
#include <jansson.h>
#include "killcheck.h"

using namespace xptr;


static bool find_line(const char * fname, unsigned int beginline, size_t & filepos)
{
	size_t tsize = 1024 * 1024;
	FILE * fp = fopen(fname, "rb");
	if (!fp) return false;
	char * tempmem = (char*)malloc(tsize);
	size_t curline = 0;

	AUTOCLOSE(free, tempmem);
	AUTOCLOSE(fclose, fp);
	if (beginline == 0)
	{
		filepos = 0;
		return true;
	}
	else
	{
		filepos = 0;
		for (;;)
		{
			size_t r = fread(tempmem, 1, tsize, fp);
			for (size_t i = 0; i < r; ++i)
			{
				if (tempmem[i] != '\n') continue;
				++curline;
				if (curline == beginline)
				{
					filepos += i+1;
					return true;
				}
			}
			filepos += r;
			if (r == 0)break;
		}
		//not found.
		return false;
	}
}

static bool same_sign(int64_t a, int64_t b)
{
	if (a == 0 || b == 0) return true;
	return (a > 0 && b > 0) || (a < 0 && b < 0);
}

CJobQueue::CJobQueue(){}
CJobQueue::~CJobQueue()
{
	KillCheck::Unregister(&CJobQueue::save_pending, this);
}

bool CJobQueue::init(const char * fn)
{
	if (m_fm.init(fn))
	{
		JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
		if (jqinfo->magic != JobQueueInfo::MAGIC)
		{
			jqinfo->magic = JobQueueInfo::MAGIC;
			baseaddr_t ba = (baseaddr_t)m_fm.base();
			jqinfo->mq.first_init(ba);
			jqinfo->q2.first_init(ba);
			jqinfo->q3.first_init(ba);
			jqinfo->sz = 0;
			jqinfo->mqsz = 0;
			jqinfo->qlock = 0;
		}
		KillCheck::Register(&CJobQueue::save_pending, this);
		return true;
	}
	return false;
}

bool CJobQueue::get_job_normq_(JobQueueInfo * jqinfo, string & vs, bool & ismain)
{
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	double_list * x = 0;
	if (jqinfo->q2.popnext(x, ba))
	{
		JobObject * j = (JobObject*)x;
		MYASSERT(j->type == JobObject::TYPE_NORMAL);
		vs = j->json.rawptr(ba);
		m_fm.do_free(j->json);
		m_fm.do_free(j);
		-- jqinfo->sz;
		ismain = false;
		return true;
	}
	return false;
}

bool CJobQueue::get_job_mainq_(JobQueueInfo * jqinfo, string & vs, bool & ismain)
{
	json_error_t error;
	baseaddr_t ba = (baseaddr_t)m_fm.base();

	if (jqinfo->mq.next.rawptr(ba) != &jqinfo->mq)
	{
		JobObject * j = (JobObject*)jqinfo->mq.next.rawptr(ba);
		if (j->type == JobObject::TYPE_NORMAL)
		{
			jqinfo->mq.popnext(*(double_list**)&j, ba);
			vs = j->json.rawptr(ba);
			m_fm.do_free(j->json);
			m_fm.do_free(j);
			-- jqinfo->sz;
			-- jqinfo->mqsz;
			ismain = true;
			return true;
		}
		if (j->type == JobObject::TYPE_RANGE)
		{
			RangeJobObject * rj = (RangeJobObject*)j;

			int64_t value = rj->cur;
			json_t * js = json_loads((char*)rj->json.rawptr(ba), 0, &error);
			json_object_set_new(js, "value", json_integer(value));
			char * infox = json_dumps(js, JSON_SORT_KEYS);
			vs = infox;
			free(infox);
			json_decref(js);

			rj->cur += rj->step;
			if (!same_sign(rj->end - rj->cur, rj->step))
			{
				jqinfo->mq.popnext(*(double_list**)&j, ba);
				m_fm.do_free(rj->json);
				m_fm.do_free(rj);
				-- jqinfo->sz;
				-- jqinfo->mqsz;
			}
			ismain = true;
			return true;
		}
		if (j->type == JobObject::TYPE_FILE)
		{
			bool found = false;
			bool isend = false;
			FileJobObject * fj = (FileJobObject*)j;
			FILE * fp = fopen((char*)fj->filename.rawptr(ba), "rb");
			if (fp)
			{
				AUTO_CLOSE(fclose, fp);
				fseek(fp, fj->filepos, SEEK_SET);

				enum {MAXLINESIZE = 8*1024};
				char * mem = (char*)malloc(MAXLINESIZE);
				AUTOCLOSE(free, mem);
				int r = (int)fread(mem, 1, MAXLINESIZE, fp);
				if (r > 0)
				{
					json_t * js = json_loads(fj->json.rawptr(ba), 0, &error);
					if (js)
					{
						for (int i = 0; i <= r; ++i)
						{
							if (i == r || mem[i] == '\n')
							{
								fj->filepos += i + 1;
								int len = i;
								if (len > 0 && mem[len - 1] == '\r') --len;
								json_object_set_new(js, "line", json_stringn(mem, len));
								char * infox = json_dumps(js, JSON_SORT_KEYS);
								vs = infox;
								free(infox);
								ismain = true;
								found = true;
								fj->lines_remain--;
								isend = isend || fj->lines_remain < 0;
								break;
							}
						}
						json_decref(js);
					}
				}
				else
				{
					if (errno != EINTR)
						isend = true;
				}
			}
			if (isend || !found)
			{
				jqinfo->mq.popnext(*(double_list**)&j, ba);
				m_fm.do_free(fj->filename);
				m_fm.do_free(fj->json);
				m_fm.do_free(fj);
				-- jqinfo->sz;
				-- jqinfo->mqsz;
				errno = EINTR;
			}
			return found;
		}
	}
	return false;
}

bool CJobQueue::get_job_failq_(JobQueueInfo* jqinfo, string & vs, bool & ismain)
{
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	double_list * x = 0;
	if (jqinfo->q3.popnext(x, ba))
	{
		JobObject * j = (JobObject*)x;
		MYASSERT(j->type == JobObject::TYPE_NORMAL);
		vs = j->json.rawptr(ba);
		m_fm.do_free(j->json);
		m_fm.do_free(j);
		-- jqinfo->sz;
		ismain = false;
		return true;
	}
	return false;
}

void CJobQueue::save_pending()
{
	vector<string> jobs;
	m_lock.Lock();
	for (auto it=m_pending.begin(); it!=m_pending.end(); ++it)
	{
		jobs.push_back(it->second);
	}
	m_pending.clear();
	m_lock.Unlock();

	for (auto it = jobs.begin(); it!=jobs.end(); ++it)
	{
		add_job(it->c_str());
	}
}

bool CJobQueue::get_job(string &vs, bool &ismain, int64_t tid, const char * mask)
{
	if (get_job1(vs, ismain, mask))
	{
		//set the pending task.
		m_lock.Lock();
		m_pending[tid] = vs;
		m_lock.Unlock();
		return true;
	}
	return false;
}

bool CJobQueue::get_job1(string & vs, bool & ismain, const char * mask)
{
	bool get_mq = mask==0 || (strchr(mask, 'm') != 0);
	bool get_nq = mask==0 || (strchr(mask, 'n') != 0);
	bool get_fq = mask==0 || (strchr(mask, 'f') != 0);

	ENTER_FUNCO(&m_fm);
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
	CSimpLock * slock = CSimpLock::from(&jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);

	if (get_nq && get_job_normq_(jqinfo, vs, ismain))
		return true;

	if (get_fq && (xrand()%100<15) && get_job_failq_(jqinfo, vs, ismain))
		return true;

	if (get_mq && get_job_mainq_(jqinfo, vs, ismain))
		return true;

	if (get_fq && get_job_failq_(jqinfo, vs, ismain))
		return true;

	return false;
}

bool CJobQueue::add_main_job_range(const char * info, int64_t minv, int64_t maxv, int step) //{"type":type, "value":1122}
{
	if (!info || info[0] != '{') return false;
	if (!same_sign(maxv - minv, step)) return false;

	packed_ptr jsstr = m_fm.do_alloc(strlen(info)+1);
	packed_ptr rjobj = m_fm.do_alloc(sizeof(RangeJobObject));

	ENTER_FUNCO(&m_fm);
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();

	strcpy((char*)jsstr.rawptr(ba), info);
	RangeJobObject * j = (RangeJobObject*) rjobj.rawptr(ba);
	j->type = JobObject::TYPE_RANGE;
	j->lst.first_init(ba);
	j->retrycnt = 0;
	j->json.value_ = jsstr.value_;
	j->cur = minv;
	j->end = maxv;
	j->step = step;

	CSimpLock * slock = CSimpLock::from(& jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);
	jqinfo->mq.addprev(&j->lst, ba);
	++ jqinfo->sz;
	++ jqinfo->mqsz;
	return true;
}

bool CJobQueue::add_main_job_file(const char * info, const char * fname, unsigned int beginline, unsigned int endline)
{
	//{"type":type, "line":line}
	if (!info || info[0] != '{') return false;
	size_t filepos = 0;
	int64_t linesremain = endline == 0 ? INT64_MAX : endline - beginline;
	if (beginline != 0)
	{
		if (!find_line(fname, beginline, filepos))
			return false;
	}
	if (linesremain < 0)
		return false;

	packed_ptr jsstr = m_fm.do_alloc(strlen(info) + 1);
	packed_ptr fjobj = m_fm.do_alloc(sizeof(FileJobObject));
	packed_ptr fnstr = m_fm.do_alloc(strlen(fname) + 1);

	ENTER_FUNCO(&m_fm);
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();

	strcpy((char*)jsstr.rawptr(ba), info);
	strcpy((char*)fnstr.rawptr(ba), fname);

	FileJobObject * j = (FileJobObject*) fjobj.rawptr(ba);
	j->type = JobObject::TYPE_FILE;
	j->lst.first_init(ba);
	j->retrycnt = 0;
	j->json.value_ = jsstr.value_;
	j->filename.value_ = fnstr.value_;
	j->lines_remain = linesremain;
	j->filepos = filepos;

	CSimpLock * slock = CSimpLock::from(&jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);
	jqinfo->mq.addprev(&j->lst, ba);
	++ jqinfo->sz;
	++ jqinfo->mqsz;
	return true;
}

bool CJobQueue::add_main_job(const char * info)
{
	if (!info || info[0] != '{') return false;

	packed_ptr jsstr = m_fm.do_alloc(strlen(info) + 1);
	packed_ptr jobj = m_fm.do_alloc(sizeof(JobObject));

	ENTER_FUNCO(&m_fm);
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();

	strcpy((char*)jsstr.rawptr(ba), info);

	JobObject * j = (JobObject*)jobj.rawptr(ba);
	j->type = JobObject::TYPE_NORMAL;
	j->lst.first_init(ba);
	j->retrycnt = 0;
	j->json.value_ = jsstr.value_;

	CSimpLock * slock = CSimpLock::from(&jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);
	jqinfo->mq.addprev(&j->lst, ba);
	++ jqinfo->sz;
	++ jqinfo->mqsz;
	return true;
}

bool CJobQueue::add_job(const char * info)
{
	if (!info || info[0] != '{') return false;
	packed_ptr jsstr = m_fm.do_alloc(strlen(info) + 1);
	packed_ptr jobj = m_fm.do_alloc(sizeof(JobObject));

	ENTER_FUNCO(&m_fm);
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
	strcpy((char*)jsstr.rawptr(ba), info);

	JobObject * j = (JobObject*)jobj.rawptr(ba);
	j->type = JobObject::TYPE_NORMAL;
	j->lst.first_init(ba);
	j->retrycnt = 0;
	j->json.value_ = jsstr.value_;

	CSimpLock * slock = CSimpLock::from(&jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);
	jqinfo->q2.addnext(&j->lst, ba);
	++ jqinfo->sz;
	return true;
}

bool CJobQueue::readd_job(const char * info)
{
	if (!info || info[0] != '{') return false;
	const char * key = "_retrycnt_";
	json_error_t error;
	json_t * js = json_loads(info, 0, &error);
	json_t * z = json_object_get(js, key);

	int iv = 0;
	if (z == 0) ;
	else if (z->type == JSON_INTEGER)
	{
		iv = (int)json_integer_value(z);
		json_integer_set(z, iv + 1);
	}
	else if (z->type == JSON_STRING)
	{
		iv = atoi( json_string_value(z) );
		json_object_set_new(js, key, json_integer(iv + 1));
	}
	if (iv >= 50)
	{
		json_decref(js);
		return false;
	}

	json_object_set_new(js, key, json_integer(iv +1));

	char * infox = json_dumps(js, JSON_SORT_KEYS);
	json_decref(js);
	AUTOCLOSE(free, infox);

	packed_ptr jsstr = m_fm.do_alloc(strlen(infox) + 1);
	packed_ptr jobj = m_fm.do_alloc(sizeof(JobObject));

	ENTER_FUNCO(&m_fm);
	baseaddr_t ba = (baseaddr_t)m_fm.base();
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
	strcpy((char*)jsstr.rawptr(ba), infox);

	JobObject * j = (JobObject*)jobj.rawptr(ba);
	j->type = JobObject::TYPE_NORMAL;
	j->lst.first_init(ba);
	j->retrycnt = 0;
	j->json.value_ = jsstr.value_;

	CSimpLock * slock = CSimpLock::from(&jqinfo->qlock);
	CSimpLock::AutoLock _1(*slock);
	jqinfo->q3.addprev(&j->lst, ba);
	++ jqinfo->sz;
	return true;
}

size_t CJobQueue::get_size()
{
	CRWLock::AutoRLock _(m_fm.lock);
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
	return jqinfo->sz;
}

size_t CJobQueue::get_mqsz()
{
	CRWLock::AutoRLock _(m_fm.lock);
	JobQueueInfo * jqinfo = m_fm.get_app_space<JobQueueInfo>();
	return jqinfo->mqsz;
}
