#pragma once
#include "xptr.h"
#include "fmalloc.h"

class CJobQueue
{
public:
	struct JobObject
	{
		xptr::double_list lst;
		enum { TYPE_NORMAL, TYPE_FILE, TYPE_RANGE, SIZEX = 0x7fffffff } type;
		int retrycnt;
		xptr::packed_ptr_t<char> json;
	};

	struct FileJobObject : JobObject
	{
		xptr::packed_ptr_t<char> filename;
		int64_t filepos;
		int64_t lines_remain;
	};

	struct RangeJobObject : JobObject
	{
		int64_t cur;
		int64_t end;
		int step;
	};

	struct JobQueueInfo
	{
		enum { MAGIC = 0x514a504d };
		unsigned int magic;
		volatile int qlock;
		xptr::double_list mq;
		xptr::double_list q2;
		xptr::double_list q3;
		size_t sz;
		size_t mqsz;
	};

private:
	CFMalloc m_fm;
	CLock m_lock;
	map<int64_t, string> m_pending;

public:
	CJobQueue();
	~CJobQueue();
	bool init(const char * fn);
	bool get_job(string & vs, bool & ismain, int64_t tid, const char * mask="mnf");
	bool get_job1(string & vs, bool & ismain, const char * mask="mnf");

protected:
	bool get_job_mainq_(JobQueueInfo * jqinfo, string & vs, bool & ismain);
	bool get_job_normq_(JobQueueInfo * jqinfo, string & vs, bool & ismain);
	bool get_job_failq_(JobQueueInfo * jqinfo, string & vs, bool & ismain);

public:
	bool add_main_job_range(const char * info, int64_t minv, int64_t maxv, int step); //{"type":type, "value":1122}
	bool add_main_job_file(const char * info, const char * fname, unsigned int beginline, unsigned int endline); //{"type":type, "line":line}
	bool add_main_job(const char * info);
	bool add_job(const char * info);
	bool readd_job(const char * info);
	size_t get_size();
	size_t get_mqsz();
private:
	static void save_pending(void* ptr)
	{
		return ((CJobQueue*)ptr)->save_pending();
	}
	void save_pending();
};
