#include "stdafx.h"
#include <mongoc.h>
#include "cmongo.h"

void CMongoSupport::enable()
{
	static CMongoSupport ms;
}

CMongo::CMongo()
{
	m_client = 0;
	m_collection = 0;
	m_dbname[0] = 0;
	m_cursor = 0;
	m_rstr = 0;
	m_waitdef = mongoc_write_concern_new();
	mongoc_write_concern_set_w(m_waitdef, MONGOC_WRITE_CONCERN_W_DEFAULT);
	m_nowait = mongoc_write_concern_new();
	mongoc_write_concern_set_w(m_nowait, MONGOC_WRITE_CONCERN_W_UNACKNOWLEDGED);
	memset(&m_error, 0, sizeof(m_error));
}

CMongo::~CMongo()
{
	save_str(NULL);
	mongoc_write_concern_destroy(m_waitdef);
	mongoc_write_concern_destroy(m_nowait);
	if (m_cursor)
	{
		mongoc_cursor_destroy(m_cursor);
		m_cursor = 0;
	}
	if (m_collection)
		mongoc_collection_destroy (m_collection);
	if (m_client)
		mongoc_client_destroy (m_client);
}

char* CMongo::save_str(char * str)
{
	if (m_rstr) bson_free(m_rstr);
	m_rstr = str;
	return m_rstr;
}

bool CMongo::init(const char * uristr, const char * dbname, const char * collection_name)
{
	m_dbname[0] = 0;
	m_client = mongoc_client_new (uristr);
	if (m_client)
	{
		if (!dbname)
			dbname = mongoc_uri_get_database(mongoc_client_get_uri(m_client));
		if (!dbname)
			dbname = "admin";
		strncpy(m_dbname, dbname, sizeof(m_dbname)-1);
		m_dbname[sizeof(m_dbname)-1] = 0;
		m_collection = mongoc_client_get_collection (m_client, dbname, collection_name);
		return true;
	}
	return false;
}

bool CMongo::do_find(const char * json, const char * fields, uint32_t limit)
{
	bson_t * bsquery = json ?\
	bson_new_from_json ((const uint8_t*)json, -1, &m_error) :\
	bson_new();
	if (!bsquery) return false;

	bson_t * bfields = fields ? bson_new_from_json((const uint8_t*)fields, -1, &m_error) : NULL;
	bool r = do_find(bsquery, bfields, limit);
	if (bsquery) bson_destroy(bsquery);
	if (bfields) bson_destroy(bfields);
	return r;
}

bool CMongo::do_find(bson_t * bsquery, bson_t * fields, uint32_t limit)
{
	if (m_cursor)
	{
		mongoc_cursor_destroy(m_cursor);
		m_cursor = 0;
	}
	uint32_t skip = 0;
	m_cursor = mongoc_collection_find (m_collection, MONGOC_QUERY_NONE,
									   skip, limit, 0, bsquery, fields, NULL);
	return m_cursor != 0;
}

bool CMongo::insert_one(const char * json)
{
	if (!json) return false;
	bson_t * doc = bson_new_from_json((const uint8_t*)json, -1, &m_error);
	bool br = insert_one(doc);
	bson_destroy(doc);
	return br;
}

bool CMongo::insert_one(const bson_t * doc)
{
	mongoc_insert_flags_t flags = (mongoc_insert_flags_t)MONGOC_INSERT_NO_VALIDATE;
	return mongoc_collection_insert(m_collection, flags, doc, m_waitdef, &m_error);
}

bool CMongo::update_json(const char * jkey, const char * jdoc, bool upsert, bool many, bool wait)
{
	if (!jkey || !jdoc) return false;
	bson_t * bkey = bson_new_from_json((const uint8_t*)jkey, -1, &m_error);
	if (!bkey) return false;
	bson_t * bdoc = bson_new_from_json((const uint8_t*)jdoc, -1, &m_error);
	if (!bdoc) return (bson_destroy(bkey),false);

	bool r = update_bson(bkey, bdoc, upsert, many, wait);

	bson_destroy(bkey);
	bson_destroy(bdoc);
	return r;
}

bool CMongo::update_bson(const bson_t* bkey, const bson_t* bdoc, bool upsert, bool many, bool wait)
{
	mongoc_update_flags_t fl = (mongoc_update_flags_t) MONGOC_UPDATE_NO_VALIDATE;
	if (upsert) fl = (mongoc_update_flags_t) (fl|MONGOC_UPDATE_UPSERT);
	if (many) fl = (mongoc_update_flags_t) (fl|MONGOC_UPDATE_MULTI_UPDATE);
	return mongoc_collection_update(m_collection, fl, bkey, bdoc, wait?m_waitdef:m_nowait, &m_error);
}

char* CMongo::get_result(bool * haserr)
{
	const bson_t * doc;
	if (haserr) *haserr = false;
	if (!m_cursor) return NULL;
	if (mongoc_cursor_next(m_cursor, &doc))
	{
		return save_str(bson_as_json(doc, NULL));
	}
	if (mongoc_cursor_error(m_cursor, &m_error))
		if (haserr) *haserr = true;
	return NULL;
}

const bson_t* CMongo::get_result_bson(bool * haserr)
{
	const bson_t * doc;
	if (haserr) *haserr = false;
	if (!m_cursor) return NULL;
	if (mongoc_cursor_next(m_cursor, &doc))
	{
		return doc;
	}
	if (mongoc_cursor_error(m_cursor, &m_error))
		if (haserr) *haserr = true;
	return NULL;
}

CMongoMultiThreaded::CMongoMultiThreaded()
{
}

CMongoMultiThreaded::~CMongoMultiThreaded()
{
	m_maplock.Lock();
	for (auto it = m_dbs.begin(); it!=m_dbs.end(); ++it)
	{
		delete it->second;
		it->second = 0;
	}
	m_dbs.clear();
	m_maplock.Unlock();
}

bool CMongoMultiThreaded::init(const char * uri, const char * col)
{
	ENSURE_LOCK(m_mainlock);
	m_uri = uri;
	m_col = col;
	return m_maindb.init(uri, NULL,  col);
}
