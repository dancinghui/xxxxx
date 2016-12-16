#define _BSD_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <dirent.h>
#include <limits.h>
#include <memory.h>
#include <string.h>
#include <stdlib.h>
#include <poll.h>
#include <sys/socket.h>
#include <netinet/in.h>

int do_urecv(int port, const char * incstr)
{
	struct sockaddr to;
	int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	memset(&to, 0, sizeof(to));
	((struct sockaddr_in*)&to)->sin_port = htons(port);
	((struct sockaddr_in*)&to)->sin_family = AF_INET;
	((struct sockaddr_in*)&to)->sin_addr.s_addr = htonl(0x7f000001);
	if (bind(sock, &to, sizeof(to))) { perror("bind"); return 1; }
	for (;;)
	{
		struct pollfd pf = {sock, POLLIN, 0};
		poll(&pf, 1, -1);

		struct sockaddr srcaddr;
		char buf[8192];
		socklen_t srcaddrlen = sizeof(srcaddr);
		int n = recvfrom(sock, buf, sizeof(buf), 0, &srcaddr, &srcaddrlen);
		if (n > 0)
		{
			if (buf[n-1] != '\n') buf[n++] = '\n';
			buf[n] = 0;
			if (incstr && *incstr)
			{
				if (strstr(buf, incstr))
				{
					printf("%s", buf);
					fflush(stdout);
				}
			}
			else
			{
				printf("%s", buf);
				fflush(stdout);
			}
		}
	}
	return 0;
}

int main(int argc, char ** argv)
{
	if (argc != 2 && argc != 3)
	{
		fprintf(stderr, "usage: urecv port [incstr]\n");
		return 1;
	}
	int port = atoi(argv[1]);
	const char * incstr = "";
	if (argc==3) incstr = argv[2];

	return do_urecv(port, incstr);
}
