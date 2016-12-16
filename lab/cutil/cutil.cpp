#include "stdafx.h"
#include <openssl/md5.h>
#include <unordered_set>
#include <unordered_map>
#ifdef _WIN32
#include <windows.h>
#else
#include <sys/syscall.h>
#include <sys/types.h>
#endif
#include "base/lock.h"
#include "hashm.h"
#include "modhelper.h"
#include "fhtml.h"
#include "qqptlogin.h"
#include "kvstore.h"


long gettid();
const char * md5hex(const char * s, size_t len);
PyObject * import_module(PyObject *, PyObject * args);
int64_t mp_append_log(const char * logfile, const char * logs, int len);

static int get_version()
{
	return 103;
}


class CPyHasher : public CHashTable
{
public:
	static void MD5_Buffer(const void * mem, size_t len, unsigned char * md)
	{
		MD5_CTX ctx;
		MD5_Init(&ctx);
		MD5_Update(&ctx, mem, len);
		MD5_Final(md, &ctx);
	}
public:
	int hashinc(const char * s, size_t len)
	{
		unsigned char md[16];
		MD5_Buffer(s, len, md);
		return this->Inc(md);
	}
	int hashlookup(const char * s, size_t len)
	{
		unsigned char md[16];
		MD5_Buffer(s, len, md);
		return this->Lookup(md);
	}
};

CHashTable g_hashtable;

void debug_ref(const char * name, int line, PyObject * obj)
{
	fprintf(stderr, "line:%d %s ref=%d\n", line, name, (int)obj->ob_refcnt);
}
#define DBGREF(x) debug_ref(#x, __LINE__, x)

void * CFindForm::pyobj()
{
	PyObject * dict1 =  PyDict_New();
	for (auto i : m_kvs)
	{
		PyObject * v = Py_BuildValue("s", i.second.c_str());
		PyDict_SetItemString(dict1, i.first.c_str(), v);
		Py_XDECREF(v);
	}
	PyObject * dict2 = PyDict_New();
	for (auto i : m_submit)
	{
		PyObject * v = Py_BuildValue("s", i.second.c_str());
		PyDict_SetItemString(dict2, i.first.c_str(), v);
		Py_XDECREF(v);
	}
	return Py_BuildValue("(NN)", dict1, dict2);
}

struct QQEnc
{
	string res;
	const char * encrypt_qq_pwd(const char * passwd, const char * salt, int len, const char * imgcode)
	{
		if (getEncryption(passwd, string(salt, len), imgcode, res))
			return res.c_str();
		return "";
	}
};

/*
void * get_html_node(const char * html, int len, int place, int which);
void * get_html_text(const char * html, int len, int place, int which);
void * get_html_text_hash(const char * html, int len, int place, int which);
*/
void init_pyjobq();
PyMODINIT_FUNC PYM_VISIBLE initcutil(void)
{
	CPyModuleHelper & mh = CPyModuleHelper::GetInstance();
	mh.add_method<__COUNTER__>("version", "get version", get_version, "i");
	mh.add_method<__COUNTER__>("gettid", "get current thread id", gettid, "l");
	mh.add_method<__COUNTER__>("md5hex", "md5 hex result of string", md5hex, "Fss#");
	mh.add_alt_this_method<__COUNTER__>("hashlookup", "hash lookup of string", &CPyHasher::hashlookup, "is#", &g_hashtable);
	mh.add_alt_this_method<__COUNTER__>("hashinc", "hash inc of string", &CPyHasher::hashinc, "is#", &g_hashtable);
	mh.add_method_raw("import_module", "import a module", import_module);
	mh.add_method<__COUNTER__>("mp_append_log", "append log for multi-processes", mp_append_log, "Lss#");

	typedef CPyFuncs<CFindHtmlFuncs> FF;
	mh.add_newobj_method<__COUNTER__, FF>("process_form", "process web form", &FF::process_form, "Ns#ii");
	mh.add_newobj_method<__COUNTER__, FF>("get_html_node", "html node", &FF::get_html_node, "Ns#ii");
	mh.add_newobj_method<__COUNTER__, FF>("get_html_text", "html text", &FF::get_html_text, "Ns#ii");
	mh.add_newobj_method<__COUNTER__, FF>("get_html_text_hash", "html text hash", &FF::get_html_text_hash, "Ns#ii");
	mh.add_newobj_method<__COUNTER__, FF>("check_html", "checking html", &FF::check_html, "!s#");
	mh.add_newobj_method<__COUNTER__,QQEnc>("encrypt_qq_pwd", "encrypt qq pwd for ptlogin", &QQEnc::encrypt_qq_pwd, "sss#s");

	mh.init("cutil", "cutil module");
	init_pyjobq();
	init_py_kvstore();
}

