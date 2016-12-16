#include "stdafx.h"
#include "base/lock.h"
#include "base/HelperFuncs.h"

#include "xptr.h"
#include "xptrrb.h"
#include "fmalloc.h"
#include "rbtdb.h"

using namespace xptr;

CRBFilePageStore::CRBFilePageStore()
{
	m_use_mongo = false;
}

CRBFilePageStore::~CRBFilePageStore()
{
}

bool CRBFilePageStore::init(const char * fn, const char * dburi, const char * col)
{
	if (!fn || !*fn || !dburi || !col) return false;
	if (!CRBFile::init(fn))
		return false;

	if (*dburi == 0)
	{
		m_use_mongo = false;
	}
	else
	{
		if (! CPageStoreBase::init(dburi, col))
			return false;
		m_use_mongo = true;
	}
	return true;
}

bool CRBFilePageStore::do_init(CMongo *mg)
{
	{
		ENTER_FUNC();
		rbfps_info * info = (rbfps_info*) ( reinterpret_cast<file_st*>(m_fileptr)->reserved );
		if (info->lastinittime + 3600*24 > time(0))
			return true;
	}
	bool r = CPageStoreBase::do_init(mg);
	if (r)
	{
		ENTER_FUNC();
		rbfps_info * info = (rbfps_info*) ( reinterpret_cast<file_st*>(m_fileptr)->reserved );
		info->lastinittime = (uint32_t) time(0);
	}
	return r;
}

///=================================================================
bool CRBFilePageStore::init_record(RBItemRecord & rr, const char * indexkey, const char * cs)
{
	string res;
	Helper::decode16(cs, res);
	if (res.size() != 16)
	{
		on_error(__LINE__, "invalid contentSign");
		return false;
	}
	if (strlen(indexkey) >= sizeof(rr.indexUrl))
	{
		on_error(__LINE__, "indexUri too long");
		return false;
	}
	strcpy(rr.indexUrl, indexkey);
	memcpy(rr.contentSign, res.data(), 16);
	return true;
}

int CRBFilePageStore::compare_node(const RBItemRecord* a, const RBItemRecord* b)
{
	int n1 = strcmp(a->indexUrl, b->indexUrl);
	if (n1 != 0) return n1;
	int n2 = memcmp(a->contentSign, b->contentSign, 16);
	if (n2 != 0) return n2;
	return 0;
}

static int compare_onkey(const RBItem* a0, const RBItem* b0)
{
	RBItemRecord * a = (RBItemRecord *)a0;
	RBItemRecord * b = (RBItemRecord *)b0;

	int n1 = strcmp(a->indexUrl, b->indexUrl);
	if (n1 != 0) return n1;

	return 0;
}

bool CRBFilePageStore::has_item(const char * indexkey, const char * cs)
{
	RBItemRecord rr;
	if (!init_record(rr, indexkey, cs))
		return false;
	return Find(&rr);
}

bool CRBFilePageStore::has_new(const char * indexuri)
{
	RBItemRecord rr;
	if (!init_record(rr, indexuri, "0123456789abcdef0123456789abcdef"))
		return false;

	bool foundnew = false;
	auto callit = [&](RBItemRecord * r)->bool
	{
		if (r->crawler_time >= this->m_basetime)
		{
			foundnew = true;
			return false;
		}
		return true;
	};
	find_eq_range(&rr, callit, &compare_onkey);
	return foundnew;
}

bool CRBFilePageStore::has_key(const char * indexuri)
{
	RBItemRecord rr;
	if (!init_record(rr, indexuri, "0123456789abcdef0123456789abcdef"))
		return false;

	return find_do(&rr, [](RBItemRecord*){return false; }, &compare_onkey);
}

bool CRBFilePageStore::update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime)
{
	RBItemRecord rr;
	if (!init_record(rr, indexkey, contentsign))
		return false;

	bool rv = false;
	auto callit = [&](RBItem * a)->bool{
		RBItemRecord* rr = (RBItemRecord*)a;
		if (rr->crawler_time < time)
		{
			rr->crawler_time = time;
			rr->page_time = webtime;
			rv = true;
		}
		return true;
	};

	find_do(&rr, callit);
	if (rv && m_use_mongo)
		QueueDBUpdateTime(indexkey, contentsign, time, webtime);

	return rv;
}

int64_t CRBFilePageStore::CRBFilePageStore::get_page_time(char const* indexkey, char const* cs, int cslen)
{
	RBItemRecord rr;
	if (!init_record(rr, indexkey, cslen == 32 ? cs : "0123456789abcdef0123456789abcdef"))
		return 0;

	int64_t found_time = 0;

	auto rcv = [&] (RBItemRecord * r) -> bool {
		found_time = r->page_time;
		return false;
	};

	if (cslen == 32)
	{
		find_do(&rr, rcv);
		return found_time;
	}
	else
	{
		find_eq_range(&rr, rcv, &compare_onkey);
		return found_time;
	}
}

//got the doc. and .....
bool CRBFilePageStore::upsert_doc(const char * key, const char * json)
{
	DBRow row = {0};
	bson_t * bx = 0;
	bool rv = false;

	if (translate_doc(json, row, &bx))
	{
		add_row(row);
		rv = true;
		if (m_use_mongo) rv = QueueDBInsert(key, bx);
	}
	if (bx) bson_destroy(bx);
	return rv;
}

bool CRBFilePageStore::add_row(const DBRow & row)
{
	RBItemRecord rr;
	if (strlen(row.indexUrl) >= sizeof(rr.indexUrl))
	{
		fprintf(stderr, "indexUrl %s is too long! should be not more than %d bytes.\n",
				row.indexUrl, (int)sizeof(rr.indexUrl)-1);
		return false;
	}

	memset(&rr, 0, sizeof(rr));
	memcpy(rr.contentSign, row.contentSign, 16);
	rr.crawler_time = row.crawler_time;
	rr.page_time = row.page_time;
	strcpy(rr.indexUrl, row.indexUrl);

	return Insert(&rr);
}
