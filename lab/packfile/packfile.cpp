#define _BSD_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <dirent.h>
#include <limits.h>
#include <memory.h>
#include <string.h>
#include <stdlib.h>

int packfile(const char * dirname, DIR * dir, FILE * fo)
{
	const int maxfsz = 10 * 1024*1024;
	char * mem = (char*)malloc(maxfsz);
	for (int count=1; ; ++count)
	{
		struct dirent * ent = readdir(dir);
		if (!ent) break;
		if (ent->d_name[0]=='.' && (
					(ent->d_name[1]=='.' && ent->d_name[2]==0)  ||
					ent->d_name[1] == 0))
		{
			continue;
		}
		if (!(ent->d_type & DT_REG))
		{
			continue;
		}

		char filename[500];
		sprintf(filename, "%s/%s", dirname, ent->d_name);
		FILE * fin = fopen(filename, "rb");
		if (!fin)
		{
			fprintf(stderr, "can't open %s !\n", filename);
		}
		else
		{
			fseek(fin, 0, SEEK_END);
			long fsz = ftell(fin);
			fseek(fin, 0, SEEK_SET);

			long namelen = strlen(ent->d_name);
			if (fsz > maxfsz || namelen > INT_MAX || fsz<=0 || namelen <= 0)
			{
				fprintf(stderr, "invalid entry %s\n", filename); 
			}
			else
			{
				printf("[%d] %s\n", count, filename);
				int a = (int)namelen;
				int b = (int)fsz;
				
				memset(mem, 0, b);
				fread(mem, 1, b, fin);

				fwrite(&a, 1, sizeof(int), fo);
				fwrite(ent->d_name, 1, a, fo);
				fwrite(&b, 1, sizeof(int), fo);
				fwrite(mem, 1, b, fo);
				fflush(fo);
			}
			fclose(fin);
		}

		printf("%s\n", filename);
	}
	free(mem);
}

int main(int argc, char ** argv)
{
	if (argc != 3)
	{
		fprintf(stderr, "usage: packfile dir outfile.bin\n");
		return 1;
	}

	DIR * dir = opendir(argv[1]);
	if (!dir)
	{
		perror("opendir");
		return 2;
	}
	
	FILE * fo = fopen(argv[2], "wb");
	if (!fo)
	{
		perror("open outfile");
		return 3;
	}
	packfile(argv[1], dir, fo);
	fclose(fo);
	closedir(dir);
	return 0;
}
