#pragma once
#include "cmongo.h"
#include "base/HelperFuncs.h"
#include <unordered_map>

class CPageStoreBase
{
public:
	struct DBRow
	{
		char indexUrl[256];
		unsigned char contentSign[16];
		uint64_t crawler_time;
		uint64_t page_time;
	};

protected:
	int64_t m_basetime;
	CMongoMultiThreaded m_db;

public:
	CPageStoreBase();
	virtual ~CPageStoreBase();
protected:
	bool translate_doc(const bson_t * bx, DBRow & row);
	bool translate_doc(const char * json, DBRow & row, bson_t ** bsout);
	bool QueueDBUpdateTime(const char * key, const char * sign, int64_t time, int64_t webtime);
	bool QueueDBInsert(const char * key, bson_t * bs);

	bool init(const char * uri, const char * col);
	virtual bool do_init(CMongo * mg);
	virtual bool add_row(const DBRow & row) = 0;
	virtual void on_error(int code, const char * msg){}
	virtual bool is_new(int64_t time){return time>m_basetime;}
#if 0
public:
	virtual bool has_item(const char * indexkey, const char * cs) = 0;
	virtual bool has_new(const char * indexuri) = 0;
	virtual bool has_key(const char * indexuri) = 0;
	virtual int64_t get_page_time(const char * indexkey, const char * cs, int cslen) = 0;
	virtual bool update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime) = 0;
	virtual bool upsert_doc(const char * key, const char * doc) = 0;
#endif
};

class CMongoPageStore : public CPageStoreBase
{
public:
	typedef CRWLock MPS_RWLock;
	struct Doc{
		char contentSign[16];
		int64_t crawler_time;
		int64_t page_time;
		struct Doc * next;
	};
	struct Topic{
		bool isnewdoc;
		Doc * next;
	};
protected:
	MPS_RWLock m_lock;
	std::unordered_map<string, Topic> m_index;

public:
	void dump()
	{
		MPS_RWLock::AutoRLock _(m_lock);
		for (auto x : m_index)
		{
			Doc * doc = x.second.next;
			for (int i=0; doc; ++i)
			{
				string r = Helper::encode16(doc->contentSign, 16);
				printf("[%d] %s=>%s, %lld\n", i, x.first.c_str(), r.c_str(), doc->crawler_time);
				doc = doc->next;
			}
		}
	}

public:
	CMongoPageStore();
	virtual ~CMongoPageStore();

	bool has_item(const char * indexkey, const char * cs);
	bool has_new(const char * indexuri);
	bool has_key(const char * indexuri);
	int64_t get_page_time(const char * indexkey, const char * cs, int cslen);
	bool update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime);
	bool upsert_doc(const char * key, const char * json);
	bool init(const char * uri, const char * col)
	{
		return CPageStoreBase::init(uri, col);
	}
private:
	Doc * find_doc_nolock(const char * indexkey, const char * contentsign);
	bool add_row(const DBRow & row);
	virtual bool do_init(CMongo * mg);

	//TODO: memory pool
	Doc * new_doc(Doc & doc);
	void free_topic(Topic & topic);
};
