#include "stdafx.h"
#include "crypt/base64.h"
#include "qqptlogin.h"

int main(int argc, char ** argv)
{
	if (argc != 4)
	{
		fprintf(stderr, "usage: getqqpwd <password> <base64salt> <verifycode>\n");
		return 1;
	}
	else
	{
		string res;
		if (getEncryption(argv[1], base64_decode(argv[2]), argv[3], res))
		{
			printf("%s\n", res.c_str());
			return 0;
		}
		else
		{
			fprintf(stderr, "error!\n");
			return 2;
		}
	}
}
