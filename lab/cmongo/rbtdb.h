#pragma once

#include "xptr.h"
#include "xptrrb.h"
#include "pagestore.h"
#include "sharedfm.h"



struct RBItemRecord : xptr::RBItem
{
	const static uint64_t magic = 0x4c49464244544252llu;
	const static uint32_t version = 0x10001;

	unsigned char contentSign[16];
	uint64_t crawler_time;
	uint64_t fileoffset;
	uint64_t page_time;
	char filename[20];
	char indexUrl[52];
};

class CRBFilePageStore : public CRBFile<RBItemRecord, RBItemRecord>, public CPageStoreBase
{
protected:
	bool m_use_mongo;

public:
	struct rbfps_info
	{
		uint32_t lastinittime;
	};
	void check()
	{
		static_assert(sizeof(RBItemRecord) == 128, "");
		static_assert(sizeof(file_st) == 128, "");
		static_assert(__is_pod(file_st), "");
	}

	CRBFilePageStore();
	~CRBFilePageStore();
	bool init(const char * fn, const char * dburi, const char * col);

public:
	bool has_item(const char * indexkey, const char * cs);
	bool has_new(const char * indexuri);
	bool has_key(const char * indexuri);
	int64_t get_page_time(const char * indexkey, const char * cs, int cslen);
	bool update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime);
	bool upsert_doc(const char * key, const char * doc);

protected:
	bool init_record(RBItemRecord & rr, const char * indexkey, const char * cs);
	bool add_row(const DBRow & row);
	virtual void on_error(int code, const char * msg) = 0;
	virtual int compare_node(const RBItemRecord * a, const RBItemRecord * b);
private:
	bool do_init(CMongo* mg);
};
