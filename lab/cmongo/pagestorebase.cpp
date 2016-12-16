#include "stdafx.h"
#include "pagestore.h"

CPageStoreBase::CPageStoreBase()
{
	m_basetime = ((int64_t)time(0) - 3*24*3600) * 1000;
}

CPageStoreBase::~CPageStoreBase()
{

}

bool CPageStoreBase::init(const char * uri, const char * col)
{
	if (!m_db.init(uri, col))
		return false;
	bool rv = false;
	m_db.get_db_do([&](CMongo * mg)->void{
		rv = this->do_init(mg);
	});
	return rv;
}

bool CPageStoreBase::do_init(CMongo* mg)
{
	CBson query, fields;
	fields.addint32("indexUrl", 1);
	fields.addint32("contentSign", 1);
	fields.addint32("crawlerUpdateTime", 1);
	fields.addint32("updateTime", 1);

	if (!mg->do_find(&query, &fields))
		return false;

	bool err = false;
	for (unsigned int cnt=0; ; )
	{
		const bson_t * bx = mg->get_result_bson(&err);
		if (!bx) break;
		DBRow row;
		if (translate_doc(bx, row))
		{
			add_row(row);
			++ cnt;
			if ((cnt % 10000) == 0)
			{
				fprintf(stderr, "[%llu] got %u docs\n", (unsigned long long)time(0), cnt);
			}
		}
		else
		{
			char * json = bson_as_json(bx, NULL);
			fprintf(stderr, "unknown doc: %s\n", json);
			bson_free(json);
		}
	}
	return !err;
}

bool CPageStoreBase::translate_doc(const bson_t * bx, DBRow & row)
{
	bson_iter_t iter;
	bson_iter_init(&iter, bx);
	string res;
	memset(&row, 0, sizeof(row));
	int find = 0;

	while (bson_iter_next(&iter))
	{
		const char * key = bson_iter_key(&iter);
		bson_type_t tp =bson_iter_type(&iter);
		const char * v;
		int64_t v64;
		double dv = 0.0;
		switch (tp)
		{
			case BSON_TYPE_UTF8:
				v = (const char*) bson_iter_utf8(&iter, NULL);
				if (strcmp(key, "contentSign") == 0)
				{
					Helper::decode16(v, res);
					if (res.length() == 16)
					{
						memcpy(row.contentSign, res.data(), 16);
						find |= 1;
					}
				}
				if (strcmp(key, "indexUrl") == 0)
				{
					if (strlen(v) >= sizeof(row.indexUrl))
						return false; // too long..
					strcpy(row.indexUrl, v);
					find |= 2;
				}
				break;
			case BSON_TYPE_INT64:
				v64 = bson_iter_int64(&iter);
				if (strcmp(key, "crawlerUpdateTime") == 0)
				{
					row.crawler_time = v64;
					find |= 4;
				}
				else if (strcmp(key, "updateTime") == 0)
				{
					row.page_time = v64;
					find |= 8;
				}
				break;
			case BSON_TYPE_DOUBLE:
				//early data uses double as updateTime.
				dv = bson_iter_double(&iter);
				if (strcmp(key, "updateTime") == 0)
				{
					row.page_time = (int64_t)dv;
					find |= 8;
				}
				break;
			default:
				break;
		}
		if (find == 15) return true;
	}
	return false;
}

bool CPageStoreBase::translate_doc(const char * json, DBRow &row, bson_t** bsout)
{
	bson_error_t error;
	bson_t * bx = bson_new_from_json((const uint8_t*)json, -1, &error);
	if (!bx) return false;
	bool rv = translate_doc(bx, row);
	if (bsout)
		*bsout = bx;
	else
		bson_destroy(bx);
	return rv;
}


bool CPageStoreBase::QueueDBUpdateTime(const char * key, const char * sign, int64_t time, int64_t webtime)
{
	CNoinitBson sub;
	CBson qkey, qset;
	qkey.addstr("indexUrl", key);
	qkey.addstr("contentSign", sign);
	//{'$set': {'crawlerUpdateTime': int(getime) * 1000}})
	qset.adddoc_begin("$set", sub);
	sub.addint64("crawlerUpdateTime", time);
	sub.addint64("updateTime", webtime);
	sub.addint32("isUpdated", 1);
	qset.adddoc_end(sub);

	bson_error_t berr = {0};
	bool rv = false;
	m_db.get_db_do([&](CMongo *mg)->void{
		rv = mg->update_one_nowait(&qkey, &qset, false);
		if (!rv) mg->get_err(&berr);
	});

	if (!rv) on_error(berr.code, berr.message);
	return rv;
}

bool CPageStoreBase::QueueDBInsert(const char * key, bson_t * bs)
{
	bson_error_t berr = {0};
	bool rv = false;
	CBson qkey;
	qkey.addstr("indexUrl", key);

	m_db.get_db_do([&](CMongo *mg)->void{
		rv = mg->insert_one(bs);
		if (!rv) rv = mg->update_one(&qkey, bs, true);
		if (!rv) mg->get_err(&berr);
	});

	if (!rv) on_error(berr.code, berr.message);
	return rv;
}
