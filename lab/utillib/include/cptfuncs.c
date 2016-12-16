/*
 *  macwin.c
 *  utillib
 *
 *  Created by li xungeng on 11/14/10.
 *  Copyright 2010 tx. All rights reserved.
 *
 */
#include <stdint.h>
#include <stdarg.h>
#include <wchar.h>
#include <time.h>
#include <stdio.h>
#include <memory.h>
#include <stdlib.h>
#include <errno.h>

#ifdef _WIN32
#include <Windows.h>
#include <process.h>
#else
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <pthread.h>
#include <errno.h>
#endif

#include "cptfuncs.h"

#if defined(_WIN32) && defined(_DEBUG)
void cptf_MYAssert(int v, const char * desc, int line, const char * file)
{
	char sbuf[512] = { 0 };
	if (v)return;
	_snprintf(sbuf, sizeof(sbuf),
		"File: %s\r\n"
		"Line: %d  pid: %d\r\n"
		"Assert expression:\r\n"
		"  %s\r\n", file, line, (int)GetCurrentProcessId(), desc);
	switch (MessageBoxA(0, sbuf, "ASSERT FAILED", MB_ICONHAND | MB_ABORTRETRYIGNORE | MB_SERVICE_NOTIFICATION))
	{
	case IDRETRY:
		__debugbreak();
		break;
	case IDIGNORE:
		break;
	case IDABORT:
	default:
		ExitProcess(1);
		break;
	}
}
#elif defined(__APPLE__)// && (defined(DEBUG) || defined(_DEBUG))
#include <CoreFoundation/CoreFoundation.h>
void cptf_MYAssert(int v, const char * desc, int line, const char * file)
{
	char sbuf[512] = { 0 };
	if (v)return;
	_snprintf(sbuf, sizeof(sbuf),
			"file: %s\r\n"
			"line: %d  pid: %d\r\n"
			"assert expression:\r\n"
			"  %s\r\n", file, line, (int)getpid(), desc);
	CFStringRef content = CFStringCreateWithCStringNoCopy(0, sbuf, kCFStringEncodingUTF8, kCFAllocatorNull);
	CFStringRef title = CFSTR("ASSERT FAILED");
	CFOptionFlags opf = 0;
	v = CFUserNotificationDisplayAlert(0, /*CFOptionFlags*/0, 0, 0, 0, title, content, CFSTR("IGNORE"), CFSTR("RETRY"), CFSTR("ABORT"), &opf);
	CFRelease(content);

	switch (opf)
	{
	case 1:
		__asm__("int3\n");
		break;
	case 0:
		break;
	case 2:
	default:
		abort();
		exit(1);
		break;
	}
}
#elif defined(__linux__) && (defined(_DEBUG) || defined(DEBUG))
void cptf_MYAssert(int v, const char * desc, int line, const char * file)
{
	unsigned int i;
	char sbuf[512] = { 0 };
	if (v)return;
	_snprintf(sbuf, sizeof(sbuf),
			"file: %s\r\n"
			"line: %d  pid: %d tid:%d\r\n"
			"assert expression:\r\n"
			"  %s\r\n", file, line, (int)getpid(), (int)GetCurrentThreadId(), desc);
	for (i=0; i<10; )
	{
		fprintf(stderr, "%s", sbuf);
		i = sleep(5);
	}
}
#endif

#ifdef __APPLE__
#include <mach/clock.h>
#include <mach/clock_types.h>
#include <mach/mach_host.h>
#include <mach/clock.h>
#include <pthread.h>

static int get_clock_ref()
{
	clock_serv_t clock_ref = 0;
	host_get_clock_service(mach_host_self(), SYSTEM_CLOCK, &clock_ref);
	return clock_ref;
}

static int darwin_clock_gettime_MONOTONIC(struct timespec *tp)
{
    static int clockinit = 0;
	static clock_serv_t clock_ref = 0;
    mach_timespec_t mach_tp = {0};

	if (clockinit == 0)
	{
		clockinit = 1;
		clock_ref = get_clock_ref();
	}

    kern_return_t ret = clock_get_time(clock_ref, &mach_tp);
    if (ret != KERN_SUCCESS) return -1;

	tp->tv_sec = mach_tp.tv_sec;
    tp->tv_nsec = mach_tp.tv_nsec;
    return 0;
}

int64_t GetTickCount64b()
{
	struct timespec ts = {0};
	int r = darwin_clock_gettime_MONOTONIC(&ts);
	if (r<0) return 1;
	int64_t a = (int64_t)ts.tv_sec * 1000 + ts.tv_nsec/1000000;
	return a;
}
#endif

#ifdef __linux__
int64_t GetTickCount64b()
{
	struct timespec ts;
	uint64_t tt;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	tt = (uint64_t)ts.tv_sec*1000 + ts.tv_nsec/1000000;
	return (int64_t)tt;
}
#endif

#ifdef _WIN32
static int64_t (*pGetTickCount64)() = 0;
static int64_t GetTickCount64_xp()
{
	volatile DWORD * p = (volatile DWORD*)0x7ffe0000;
	DWORD multi = p[1];
	if (p[0] == 0)
	{
		for (;;)
		{
			DWORD mx = p[0x324/4];
			DWORD a = p[0x320/4];
			if (mx == p[0x328/4])
			{
				uint64_t d1 = ((uint64_t)a * multi) >> 0x18;
				uint64_t d2 = ((uint64_t)mx * multi) << 0x8;
				return d1 + d2;
			}
			__nop();
			//__asm{pause};
		}
	}
	else
	{
		uint64_t d2 = (uint64_t)p[0] * multi;
		d2 = d2>>0x18;
		return (int64_t)d2;
	}
}

