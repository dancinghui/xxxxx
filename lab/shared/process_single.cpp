#include "stdafx.h"
#include "process_single.h"
#include "base/lock.h"

struct VProcessOnce
{
	virtual void * process_single(const char * name, void * defptr) = 0;
};

struct VProcessOnceImpl : VProcessOnce
{
	CLock m_lock;
	map<string, void *> m_values;

	void * process_single(const char * name, void * defptr)
	{
		string mname(name);
		void * rptr = 0;
		m_lock.Lock();
		{
			void * & ptr = m_values[mname];
			if (!ptr) ptr = defptr;
			rptr = ptr;
		}
		m_lock.Unlock();
		return rptr;
	}
};

static VProcessOnce * get_base()
{
	static VProcessOnceImpl one;
	VProcessOnce * defv = &one;
	char prefix[100], value[100], *oldvalue;
	sprintf(prefix, "%lu:", (unsigned long)GetCurrentProcessId());
	sprintf(value, "%s%p", prefix, defv);
	const char * envname = "SWPROCESSONCEBASEPTR";
#ifdef _WIN32
	WNDCLASSEXA  cls = { sizeof(cls) };
	cls.hInstance = (HINSTANCE)GetModuleHandle(0);
	cls.lpszClassName = envname;
	cls.lpfnWndProc = (WNDPROC)defv;
	cls.style = CS_HREDRAW | CS_VREDRAW;
	ATOM atom = RegisterClassExA(&cls);
	if (atom)
	{
		return defv;
	}
	else
	{
		WNDCLASSEXA cls1 = { sizeof(cls1) };
		GetClassInfoExA(cls.hInstance, cls.lpszClassName, &cls1);
		return (VProcessOnce*)cls1.lpfnWndProc;
	}
#else
	for (;;)
	{
		oldvalue = getenv(envname);
		if (oldvalue && strncmp(oldvalue, prefix, strlen(prefix)) == 0)
		{
			oldvalue += strlen(prefix);
			return (VProcessOnce*)strtoull(oldvalue, 0, 16);
		}
		setenv(envname, value, 1);
	}
#endif
}

void * process_single(const char * name, void * defptr)
{
	return get_base()->process_single(name, defptr);
}
