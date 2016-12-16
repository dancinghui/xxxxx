#include "stdafx.h"
#include "lock.h"
#include "atomic.h"

static void yield_or_delay(int & t)
{
	if (t++ <= 0)
		return;
	if (t <= 10)
	{
#ifdef _WIN32
		Sleep(0);
#else
		sched_yield();
#endif
		return;
	}
	if (t>30) t = 30;
	Sleep(t * 2);
}

void CABLock::LockA()
{
	int d = -100;
	for (;;)
	{
		int v = m_vv;
		if (v < 0)
			yield_or_delay(d);
		else
		{
			if (atomops::lock_comp_swap(&m_vv, v, v + 1))
				return;
		}
	}
}
void CABLock::UnlockA()
{
	atomops::lock_dec(&m_vv);
}
void CABLock::LockB()
{
	int d = -100;
	for (;;)
	{
		int v = m_vv;
		if (v > 0)
			yield_or_delay(d);
		else
		{
			if (atomops::lock_comp_swap(&m_vv, v, v - 1))
				return;
		}
	}
}
void CABLock::UnlockB()
{
	atomops::lock_inc(&m_vv);
}

CSimpLock::CSimpLock() : m_lv(0)
{
}

void CSimpLock::Lock()
{
	for (int i= -SPINCOUNT;;)
	{
		if (TryLock()) return;
		yield_or_delay(i);
	}
}

void CSimpLock::Unlock()
{
	atomops::lock_dec(&m_lv);
}

bool CSimpLock::TryLock()
{
	if (atomops::lock_inc(&m_lv) == 1)
		return true;
	atomops::lock_dec(&m_lv);
	return false;
}


//================rw lock=======================
CSimpRWLock::CSimpRWLock() :m_value(0)
{
}

CSimpRWLock::~CSimpRWLock()
{
#if defined(_WIN32) && defined(_DEBUG)
	if (m_value) __debugbreak();
#endif
}

bool CSimpRWLock::RTryLock()
{
	int oldvalue = m_value;
	if (oldvalue >= 0)
	{
		return atomops::lock_comp_swap(&m_value, oldvalue, oldvalue + 1);
	}
	return false;
}

void CSimpRWLock::RLock()
{
	int d = -1000;
	for (;;)
	{
		int oldvalue = m_value;
		if (oldvalue >= 0)
		{
			if (atomops::lock_comp_swap(&m_value, oldvalue, oldvalue + 1))
				return; //ok
			yield_or_delay(d);
		}
		else //writing.
			yield_or_delay(d);
	}
}

void CSimpRWLock::RUnlock()
{
	atomops::lock_dec(&m_value);
}

bool CSimpRWLock::WTryLock()
{
	return atomops::lock_comp_swap(&m_value, 0, -9999);
}

void CSimpRWLock::WLock()
{
	int tryc = 0;
	for (;;)
	{
		if (atomops::lock_comp_swap(&m_value, 0, -9999))
			return;
		yield_or_delay(tryc);
	}
}

void CSimpRWLock::WUnlock()
{
	int tryc = 0;
	for (;;)
	{
		if (atomops::lock_comp_swap(&m_value, -9999, 0))
			return;
		yield_or_delay(tryc);
	}
}
