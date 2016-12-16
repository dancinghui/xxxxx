#pragma once
#include "atomic.h"

namespace LockUtil
{
	template <class Lock>
	struct CAutoLock
	{
		Lock & lock;
		CAutoLock(Lock & lock) : lock(lock){ lock.Lock(); }
		~CAutoLock(){ lock.Unlock(); }
	};

	template <class RWLOCK>
	struct CAutoRLock
	{
		RWLOCK & lock;
		CAutoRLock(RWLOCK & lock) :lock(lock){ lock.RLock(); }
		~CAutoRLock(){ lock.RUnlock(); }
	};

	template <class RWLOCK>
	struct CAutoWLock
	{
		RWLOCK & lock;
		CAutoWLock(RWLOCK & lock) :lock(lock){ lock.WLock(); }
		~CAutoWLock(){ lock.WUnlock(); }
	};
}

class CSimpLock
{
	volatile int m_lv;
	enum { SPINCOUNT = 0x10000 };
public:
	static void yield()
	{
#ifdef _WIN32
		Sleep(0);
#else
		sched_yield();
#endif
	}
public:
	CSimpLock();
	void Lock();
	void Unlock();
	bool TryLock();
public:
	static CSimpLock * from(volatile int * var)
	{
		return (CSimpLock*)var;
	}
	typedef LockUtil::CAutoLock<CSimpLock> AutoLock;
};

class CABLock
{
	volatile int m_vv;
public:
	CABLock():m_vv(0){}
	void LockA();
	void UnlockA();
	void LockB();
	void UnlockB();
public:
	static CABLock * from(volatile int * var){ return (CABLock*)var; }

	struct AutoALock{
		CABLock & m_l;
		AutoALock(CABLock & l) : m_l(l){ m_l.LockA(); }
		AutoALock(volatile int * lk) : m_l(*(CABLock*)lk){ m_l.LockA(); }
		~AutoALock(){ m_l.UnlockA(); }
	};
	struct AutoBLock{
		CABLock & m_l;
		AutoBLock(CABLock & l) :m_l(l){ m_l.LockB(); }
		AutoBLock(volatile int * lk) : m_l(*(CABLock*)lk){ m_l.LockB(); }
		~AutoBLock(){ m_l.UnlockB(); }
	};
};

//misc.
#ifdef _WIN32
class CLock : protected CRITICAL_SECTION
{
public:
	CLock(){ InitializeCriticalSection(this); }
	~CLock(){ DeleteCriticalSection(this); }
	void Lock(){ if (this)EnterCriticalSection(this); }
	void Unlock(){ if (this)LeaveCriticalSection(this); }
	bool TryLock()
	{
		if (!this)return true;
		return !!TryEnterCriticalSection(this);
	}
	typedef LockUtil::CAutoLock<CLock> AutoLock;
};
#else
class CLock
{
	pthread_mutex_t mutex;
	pthread_mutexattr_t mutex_attr;
public:
	CLock()
	{
		pthread_mutexattr_init(&mutex_attr);
		pthread_mutexattr_settype(&mutex_attr, PTHREAD_MUTEX_RECURSIVE);
		pthread_mutex_init(&mutex, &mutex_attr);
	}
	~CLock()
	{
		pthread_mutex_destroy(&mutex);
		pthread_mutexattr_destroy(&mutex_attr);
	}
	void Lock(){ CLock * ptr = this; if (ptr) pthread_mutex_lock(&mutex); }
	void Unlock(){ CLock * ptr = this; if (ptr) pthread_mutex_unlock(&mutex); }
	bool TryLock()
	{
		CLock * ptr = this;
		if (!ptr) return true;
		return pthread_mutex_trylock(&mutex) == 0;
	}
	typedef LockUtil::CAutoLock<CLock> AutoLock;
};
#endif

class CSimpRWLock
{
	//0: 一般情况。 >0 在读 <0在写.
	//写操作只能把0变负，读操作可以把0或正加1.
private:
	volatile int m_value;

public:
	CSimpRWLock();
	~CSimpRWLock();
	bool RTryLock();
	void RLock();
	void RUnlock();
	bool WTryLock();
	void WLock();
	void WUnlock();

public:
	static CSimpRWLock * from(volatile int * v)
	{
		return (CSimpRWLock*)v;
	}
	typedef LockUtil::CAutoRLock<CSimpRWLock> AutoRLock;
	typedef LockUtil::CAutoWLock<CSimpRWLock> AutoWLock;
};

#ifndef _WIN32
class CPthreadRWLock
{
private:
	pthread_rwlock_t m_rwlock;
public:
	CPthreadRWLock()
	{
		pthread_rwlock_t xx = PTHREAD_RWLOCK_INITIALIZER;
		memcpy(&m_rwlock, &xx, sizeof(xx));
		pthread_rwlock_init(&m_rwlock, NULL);
	}
	~CPthreadRWLock()
	{
		pthread_rwlock_destroy(&m_rwlock);
	}
public:
	bool RTryLock()
	{
		return 0 == pthread_rwlock_tryrdlock(&m_rwlock);
	}
	void RLock()
	{
		pthread_rwlock_rdlock(&m_rwlock);
	}
	void RUnlock()
	{
		pthread_rwlock_unlock(&m_rwlock);
	}

