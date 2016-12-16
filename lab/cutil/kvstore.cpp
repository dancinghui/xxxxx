#include "stdafx.h"
#include "base/lock.h"
#include "base/HelperFuncs.h"
#include "fmalloc.h"
#include "kvstore.h"
#include "rbtree.hpp"

using namespace xptr;

namespace nskvstore
{
	struct KVRBItem;
	struct KVRBItemPtr;
	typedef CRBTreeBase<KVRBItemPtr>::RBItemX RBItemX;
	
	struct KVRBItemPtr : packed_ptr_t<KVRBItem>
	{
		KVRBItem * v(void * env)
		{
			return rawptr((baseaddr_t)env);
		}
		void set(RBItemX * p, void *env)
		{
			setptr( (KVRBItem*)p, (baseaddr_t)env);
		}
	};
	
	struct KVRBItem : public RBItemX
	{
		unsigned char key[16];
		packed_ptr svalue;
		int reserved[12];
	};

	struct RootData
	{
		KVRBItemPtr rbroot_;
		volatile int rwlock;
		
		CRBTreeTemp<KVRBItemPtr> * root()
		{
			static_assert(sizeof(KVRBItemPtr) == 4, "must be a small ptr.");
			static_assert(sizeof(CRBTreeTemp<KVRBItemPtr>) == 4, "must be a small ptr.");
			return (CRBTreeTemp<KVRBItemPtr>*) &rbroot_;
		}
	};
	
	static int compare_itm(const RBItemX *a, const RBItemX *b)
	{
		KVRBItem * a1 = (KVRBItem*)a;
		KVRBItem * b1 = (KVRBItem*)b;
		return memcmp(a1->key, b1->key, 16);
	}
}

bool CKVStore::get_item(const char * key, int keylen, string & so)
{
	if (keylen != 16) return 0;
	
	nskvstore::KVRBItem itm;
	memcpy(itm.key, key, 16);
	
	m_fm.RLock();
	
	nskvstore::RootData * rd = m_fm.get_app_space<nskvstore::RootData>();
	CSimpRWLock * rwl = CSimpRWLock::from(&rd->rwlock);
	rwl->RLock();
	nskvstore::RBItemX * f = rd->root()->Find(&itm, &nskvstore::compare_itm, (void*)m_fm.base());
	nskvstore::KVRBItem * f1 = (nskvstore::KVRBItem*)f;
	rwl->RUnlock();
	
	char * r = 0;
	if (f1)
	{
		r = (char*)f1->svalue.rawptr(m_fm.base());
		so.assign(r+4, *(int*)r);
	}
	
	m_fm.RUnlock();
	return !!r;
}

bool CKVStore::set_item(const char * key, int keylen, const char * value, int vallen)
{
	if (keylen != 16) return false;
	
	packed_ptr item_ = m_fm.do_alloc(sizeof(nskvstore::KVRBItem));
	packed_ptr pv_ = m_fm.do_alloc(vallen + 4);
	
	m_fm.RLock();
	nskvstore::KVRBItem * item = (nskvstore::KVRBItem*) item_.rawptr(m_fm.base());
	memcpy(item->key, key, keylen);
	item->svalue = pv_;
	
	void * v = pv_.rawptr(m_fm.base());
	*(int*)v = vallen;
	memcpy((char*)v+4, value, vallen);
	
	nskvstore::RootData * rd = m_fm.get_app_space<nskvstore::RootData>();
	CSimpRWLock * rwl = CSimpRWLock::from(&rd->rwlock);
	rwl->WLock();
	bool rv = rd->root()->Insert(item, &nskvstore::compare_itm, (void*)m_fm.base());
	rwl->WUnlock();
	m_fm.RUnlock();
	
	if (!rv)
	{
		m_fm.do_free(item_);
		m_fm.do_free(pv_);
	}
	
	return rv;
}

//for python.
#include "modhelper.h"

class CPyKVStore : public CKVStore
{
public:
	bool init(PyObject* args, PyObject* kwds)
	{
		char * fn = 0;
		int n = PyArg_ParseTuple(args, "s", &fn);
		if (!n) return false;
		if (CKVStore::init(fn))
			return true;
		
		char errs[1000];
		snprintf(errs, sizeof(errs), "unable to open file %s", fn);
		CPyModuleHelper::GetInstance().SetErrStr(__LINE__, errs);
		return false;
	}
	
	PyObject * get_item(const char * key, int keylen)
	{
		string ro;
		if (! CKVStore::get_item(key, keylen, ro))
		{
			Py_IncRef(Py_None);
			return Py_None;
		}
		else
		{
			PyObject * os = PyString_FromStringAndSize(ro.c_str(), ro.length());
			assert(os->ob_refcnt == 1);
			return os;
		}
	}
};

void init_py_kvstore()
{
	static PythonObjectFactory<CPyKVStore> jq("KVStore", "a storage object saves 16bytes key and string value. init args: (storage_filename)");
	jq.add_this_method<__COUNTER__>("get_item",
									"get item from storage.\n"
									"args:(key). returns: value or None\n",
									&CPyKVStore::get_item, "Ns#");
	jq.add_this_method<__COUNTER__>("set_item", "save item to storage. args:(key, value)",
									&CPyKVStore::set_item, "!s#s#" );
	jq.apply();
}
