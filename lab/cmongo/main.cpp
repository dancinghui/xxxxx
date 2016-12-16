#include "stdafx.h"
#include "cmongo.h"
#include "pagestore.h"
#include "rbtdb.h"

#include "sharedfm.h"

struct RBNode{
	char _[16];
	char c[16];
};

struct Settings{
	const static uint64_t magic = 0x123456789abcdef;
	const static uint32_t version = 0x12345678;
};

class CMyRBF : public CRBFile < RBNode, Settings >
{
protected:
	int compare_node(const RBNode * a, const RBNode * b)
	{
		return strcmp(a->c, b->c);
	}
};

CMyRBF rbf;

void insert_s(CMyRBF & rbf, const char * p)
{
	RBNode n;
	strncpy(n.c, p, sizeof(n.c));
	rbf.Insert(&n);
}

int do_test()
{
	CMyRBF rbf;
	rbf.init("teststr.bin");
	insert_s(rbf, "aa");
	insert_s(rbf, "bb");
	insert_s(rbf, "cc");

	auto recv =[](RBNode*a){
		printf("got %s\n", a->c);
		return true;
	};
	auto cmp = [](const char * s, RBNode * b)->int{
		return strcmp(s, b->c);
	};

	int n = rbf.find_key_do((char*)"hello", recv, cmp);
	printf("find result: %d\n", n);

	n = rbf.find_eq_range("bb", recv, cmp);
	printf("find range result: %d\n", n);

	return 0;
}

int i = do_test();




void test_mongo(const char * uri, const char * col)
{
	CMongo mg;
	if (mg.init(uri, NULL, col))
	{
		bson_t q, doc, sub;
		bson_init(&q);
		bson_append_utf8(&q, "indexUrl", -1, "jd_51job://70360961", -1);
		bson_append_utf8(&q, "contentSign", -1, "xxxxxx", -1);
		//bson_append_utf8(&q, "testfield", -1, "hehehehe", -1);

		bson_init(&doc);
		//index_key, {'$set': {'crawlerUpdateTime': int(getime) * 1000}})
		bson_append_document_begin(&doc, "$set", -1, &sub);
		bson_append_int64(&sub, "crawlerUpdateTime", -1, (int64_t)time(0)*1000);
		bson_append_document_end(&doc, &sub);

		//mg.do_query(&q);
		if (mg.update_one(&q, &doc, false))
		{
			printf("insert OK!\n");
		}
		else
		{
			printf("ERROR: %d %d %s\n", mg.m_error.domain, mg.m_error.code, mg.m_error.message);
		}

		bson_destroy(&q);

		mg.find("{\"indexUrl\":\"jd_51job://70360961\"}", "{\"pageContentPath\":0}");

		char * s;
		for (int i=0; (s=mg.get_result())!=0 && i<20; ++i)
		{
			printf("%s\n", s);
			fflush(stdout);
		}
	}
	else
	{
		fprintf(stderr, "init mongoc failed\n");
	}
}

int main (int argc, char *argv[])
{
	fprintf(stderr, "%llx\n", *(uint64_t*)"RBTDBFIL");

	printf("%d\n", GetCurrentThreadId());
	assert((int)GetCurrentThreadId() > 0);
	CMongoSupport::enable();

	if (argc != 3)
	{
		fprintf(stderr, "usage: cmongo dburi collection_name\n");
		return 1;
	}

	CMongoPageStore ps;
	ps.init(argv[1], argv[2]);
	ps.dump();
	return 0;
}