	bool WTryLock()
	{
		return 0 == pthread_rwlock_trywrlock(&m_rwlock);
	}
	void WLock()
	{
		pthread_rwlock_wrlock(&m_rwlock);
	}
	void WUnlock()
	{
		pthread_rwlock_unlock(&m_rwlock);
	}
public:
	typedef LockUtil::CAutoRLock<CPthreadRWLock> AutoRLock;
	typedef LockUtil::CAutoWLock<CPthreadRWLock> AutoWLock;
};
typedef CPthreadRWLock CRWLock;
#else
class CMSRWLock
{
private:
	SRWLOCK m_SRWLock;
public:
	CMSRWLock()
	{
		InitializeSRWLock(&m_SRWLock);
	}
	~CMSRWLock(){}
public:
	bool RTryLock()
	{
		return !!TryAcquireSRWLockShared(&m_SRWLock);
	}
	void RLock()
	{
		AcquireSRWLockShared(&m_SRWLock);
	}
	void RUnlock()
	{
		ReleaseSRWLockShared(&m_SRWLock);
	}

	bool WTryLock()
	{
		return !!TryAcquireSRWLockExclusive(&m_SRWLock);
	}
	void WLock()
	{
		AcquireSRWLockExclusive(&m_SRWLock);
	}
	void WUnlock()
	{
		ReleaseSRWLockExclusive(&m_SRWLock);
	}
public:
	typedef LockUtil::CAutoRLock<CMSRWLock> AutoRLock;
	typedef LockUtil::CAutoWLock<CMSRWLock> AutoWLock;
};

typedef CMSRWLock CRWLock;
#endif

template <class BaseLock>
class CWBRWLock
{
private:
	BaseLock m_baselock;
	volatile long m_wpending;
public:
	CWBRWLock() :m_wpending(0){}
	void WLock()
	{
		atomops::lock_inc(&m_wpending);
		m_baselock.WLock();
		atomops::lock_dec(&m_wpending);
	}
	bool WTryLock()
	{
		return m_baselock.WTryLock();
	}
	void WUnlock(){ return m_baselock.WUnlock(); }
	void RLock()
	{
		while (m_wpending > 0)
			CSimpLock::yield();
		m_baselock.RLock();
	}
	bool RTryLock()
	{
		if (m_wpending > 0) return false;
		return m_baselock.RTryLock();
	}
	void RUnlock() { return m_baselock.RUnlock(); }
public:
	typedef LockUtil::CAutoRLock<CWBRWLock<BaseLock> > AutoRLock;
	typedef LockUtil::CAutoWLock<CWBRWLock<BaseLock> > AutoWLock;
};

namespace LockUtil
{
	template <class T>
	struct type_self
	{
		typedef T self;
	};
	struct Once{
		int cnt;
		Once() :cnt(0){}
		operator bool() { return cnt++ == 0; }
	};
	template <class T>
	struct CAutoLock2 : CAutoLock<T>
	{
		CAutoLock2(CLock & lock) :CAutoLock<T>(lock){}
		Once once;
	};
	template <class T>
	struct CAutoRLock2 : CAutoRLock < T >
	{
		CAutoRLock2(T & l) : CAutoRLock<T>(l){}
		Once once;
	};
	template <class T>
	struct CAutoWLock2 : CAutoWLock < T >
	{
		CAutoWLock2(T & l) : CAutoWLock<T>(l){}
		Once once;
	};
#define WITH_LOCK(lock) for (LockUtil::CAutoLock2<decltype(lock)> a_(lock); a_.once; )
#define WITH_RWLOCK_READ(lock) for (LockUtil::CAutoRLock2<decltype(lock)> a_(lock); a_.once; )
#define WITH_RWLOCK_WRITE(lock) for (LockUtil::CAutoWLock2<decltype(lock)> a_(lock); a_.once; )
}

#define ENSURE_LOCK(var)  LockUtil::type_self<decltype(var)>::self::AutoLock al_##var(var)

template <class T>
class CThreadedResource
{
protected:
	map<intptr_t, T*> m_res;
	CSimpLock m_lock;
public:
	CThreadedResource(){}
	~CThreadedResource()
	{
		m_lock.Lock();
		for (auto it = m_res.begin(); it != m_res.end(); ++it)
		{
			delete it->second;
			it->second = 0;
		}
		m_res.clear();
		m_lock.Unlock();
	}
	T * get(){
		intptr_t tid = GetCurrentThreadId();
		m_lock.Lock();
		T * & p = m_res[tid];
		if (!p) p = new T();
		m_lock.Unlock();
		return p;
	}
};
