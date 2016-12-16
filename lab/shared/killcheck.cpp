#include "stdafx.h"
#include "killcheck.h"
#include "base/lock.h"
#include "process_single.h"
#include "base/atomic.h"

struct VOnKillFuncs
{
	virtual void Register(void(*func)(void *), void * arg) = 0;
	virtual void Unregister(void(*func)(void *), void * arg) = 0;

	virtual void Enter() = 0;
	virtual void Leave() = 0;
	virtual void Kill() = 0;
};


static __thread int g_lock_token;

struct OnKillFuncs : VOnKillFuncs
{
	struct FuncCall
	{
		void(*func)(void*);
		void * arg;

		bool operator < (const FuncCall & ano) const
		{
			if (func != ano.func)
				return func < ano.func;
			return arg < ano.arg;
		}

		void call() const
		{
			func(arg);
		}
	};

	CLock m_lock;
	set<FuncCall> m_funcs;
	int threads_cnt, threads_idle, kill_pending;

	virtual void Register(void(*func)(void *), void * arg)
	{
		FuncCall fc;
		fc.func=func;
		fc.arg = arg;

		m_lock.Lock();
		m_funcs.insert(fc);
		m_lock.Unlock();
	}
	virtual void Unregister(void(*func)(void *), void * arg)
	{
		FuncCall fc;
		fc.func=func;
		fc.arg = arg;

		m_lock.Lock();
		m_funcs.erase(fc);
		m_lock.Unlock();
	}
	void CallAll()
	{
		m_lock.Lock();
		for (auto it = m_funcs.begin(); it != m_funcs.end(); ++it)
		{
			it->call();
		}
		m_funcs.clear();
		m_lock.Unlock();
	}

	void Enter()
	{
		if (g_lock_token == 0)
		{
			g_lock_token = 1;
			int n = atomops::lock_inc(&threads_cnt);
			if (n == 1)
			{
				m_lock.Lock();
				do_init();
				m_lock.Unlock();
			}
			atomops::lock_inc(&threads_idle);
		}
		m_lock.Lock();
		do_check();
		atomops::lock_dec(&threads_idle);
		m_lock.Unlock();
	}

	void Leave()
	{
		m_lock.Lock();
		atomops::lock_inc(&threads_idle);
		do_check();
		m_lock.Unlock();
	}
	void do_check()
	{
		if (threads_idle == threads_cnt)
		{
			if (kill_pending)
			{
				CallAll();
#ifndef _WIN32
				kill(getpid(), SIGKILL);
#endif
				abort();
			}
		}
	}
	void Kill()
	{
		atomops::lock_inc(&kill_pending);
		m_lock.Lock();
		do_check();
		m_lock.Unlock();
	}
	void do_init();
};

static OnKillFuncs onk;

void KillCheck::Register(void (*func)(void *), void * arg)
{
	VOnKillFuncs * f = &onk;
	f = (VOnKillFuncs *)process_single("com.ipin.cfuncs.killcheck.ptr", f);
	return f->Register(func, arg);
}

void KillCheck::Unregister(void (*func)(void*), void * arg)
{
	VOnKillFuncs * f = &onk;
	f = (VOnKillFuncs *)process_single("com.ipin.cfuncs.killcheck.ptr", f);
	return f->Unregister(func, arg);
}

KillCheck::KillCheck()
{
	VOnKillFuncs * f = &onk;
	f = (VOnKillFuncs *)process_single("com.ipin.cfuncs.killcheck.ptr", f);
	f->Enter();
}

KillCheck::~KillCheck()
{
	VOnKillFuncs * f = &onk;
	f = (VOnKillFuncs *)process_single("com.ipin.cfuncs.killcheck.ptr", f);
	f->Leave();
}



#ifdef _WIN32

void OnKillFuncs::do_init()
{
	//TODO: on windows, we should create a window to recieve the terminate msg.
	//and also register console CtrlC handler and Terminate Handler.
}

#else

static void handler1(int sig)
{
	VOnKillFuncs * f = &onk;
	f = (VOnKillFuncs *)process_single("com.ipin.cfuncs.killcheck.ptr", f);
	f->Kill();
}

void OnKillFuncs::do_init()
{
	signal(SIGUSR1, handler1);
	signal(SIGTERM, handler1);
	signal(SIGINT, handler1);
}

#endif