int64_t GetTickCount64b()
{
	if (! pGetTickCount64)
	{
		FARPROC fp = GetProcAddress(GetModuleHandleA("kernel32"), "GetTickCount64");
		pGetTickCount64 = fp ? (int64_t (*)())fp : GetTickCount64_xp;
	}
	return pGetTickCount64();
}

int inet_aton(const char *c, struct in_addr *dst)
{
	unsigned char *a = (unsigned char*)dst;
	unsigned int n, o;
	if (!c)
	{
		dst->s_addr = 0;
		return 0;
	}
	for (n = 0; n < 4; ++n)
	{
		if (*c < '0' || *c > '9')
			return 0;
		o = *c++ - '0';
		while(*c >= '0' && *c <= '9')
			if ((o = o * 10 + (*c++ - '0')) > 255)
				return 0;
		if (*c++ != (n == 3 ? '\0' : '.'))
			return 0;
		*a++ = (unsigned char)o;
	}
	return 1;
}
/*
int mkdir(const char *path, int mode)
{
	size_t len = strlen(path);
	WCHAR * wch = (WCHAR*) malloc(sizeof(WCHAR)*(len+2));
	int l2 = MultiByteToWideChar(CP_UTF8, 0, path, len, wch, len+1);
	BOOL b;

	wch[l2>=0?l2:0]=0;
	b = CreateDirectory(wch, 0);
	free(wch);
	return b?0:-1;
}
*/
#endif

#ifndef _WIN32
int GetLastError()
{
	return errno;
}
DWORD GetTickCount()
{
	return (DWORD)GetTickCount64b();
}
DWORD GetCurrentProcessId()
{
	return (DWORD)getpid();
}
DWORD GetCurrentThreadId()
{
#ifdef __APPLE__
	return syscall(SYS_thread_selfid);
#else
	return syscall(SYS_gettid);
#endif
}
void Sleep(DWORD to)
{
	useconds_t us = to;
	us *= 1000;
	usleep(us);
}
int _vscprintf(const char * fmt, va_list va)
{
	char c[2];
	return vsnprintf(c, 1, fmt, va);
}
int _vscwprintf(const wchar_t * fmt, va_list va)
{
	wchar_t * pb;
	int buf_size = 1024;
	while (buf_size < 1024*1024*20)
	{
		va_list args;
		va_copy(args, va);
		pb = (wchar_t*)malloc(buf_size*sizeof(wchar_t));
		int fmt_size = vswprintf(pb, buf_size, fmt, args);
		free(pb);
		if (fmt_size >= 0 && fmt_size<buf_size)
			return fmt_size;
		buf_size *= 2;
	}
	return -1;
}
int _wtoi(const wchar_t * wc)
{
	int x = 0;
	if (!wc) return x;
	while (*wc==' '||*wc=='\t'||*wc=='\r'||*wc=='\n') ++wc;

	int sign = 0;
	if (*wc=='+' || *wc=='-')
	{
		sign = *wc == '-';
		++wc;
	}
	for (;;)
	{
		wchar_t wch = *wc;
		if (wch>='0' && wch<='9')
			x = x*10 + wch-'0';
		else
			break;
		++ wc;
	}
	if (sign) x = -x;
	return x;
}
#endif

#define NELE 512
int xrand()
{
	static int r[NELE];
	static int i=0, v=0;
    int o;
	if (v==0)
	{
		r[0] = getpid()*10000+ (unsigned int)time(0)*1000;
		for (i=1; i<31; i++) {
			r[i] = (16807LL * r[i-1]) % 2147483647;
			if (r[i] < 0) {
				r[i] += 2147483647;
			}
		}
		for (i=31; i<34; i++) {
			r[i] = r[i-31];
		}
		for (i=34; i<344; i++) {
			r[i] = r[i-31] + r[i-3];
		}
		v=1;
	}
	o = r[i%NELE] = r[(i-31)%NELE] + r[(i-3)%NELE];
	++i;
	return ((unsigned int)o)>>1;
}

struct xth_
{
	int (*func)(void*, int);
	void * arg;
	int arg2;
};

#ifdef _WIN32
static unsigned int __stdcall win32_thd_wrap(void * arg0)
{
	int r;
	struct xth_ * arg = (struct xth_*)arg0;
	r = (*arg->func)(arg->arg, arg->arg2);
	free(arg);
	return r;
}
int new_thread(int (*pfunc)(void*,int), void * arg, int arg2, void ** handle)
{
	void * p;
	struct xth_ * t = (struct xth_*)malloc(sizeof(struct xth_));
	t->func = pfunc;
	t->arg = arg;
	t->arg2 = arg2;
	p = (void*) _beginthreadex(0, 0, win32_thd_wrap, t, 0, 0);
	if (handle) *handle = p;
	else CloseHandle((HANDLE)p);
	return !! p;
}
#else
static void * xnix_thd_wrap(void * arg0)
{
	int r;
	struct xth_ * arg = (struct xth_*)arg0;
	r = (*arg->func)(arg->arg, arg->arg2);
	free(arg);
	return (void*)(intptr_t)r;
}
int new_thread(int (*pfunc)(void*,int), void * arg, int arg2, void ** handle)
{
	pthread_t pth = 0;
	struct xth_ * t = (struct xth_*)malloc(sizeof(struct xth_));
	t->func = pfunc;
	t->arg = arg;
	t->arg2 = arg2;
	pthread_create(&pth, 0, xnix_thd_wrap, t);
	if (handle) *handle = (void*)pth;
	else pthread_detach(pth);
    return !!pth;
}
#endif

void useVar(void * ptr)
{
	char ch = "\0"[((uintptr_t)ptr) & 1];
	if (ch)	free((void*)(intptr_t)ch);
}
