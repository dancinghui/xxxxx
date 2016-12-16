#include "stdafx.h"
#include "pagestore.h"

CMongoPageStore::CMongoPageStore()
{
}

CMongoPageStore::~CMongoPageStore()
{
	MPS_RWLock::AutoWLock _(m_lock);
	for (auto it=m_index.begin(); it!=m_index.end(); ++it)
	{
		free_topic(it->second);
	}
	m_index.clear();
}

int64_t CMongoPageStore::get_page_time(const char * indexkey, const char * cs, int cslen)
{
	MPS_RWLock::AutoRLock _(m_lock);
	if (cslen == 32)
	{
		MPS_RWLock::AutoRLock _(m_lock);
		Doc * doc = find_doc_nolock(indexkey, cs);
		if (!doc) return 0;
		else return doc->page_time;
	}
	else
	{
		auto it = m_index.find(indexkey);
		if (it == m_index.end()) return 0;
		Doc * doc  = it->second.next;
		return doc ? doc->page_time : 0;
	}
}

bool CMongoPageStore::has_item(const char * indexkey, const char * cs)
{
	MPS_RWLock::AutoRLock _(m_lock);
	return !! find_doc_nolock(indexkey, cs);
}

bool CMongoPageStore::has_new(const char * indexuri)
{
	MPS_RWLock::AutoRLock _(m_lock);
	auto it = m_index.find(indexuri);
	if (it == m_index.end()) return false;
	return it->second.isnewdoc;
}

bool CMongoPageStore::has_key(const char * indexuri)
{
	MPS_RWLock::AutoRLock _(m_lock);
	auto it = m_index.find(indexuri);
	if (it == m_index.end()) return false;
	return it->second.next != NULL;
}

bool CMongoPageStore::update_time(const char * indexkey, const char * contentsign, int64_t time, int64_t webtime)
{
	WITH_RWLOCK_READ(m_lock)
	{
		Doc * doc  = find_doc_nolock(indexkey, contentsign);
		if (!doc) return false;
		if (doc->crawler_time >= time)
			return false;
		doc->crawler_time = time;
		doc->page_time = webtime;
		if (is_new(time))
		{
			auto it = m_index.find(indexkey);
			if (it != m_index.end())
				it->second.isnewdoc = true;
		}
	}
	QueueDBUpdateTime(indexkey, contentsign, time, webtime);
	return true;
}

bool CMongoPageStore::upsert_doc(const char * key, const char * json)
{
	bool rv = true;
	DBRow row;
	bson_t * bx = 0;
	if (translate_doc(json, row, &bx))
	{
		QueueDBInsert(key, bx);

		//write lock and update db.
		MPS_RWLock::AutoWLock _(m_lock);
		add_row(row);
	}
	else
	{
		on_error(-1, "invalid doc for pagestore.");
		rv = false;
	}
	if (bx) bson_destroy(bx);
	return rv;
}

bool CMongoPageStore::do_init(CMongo * mg)
{
	MPS_RWLock::AutoWLock addrows(m_lock);
	return CPageStoreBase::do_init(mg);
}

// WARNING: this method needs callers to lock data structures!
bool CMongoPageStore::add_row(const DBRow & row)
{
	string indexUrl = row.indexUrl;

	Topic & t = m_index[indexUrl];
	if (!t.isnewdoc && is_new(row.crawler_time))
	{
		t.isnewdoc = true;
	}

	Doc doc;
	doc.next = 0;
	doc.crawler_time = row.crawler_time;
	doc.page_time = row.page_time;
	memcpy(doc.contentSign, row.contentSign, 16);

	Doc ** next = & t.next;
	while (*next) next = &(*next)->next;
	*next = new_doc(doc);
	return true;
}

CMongoPageStore::Doc * CMongoPageStore::find_doc_nolock(const char * indexkey, const char * contentsign)
{
	string res;
	Helper::decode16(contentsign, res);
	if (res.size() != 16)
	{
		on_error(-1, "invalid contentSign");
		return NULL;
	}

	auto it = m_index.find(indexkey);
	if (it == m_index.end()) return NULL;
	Doc * next = it->second.next;
	uint8_t * cs = (uint8_t*)res.data();
	while (next)
	{
		if (memcmp(next->contentSign, cs, 16) == 0)
		{
			return next;
		}
		next = next->next;
	}
	return NULL;
}


//############################################################
//##########        TODO: memory pool       ##################
//############################################################
CMongoPageStore::Doc * CMongoPageStore::new_doc(Doc & doc)
{
	return new Doc(doc);
}

void CMongoPageStore::free_topic(Topic & topic)
{
	Doc * next = topic.next;
	while (next)
	{
		Doc * s = next;
		next = next->next;
		delete s;
	}
}
