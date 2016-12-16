/*
 *  macwin.h
 *  utillib
 *
 *  Created by li xungeng on 11/14/10.
 *  Copyright 2010 tx. All rights reserved.
 *
 */
#pragma once

//
//               macros and types.
//
#ifdef _WIN32
#define _SSIZE_T_DEFINED
typedef ptrdiff_t ssize_t;
typedef int socklen_t;
typedef unsigned int uint;
#else
typedef unsigned int DWORD;
typedef unsigned char BYTE;
typedef unsigned short WORD;
typedef int BOOL;
typedef unsigned int UINT;
typedef int SOCKET;
typedef long long __int64;

#define TRUE 1
#define FALSE 0
#define CP_UTF8 65001
#define INVALID_SOCKET (-1)
#define __assume(x)
#define _T(x) x

#ifndef __stdcall
#define __stdcall
#endif

#define _stricmp strcasecmp
#define _strnicmp strncasecmp
#define _vsnprintf vsnprintf
#define _vsnwprintf vswprintf
#define _snprintf snprintf
#define _atoi64 atoll
#define _strtoi64 strtoll
#define closesocket close
#define ioctlsocket(a,b,c) ioctl(a,b,c)

typedef const char * LPCSTR;
typedef const char * LPCTSTR;
typedef const wchar_t * LPCWSTR;
typedef void * PVOID;
typedef wchar_t WCHAR;
typedef void* HANDLE;
typedef char TCHAR;
#endif


#ifdef __cplusplus
#define extc extern "C"
#else
#define extc
#endif

extc void useVar(void * ptr);
extc int64_t GetTickCount64b();
#ifdef _WIN32
extc int inet_aton(const char *cp, struct in_addr *inp);
extc char * getpass(const char *prompt);
#else
extc DWORD GetTickCount();
extc DWORD GetCurrentProcessId();
extc DWORD GetCurrentThreadId();
extc int _vscprintf(const char * fmt, va_list va);
extc int _vscwprintf(const wchar_t * fmt, va_list va);
extc void Sleep(DWORD to);
extc int _wtoi(const wchar_t * wc);
extc int GetLastError();
#define do_syscall(s) ({ int r; for (;;) {\
		r = s; if (r<0 && errno==EINTR) continue; else break; } \
		r; })
#endif

extc int new_thread(int (*pfunc)(void*, int), void * arg, int arg2, void ** pphandle);
extc int xrand();

#define __MYCOUNTER__(x) x
#define STRINGIFY_1(x) #x
#define STRINGIFY(x) STRINGIFY_1(x)

#if (defined(_DEBUG) || defined(DEBUG))
extc void cptf_MYAssert(int v, const char * desc, int line, const char * file);
#define MYASSERT(x)	do{cptf_MYAssert((x)!=0,#x,__LINE__,__FILE__);}while(0)
#else
#define MYASSERT(x) do{  }while(0)
#endif

#ifdef _WIN32
#define __thread __declspec(thread)
#endif
