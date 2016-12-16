#include "stdafx.h"
#include "base/HelperFuncs.h"
#include "base/atomic.h"
#include "synchronize.h"


#if 0
class CWaitable
{
	sem_t sm;
public:
	CWaitable(){ sem_init(&sm, 0, 0); }
	~CWaitable(){ sem_destroy(&sm); }
	void raise(){ sem_post(&sm); }
	bool wait(int timeo = -1)
	{
		for (;;)
		{
			int nr = timeo<0 ? sem_wait(&sm) : sem_timedwait(&sm, &ts);
			if (nr<0 && errno == EINTR) continue;
			return nr == 0;
		}
	}
};
class CWaitable
{
	int hd[2];
public:
	CWaitable(){ hd[0] = hd[1] = -1; pipe(hd); }
	~CWaitable(){ close(hd[0]); close(hd[1]); }
	void raise(){ char c = 0; write(hd[1], &c, 1); }
	void clear(){ char c = 0; read(hd[0], &c, 1); }
	bool wait(int timeo = -1)
	{
		pollfd pf = { hd[0], POLLIN };
		poll(&pf, 1, timeo);
		return pf.revents & POLLIN;
	}
};
#endif

void CParallelWorkMgr::parallel_proc(int thdidx)
{
	for (;;)
	{
		long idx = atomops::lock_inc(&m_indx);
		bool b = m_func(&m_lock, idx, thdidx, m_pars);
		if (!b) break;
	}
}

unsigned int __stdcall CParallelWorkMgr::parallel_proc(void * arg)
{
	CParallelWorkMgr * mgr = (CParallelWorkMgr *)arg;
	atomops::lock_inc(&mgr->m_started);
	atomops::lock_inc(&mgr->m_running);
	long thdidx = atomops::lock_inc(&mgr->m_thdidx);
	mgr->parallel_proc(thdidx);
	atomops::lock_dec(&mgr->m_running);
	return 0;
}

void * CParallelWorkMgr::parallel_proc1(void *arg)
{
	return (void*)(size_t)parallel_proc(arg);
}

void CParallelWorkMgr::do_work(int count, void ** pars, parallel_func func, DWORD slp)
{
	m_created = 0;
	m_running = 0;
	m_started = 0;
	m_indx = -1;
	m_thdidx = -1;

	m_pars = pars;
	m_func = func;
#ifdef _WIN32
	vector<HANDLE> thds;
	for (int i = 0; i < count; ++i)
	{
		unsigned int taddr;
		HANDLE hd = (HANDLE)_beginthreadex(0, 0, parallel_proc, this, 0, &taddr);
		if (hd)
		{
			thds.push_back(hd);
			++m_created;
		}
		Sleep(slp);
	}
	parallel_proc(InterlockedIncrement(&m_thdidx));
	//while (m_started != m_created) Sleep(200);
	//while (m_running > 0) Sleep(200);
	if (!thds.empty())
	{
		WaitForMultipleObjects((DWORD)thds.size(), &thds[0], TRUE, INFINITE);
		std::for_each(thds.begin(), thds.end(), CloseHandle);
		thds.clear();
	}
#else
	vector<pthread_t> thds;
	for (int i = 0; i<count; ++i)
	{
		pthread_t thd;
		int r = pthread_create(&thd, NULL, parallel_proc1, this);
		if (r == 0)
		{
			thds.push_back(thd);
			++m_created;
		}
		Sleep(slp);
	}
	parallel_proc(atomops::lock_inc(&m_thdidx));
	//while (m_started != m_created) Sleep(200);
	//while (m_running > 0) Sleep(200);
	for (size_t i = 0; i<thds.size(); ++i)
	{
		pthread_join(thds[i], NULL);
	}
	thds.clear();
#endif
}

//################cworkmgr####################################
CWorkerMgr::CWorkerMgr()
{
}

CWorkerMgr::~CWorkerMgr()
{
}

void CWorkerMgr::init_thread(int nth)
{
	if (nth <= 0)
	{
		int ncpu = Helper::get_cpu_count();
		nth = ncpu <= 1 ? 1 : (ncpu + 1);
	}
	for (int i = 0; i < nth; ++i)
	{
		new_thread(&CWorkerMgr::thread_run, this, 0, 0);
	}
}

int CWorkerMgr::thread_run(void * a, int)
{
	CWorkerMgr * this_ = (CWorkerMgr*)a;
	return this_->thread_run();
}

int CWorkerMgr::thread_run()
{
	void * token = get_token();
	for (;;)
	{
		void * job = get_job();
		process_job(job, token);
	}
	return 0;
}

void * CWorkerMgr::get_token()
{
	return 0;
}

void * CWorkerMgr::get_job()
{
	void * job = 0;
	m_cond.wait_condition([&]()->bool{
		if (!m_jobs.empty())
		{
			job = m_jobs.front();
			m_jobs.erase(m_jobs.begin());
			return true;
		}
		return false;
	});
	return job;
}

void CWorkerMgr::add_job(void * job)
{
	if (!job) return;
	m_cond.do_and_raise([&](){
		m_jobs.push_back(job);
	});
}
