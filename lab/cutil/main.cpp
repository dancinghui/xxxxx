#include "stdafx.h"
#include "xptr.h"
#include "jobq.h"

int main()
{
#ifdef _WIN32
	_CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);
	strdup("leaksample");
#endif

	CJobQueue jjq;

	CJobQueue * jq = &jjq;
	jq->init("joblist.bin");
	if (jq->get_size() == 0)
	{
		jq->add_main_job_range("{}", 0, 100, 1);
		jq->add_main_job_file("{}", "jobq.vcxproj", 220, 225);
		jq->readd_job("{\"type\":\"test\", \"_retrycnt_\":\"3\"}");
	}
	string vs;
	bool bm;
	while (jq->get_job(vs, bm, 1))
	{
		printf("%s %s\n", bm ? "#" : " ", vs.c_str());
	}
	printf("%d\n", (int) jq->get_size());
	//delete jq;
	return 0;
}
