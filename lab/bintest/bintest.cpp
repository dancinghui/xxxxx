#include "stdafx.h"
#include "base/HelperFuncs.h"

bool test_binfile(const char * fn)
{
	uint64_t fsz = 0;
	char * fx =  (char*) Helper::map_file(fn, fsz);
	if (!fx)
	{
		fprintf(stderr, "mmap failed!!");
		return false;
	}

	unsigned long long counter = 0;
	for (char * p=fx; p<fx+fsz;)
	{
		unsigned int len1 = *(unsigned int*)p;
		p += 4 + len1;
		if (p+4<=fx+fsz)
		{
			len1 = *(unsigned int *)p;
			p += 4 + len1;
			++ counter;
			if (counter % 20000 == 0)
			{
				fprintf(stderr, "%llu records, %.2lf%%\n", counter, (double)(p-fx)*100/fsz);
			}
			if (p==fx+fsz) return true;
			if (p>fx+fsz) return false;
		}
		else
			return false;
	}
	Helper::unmap_file(fx, fsz);
	return true;
}

extc int main(int argc, char ** argv)
{
	if (argc != 2)
	{
		fprintf(stderr, "usage: fix_jobuid filename\n");
		return 1;
	}
	bool t = test_binfile(argv[1]);
	printf(t ? "file OK\n" : "file invalid !!\n");
	return t ? 0 : -1;
}
