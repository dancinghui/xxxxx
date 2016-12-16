#include "stdafx.h"
#include "modhelper.h"
#include "../pagestore.h"
#include "../rbtdb.h"
#include "killcheck.h"

#define PS_VERSION 105

class CMongoPageStore4py : public CMongoPageStore
{
protected:
	void on_error(int code, const char * msg)
	{
		CPyModuleHelper::GetInstance().SetErrStr(msg);
	}
public:
	bool init(PyObject* args, PyObject* kwds)
	{
		const char *dburi=0, *colname=0;
		if (! PyArg_ParseTuple(args, "ss", &dburi, &colname))
			return false;
		if (!CMongoPageStore::init(dburi, colname))
		{
			on_error(-1, "init mongo db failed.");
			return false;
		}
		return true;
	}
	int version()
	{
		return PS_VERSION;
	}
};

class CRBFilePageStore4Py : protected CRBFilePageStore
{
protected:
	void on_error(int code, const char * msg)
	{
		CPyModuleHelper::GetInstance().SetErrStr(msg);
	}
public:
	typedef CRBFilePageStore parent_class;
	bool init(PyObject* args, PyObject* kwds)
	{
		const char *filename=0, *dburi=0, *colname=0;
		if (! PyArg_ParseTuple(args, "sss", &filename, &dburi, &colname))
			return false;
		KillCheck _k;
		if (! CRBFilePageStore::init(filename, dburi, colname) )
		{
			on_error(-1, "init failed.");
			return false;
		}
		return true;
	}
	bool has_item(const char * indexkey, const char * cs)
	{
		KillCheck _k;
		return parent_class::has_item(indexkey, cs);
	}
	bool has_new(const char * indexuri)
	{
		KillCheck _k;
		return parent_class::has_new(indexuri);
	}
	bool has_key(const char * indexuri)
	{
		KillCheck _k;
		return parent_class::has_key(indexuri);
	}
	bool update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime)
	{
		KillCheck _k;
		return parent_class::update_time(indexkey, contentsign, time, webtime);
	}
	bool upsert_doc(const char * key, const char * json)
	{
		KillCheck _k;
		return parent_class::upsert_doc(key, json);
	}
	int64_t get_page_time(const char * indexkey, const char * contentsign, int cslen)
	{
		KillCheck _k;
		return parent_class::get_page_time(indexkey, contentsign, cslen);
	}
	int version()
	{
		return PS_VERSION;
	}
};


template <class T>
void dumpxx(T obj)
{
	uintptr_t* ui = (uintptr_t*)&obj;
	printf("dumping %p\n", ui);
	for (int i=0; i*sizeof(uintptr_t)<sizeof(T); ++i)
	{
		printf("%llx\n", (unsigned long long) ui[i]);
	}
	printf("done\n");
}

PyMODINIT_FUNC PYM_VISIBLE initcpagestore(void)
{
	CMongoSupport::enable();

	CPyModuleHelper & mh = CPyModuleHelper::GetInstance();
	mh.init("cpagestore", "cpagestore module");

	static PythonObjectFactory<CMongoPageStore4py> hehe("PSObj", "a page store object");
	hehe.add_this_method<__COUNTER__>("dump", "dump contents function", &CMongoPageStore4py::dump, "v");
	hehe.add_this_method<__COUNTER__>("has_item", "has item by key and contentSign", &CMongoPageStore4py::has_item, "!ss");
	hehe.add_this_method<__COUNTER__>("has_new", "has recently updated item by key", &CMongoPageStore4py::has_new, "!s");
	hehe.add_this_method<__COUNTER__>("has_key", "has item by key", &CMongoPageStore4py::has_key, "!s");
	hehe.add_this_method<__COUNTER__>("get_page_time", "get publish time of page", &CMongoPageStore4py::get_page_time, "Lss#");
	hehe.add_this_method<__COUNTER__>("update_time", "update item time. args=(key,contentSign,crawlertime,pagetime).", &CMongoPageStore4py::update_time, "!ssLL");
	hehe.add_this_method<__COUNTER__>("upsert_doc", "insert a doc (or update by key) by json", &CMongoPageStore4py::upsert_doc, "!ss");
	hehe.add_this_method<__COUNTER__>("version", "get version", &CMongoPageStore4py::version, "i");
	hehe.apply();

	static PythonObjectFactory<CRBFilePageStore4Py> fps("RBFPSObj", "a page store object with rbtree based file engine");
	//fps.add_this_method<__COUNTER__>("dump", "dump contents function", &CRBFilePageStore4Py::dump, "v");
	fps.add_this_method<__COUNTER__>("has_item", "has item by key and contentSign", &CRBFilePageStore4Py::has_item, "!ss");
	fps.add_this_method<__COUNTER__>("has_new", "has recently updated item by key", &CRBFilePageStore4Py::has_new, "!s");
	fps.add_this_method<__COUNTER__>("has_key", "has item by key", &CRBFilePageStore4Py::has_key, "!s");
	fps.add_this_method<__COUNTER__>("get_page_time", "get publish time of page", &CRBFilePageStore4Py::get_page_time, "Lss#");
	fps.add_this_method<__COUNTER__>("update_time", "update item time. args=(key,contentSign,crawlertime,pagetime).", &CRBFilePageStore4Py::update_time, "!ssLL");
	fps.add_this_method<__COUNTER__>("upsert_doc", "insert a doc (or update by key) by json", &CRBFilePageStore4Py::upsert_doc, "!ss");
	fps.add_this_method<__COUNTER__>("version", "get version", &CRBFilePageStore4Py::version, "i");
	fps.apply();
}
