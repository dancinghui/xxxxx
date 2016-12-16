#include "stdafx.h"

#ifdef __APPLE__
#include <Python/Python.h>
#else
#include <Python.h>
#endif

#include <openssl/md5.h>
#include "base/lock.h"
#ifndef _WIN32
#include <sys/syscall.h>
#include <sys/file.h>
#endif


CLock g_lock;

PyObject * import_module(PyObject *, PyObject * args)
{
	char * name = 0;
	int n = PyArg_ParseTuple(args, "s", &name);
	if (!n) return NULL;

	//build path by name....
	char * p = strrchr(name, '/');
	if (!p)
	{
	    int len = (int)strlen(name);
	    if (len>3 && strcmp(name+len-3, ".py")==0)
	    {
	        name[len-3] = 0;
	        PyObject * a = PyImport_ImportModule(name);
	        name[len-3] = '.';
	        return a;
	    }
	    else
			return PyImport_ImportModule(name);
	}
	else
	{
		PyObject * robj = 0;

		PyObject * str = Py_BuildValue("s#", name, p - name);
		PyObject * sysobj = PyImport_ImportModule("sys");
		PyObject * strpath = Py_BuildValue("s", "path");
		g_lock.Lock();
		PyObject * oldlst = PyObject_GetAttr(sysobj, strpath);

		int oldsz = (int)PyList_Size(oldlst);
		PyObject * newlst = PyList_New(oldsz + 1);

		PyList_SET_ITEM(newlst, 0, str);
		for (int i = 0; i<oldsz; ++i)
		{
			PyList_SET_ITEM(newlst, i + 1, PyList_GET_ITEM(oldlst, i));
		}

		PyObject_SetAttr(sysobj, strpath, newlst);
		size_t plen = strlen(++p);
		if (plen>3 && _stricmp(p + plen - 3, ".py") == 0)
		{
			p[plen - 3] = 0;
			robj = PyImport_ImportModule(p);
			p[plen - 3] = '.';
		}
		else
			robj = PyImport_ImportModule(p);
		PyObject_SetAttr(sysobj, strpath, oldlst);

		for (int i = 0; i<oldsz + 1; ++i)
			PyList_SET_ITEM(newlst, i, NULL);
		g_lock.Unlock();

		Py_XDECREF(strpath);
		Py_XDECREF(sysobj);
		Py_XDECREF(oldlst);
		Py_XDECREF(newlst);
		Py_XDECREF(str);
		return robj;
	}
}

const char * md5hex(const char * s, size_t len)
{
	unsigned char md[16];
	MD5_CTX ctx;
	MD5_Init(&ctx);
	MD5_Update(&ctx, s, len);
	MD5_Final(md, &ctx);
	char rs[40] = { 0 };
	const char* tbl = "0123456789abcdef";
	for (int i = 0; i < 16; ++i)
	{
		rs[i * 2 + 0] = tbl[md[i] >> 4];
		rs[i * 2 + 1] = tbl[md[i] & 0xf];
	}
	return strdup(rs);
}

#ifdef _WIN32
long gettid()
{
	return GetCurrentThreadId();
}
#elif defined(__APPLE__)
long gettid()
{
	uint64_t tid;
	pthread_threadid_np(NULL, &tid);
	return (long)tid;
}
#else
long gettid()
{
	return (long)syscall(SYS_gettid);
}
#endif

int64_t mp_append_log(const char * logfile, const char * logs, int len)
{
	if (!logfile || !logs || !*logfile || len < 0)
		return -2;

	struct stat st;
	memset(&st, 0, sizeof(st));
	int fd = open(logfile, O_APPEND|O_CREAT|O_WRONLY, 0644);
	if (fd < 0)
		return -1;
	
	flock(fd, LOCK_EX);
	fstat(fd, &st);
	write(fd, logs, len);
	//fsync(fd);
	flock(fd, LOCK_UN);
	close(fd);
	static_assert(sizeof(st.st_size)==8, "must support large file.");
	return st.st_size;
}
