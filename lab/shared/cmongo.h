#pragma once
#include "base/lock.h"
#include <mongoc.h>

class no_init{};

class CBson;

class CNoinitBson : public bson_t
{
public:
	bool addint32(const char * k, int v){return bson_append_int32(this, k, -1, v);}
	bool addint64(const char * k, int64_t v){return bson_append_int64(this, k, -1, v);}
	bool addstr(const char *k, const char*v){return bson_append_utf8(this, k, -1, v, -1);}
	bool addfloat(const char*k, double v){return bson_append_double(this, k, -1, v);}
	bool addbool(const char*k, bool v){return bson_append_bool(this, k, -1, v);}
	bool adddoc_begin(const char *k, CNoinitBson & nb)
	{
		return bson_append_document_begin(this, k, -1, &nb);
	}
	bool adddoc_end(CNoinitBson & nb)
	{
		return bson_append_document_end(this, &nb);
	}
private:
	bool adddoc_begin(const char *, CBson &);
	bool adddoc_begin(const char *, const CBson &);
	bool adddoc_end(const char *, CBson &);
	bool adddoc_end(const char *, const CBson &);
public:
	static CNoinitBson * from(bson_t * ptr)
	{
		static_assert(sizeof(bson_t)==sizeof(CNoinitBson), "no other members and virtual funcs!");
		return (CNoinitBson*)ptr;
	}
};

class CBson : public CNoinitBson
{
public:
	CBson(){bson_init(this);}
	~CBson(){bson_destroy(this);}
	CBson(no_init){}
private:
	CBson(const CBson&);
	void operator = (const CBson&);
};

class CMongoSupport
{
private:
	CMongoSupport(){mongoc_init();}
	~CMongoSupport(){mongoc_cleanup();}
public:
	static void enable();
};


class CMongo
{
private:
	char m_dbname[256];
	mongoc_client_t * m_client;
	mongoc_collection_t * m_collection;
	mongoc_cursor_t * m_cursor;
	mongoc_write_concern_t *m_waitdef, *m_nowait;

	char * m_rstr;
public:
	bson_error_t m_error;
public:
	CMongo();
	~CMongo();
	char* save_str(char * str);
	bool init(const char * uristr, const char * dbname, const char * collection_name);
	char* get_result(bool * haserr = 0);
	const bson_t* get_result_bson(bool * haserr);
	bool do_find(const char * json, const char * fields, uint32_t limit = 0);
	bool do_find(bson_t * bsquery, bson_t * fields = 0, uint32_t limit = 0);
	bool insert_one(const char * json);
	bool insert_one(const bson_t * doc);
	
	bool init(crefstr url)
	{
		size_t pos = url.find("::");
		if (pos != string::npos)
		{
			string baseurl = url.substr(0, pos);
			string colname = url.substr(pos+2);
			return init(baseurl.c_str(), 0, colname.c_str());
		}
		else
			return init(url.c_str(), 0, 0);
	}
protected:
	bool update_bson(const bson_t* bkey, const bson_t* bdoc, bool upsert, bool many, bool wait);
	bool update_json(const char * jkey, const char * jdoc, bool upsert, bool many, bool wait);
public:
	const bson_error_t * get_err(bson_error_t * cp) const
	{
		if (cp)
		{
			memcpy(cp, &m_error, sizeof(bson_error_t));
			return cp;
		}
		else
			return &m_error;
	}
	bool find_one(const char * json, const char * fields)
	{
		return do_find(json, fields, 1);
	}
	bool find(const char * json, const char * fields)
	{
		return do_find(json, fields, 0);
	}
	bool update_one(const bson_t* bkey, const bson_t* bdoc, bool upsert)
	{
		return update_bson(bkey, bdoc, upsert, false, true);
	}
	bool update_one_nowait(const bson_t* bkey, const bson_t* bdoc, bool upsert)
	{
		return update_bson(bkey, bdoc, upsert, false, false);
	}
	bool update_many(const bson_t* bkey, const bson_t* bdoc, bool upsert)
	{
		return update_bson(bkey, bdoc, upsert, true, true);
	}
	bool update_one(const char * jkey, const char * jdoc, bool upsert)
	{
		return update_json(jkey, jdoc, upsert, false, true);
	}
	bool update_one_nowait(const char * jkey, const char * jdoc, bool upsert)
	{
		return update_json(jkey, jdoc, upsert, false, false);
	}
	bool update_many(const char * jkey, const char * jdoc, bool upsert)
	{
		return update_json(jkey, jdoc, upsert, true, true);
	}
};


class CMongoMultiThreaded
{
protected:
	CLock m_maplock, m_mainlock;
	CMongo m_maindb;
	std::map<int64_t, CMongo *> m_dbs;
	string m_uri, m_col;

public:
	CMongoMultiThreaded();
	~CMongoMultiThreaded();
	bool init(const char * uri, const char * col);

	template <class T>
	void get_db_do(T caller)
	{
		int64_t tid = GetCurrentThreadId();
		assert((int)tid > 0);

		m_maplock.Lock();
		auto it = m_dbs.find(tid);
		if (it != m_dbs.end())
		{
			CMongo * m = it->second;
			m_maplock.Unlock();
			caller(m);
			return ;
		}
		m_maplock.Unlock();

		if (m_mainlock.TryLock())
		{
			caller(&m_maindb);
			m_mainlock.Unlock();
			return ;
		}

		m_maplock.Lock();
		CMongo * m = m_dbs[tid];
		if (!m)
		{
			m = new CMongo;
			m->init(m_uri.c_str(), NULL, m_col.c_str());
			m_dbs[tid] = m;
		}
		m_maplock.Unlock();
		caller(m);
	}
};
