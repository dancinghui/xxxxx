#pragma once
#include "base/lock.h"
#include "base/atomic.h"

#ifdef _WIN32
class CWaitable
{
	HANDLE hEvent;
public:
	CWaitable(){ hEvent = CreateEvent(NULL, FALSE, FALSE, NULL); }
	~CWaitable(){ CloseHandle(hEvent); }
	void raise(){ SetEvent(hEvent); }
	bool wait(int timeo = -1)
	{
		return WaitForSingleObject(hEvent, timeo) == WAIT_OBJECT_0;
	}
};
#else
class CWaitable
{
	pthread_cond_t cond;
	pthread_mutex_t mutex;
	bool the_event;
public:
	CWaitable()
	{
		pthread_mutex_init(&mutex, NULL);
		pthread_cond_init(&cond, NULL);
		the_event = false;
	}
	~CWaitable()
	{
		pthread_cond_destroy(&cond);
		pthread_mutex_destroy(&mutex);
	}
	void raise()
	{
		pthread_mutex_lock(&mutex);
		the_event = true;
		pthread_cond_signal(&cond);
		pthread_mutex_unlock(&mutex);
	}
	static void get_abst(int timeo, struct timespec & ts)
	{
		struct timeval tv;
		gettimeofday(&tv, 0);
		ts.tv_sec = tv.tv_sec;
		ts.tv_nsec = tv.tv_usec * 1000;
		if (timeo >= 0)
		{
			ts.tv_sec += timeo / 1000;
			ts.tv_nsec += (timeo % 1000) * 1000000;
			if (ts.tv_nsec >= 1000000000)
			{
				++ts.tv_sec;
				ts.tv_nsec -= 1000000000;
			}
		}
		else
		{
			ts.tv_sec = 0;
			ts.tv_nsec = 0;
		}
	}
	bool wait(int timeo = -1)
	{
		bool br = false;
		int err;
		struct timespec ts;
		get_abst(timeo, ts);
		pthread_mutex_lock(&mutex);
		while (!the_event)
		{
			err = timeo >= 0 ? pthread_cond_timedwait(&cond, &mutex, &ts) : pthread_cond_wait(&cond, &mutex);
			if (err == ETIMEDOUT) break;
		}
		if (the_event) br = true;
		pthread_mutex_unlock(&mutex);
		return br;
	}
};
#endif

class CAnyCondition : public CWaitable
{
	long m_cnt;
public:
	CAnyCondition(long cnt) :m_cnt(cnt){}
	void Add(long cnt)
	{
		long xv = m_cnt;
		if (! atomops::lock_comp_swap(&m_cnt, xv, xv + cnt))
			return Add(cnt);
		if (xv <= 0 && xv + cnt>0) raise();
	}
};

#ifdef _WIN32
class CCondVariable
{
	CRITICAL_SECTION m_cs;
	CONDITION_VARIABLE m_cv;
public:
	CCondVariable()
	{
		InitializeCriticalSection(&m_cs);
		InitializeConditionVariable(&m_cv);
	}
	~CCondVariable()
	{
		DeleteCriticalSection(&m_cs);
	}
	template <class FuncT>
	void do_and_raise(FuncT obj)
	{
		EnterCriticalSection(&m_cs);
		obj();
		WakeAllConditionVariable(&m_cv);
		LeaveCriticalSection(&m_cs);
	}
	template <class FuncT>
	bool wait_condition(FuncT check)
	{
		bool br = false;
		EnterCriticalSection(&m_cs);
		while (!check())
		{
			SleepConditionVariableCS(&m_cv, &m_cs, INFINITE);
		}
		LeaveCriticalSection(&m_cs);
		return br;
	}
private:
	CCondVariable(const CCondVariable&);
};
#else
class CCondVariable
{
	pthread_cond_t cond;
	pthread_mutex_t mutex;
public:
	CCondVariable()
	{
		pthread_mutex_init(&mutex, NULL);
		pthread_cond_init(&cond, NULL);
	}
	~CCondVariable()
	{
		pthread_cond_destroy(&cond);
		pthread_mutex_destroy(&mutex);
	}
	template <class FuncT>
	void do_and_raise(FuncT obj)
	{
		pthread_mutex_lock(&mutex);
		obj();
		pthread_cond_signal(&cond);
		pthread_mutex_unlock(&mutex);
	}
	template <class FuncT>
	void do_and_raise_all(FuncT obj)
	{
		pthread_mutex_lock(&mutex);
		obj();
		pthread_cond_broadcast(&cond);
		pthread_mutex_unlock(&mutex);
	}
	template <class FuncT>
	bool wait_condition(FuncT check)
	{
		bool br = false;
		pthread_mutex_lock(&mutex);
		while (!check())
		{
			pthread_cond_wait(&cond, &mutex);
		}
		pthread_mutex_unlock(&mutex);
		return br;
	}
private:
	CCondVariable(const CCondVariable&);
};
#endif

class CParallelWorkMgr
{
	typedef bool(*parallel_func)(CLock* plock, int idx, int thdidx, void ** pars);
public:
	CLock m_lock;
	long m_created;
	long m_running;
	long m_started;
	long m_indx;
	long m_thdidx;
	void ** m_pars;
	parallel_func m_func;

protected:
	void parallel_proc(int thdidx);
	static unsigned int __stdcall parallel_proc(void * arg);
	static void * parallel_proc1(void *arg);

public:
	void do_work(int count, void ** pars, parallel_func func, DWORD slp = 10);
};

class CWorkerMgr
{
protected:
	CCondVariable m_cond;
	std::list<void *> m_jobs;

public:
	CWorkerMgr();
	virtual ~CWorkerMgr();

private:
	static int thread_run(void * a, int);

protected:
	virtual int thread_run();
	virtual void * get_token();
	virtual void process_job(void*job, void* token) = 0;
	void * get_job();
	void add_job(void * job);
	void init_thread(int nth = 0);
};
