#include "stdafx.h"
#include "jobq.h"
#include "killcheck.h"

#ifdef _WIN32
#include "../../../getjd/lab/shared/modhelper.h"
#else
#include "modhelper.h"
#endif


class CPyJobQueue : public CJobQueue
{
public:
	bool init(PyObject* args, PyObject* kwds)
	{
		char * fn = 0;
		int n = PyArg_ParseTuple(args, "s", &fn);
		if (!n) return false;
		if (CJobQueue::init(fn))
			return true;

		char errs[1000];
		snprintf(errs, sizeof(errs), "unable to open file %s", fn);
		CPyModuleHelper::GetInstance().SetErrStr(__LINE__, errs);
		return false;
	}

	PyObject* get_job(int64_t tid, const char * msk)
	{
		string vs;
		bool ismain = false;
		bool bg = false;

		for (int i=0; i<2; ++i)
		{
			KillCheck _k;
			bg = CJobQueue::get_job(vs, ismain, tid, msk);
			while (!bg && errno == EINTR)
			{
				errno = 0;
				bg = CJobQueue::get_job(vs, ismain, tid, msk);
			}
			if (bg) break;
		}
		
		if (bg)
		{
			return Py_BuildValue("(sO)", vs.c_str(), ismain ? Py_True : Py_False);
		}
		else
			return Py_BuildValue("(OO)", Py_None, Py_None);
	}
	bool add_main_job_range(const char * info, int64_t minv, int64_t maxv, int step)
	{
		KillCheck _;
		return CJobQueue::add_main_job_range(info, minv, maxv, step);
	}
	bool add_main_job_file(const char * info, const char * fname, unsigned int beginline, unsigned int endline)
	{
		KillCheck _;
		return CJobQueue::add_main_job_file(info, fname, beginline, endline);
	}
	bool add_main_job(const char * info)
	{
		KillCheck _;
		return CJobQueue::add_main_job(info);
	}
	bool add_job(const char * info)
	{
		KillCheck _;
		return CJobQueue::add_job(info);
	}
	bool readd_job(const char * info)
	{
		KillCheck _;
		return CJobQueue::readd_job(info);
	}
};

void init_pyjobq()
{
	static PythonObjectFactory<CPyJobQueue> jq("JobQueue", "a job queue object for multi-processes access. init args: (storage_filename)");
	jq.add_this_method<__COUNTER__>("get_job",
		"get job from queue.\n"
		"args:(tid, qmask). returns: (job,ismain)\n"
		"qmask is a string masks which queue to check a job.\n"
		"m for main job queue\n"
		"n for normal job queue\n"
		"f for failed job queue\n"
		"so 'mnf' is a good choice for this arg.\n"
		"NULL takes the same effect as 'mnf' for this arg.\n",
		&CPyJobQueue::get_job, "NL|s");
	jq.add_this_method<__COUNTER__>("add_main_job_range", "add a range-based main job. args:(json_template, minvalue, maxvalue, step)",
		&CPyJobQueue::add_main_job_range, "!sLLi" );
	jq.add_this_method<__COUNTER__>("add_main_job_file", "add a file-based main job. args:(json_template, filename, beginline, endline)",
		&CPyJobQueue::add_main_job_file, "!ssII");
	jq.add_this_method<__COUNTER__>("add_main_job", "add a main job", &CPyJobQueue::add_main_job, "!s");
	jq.add_this_method<__COUNTER__>("add_job", "add a job", &CPyJobQueue::add_job, "!s");
	jq.add_this_method<__COUNTER__>("readd_job", "re add a failed job", &CPyJobQueue::readd_job, "!s");
	jq.add_this_method<__COUNTER__>("get_size", "get job count in this queue", &CPyJobQueue::get_size, "k"); //k:unsigned long => PyInt
	jq.add_this_method<__COUNTER__>("get_mqsz", "get main job count in this queue", &CPyJobQueue::get_mqsz, "k");
	jq.apply();
}
