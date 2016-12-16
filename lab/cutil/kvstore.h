#pragma once
#include "fmalloc.h"

class CKVStore
{
protected:
	CFMalloc m_fm;
	
public:
	bool init(const char * fn)
	{
		return m_fm.init(fn);
	}

	bool get_item(const char * key, int keylen, string & so);
	bool set_item(const char * key, int keylen, const char * value, int vallen);
};

void init_py_kvstore();
