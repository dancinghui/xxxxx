#include "stdafx.h"
#include "net/nethelper.h"
#include "base/HelperFuncs.h"
#include "base/sutil.h"
#include <openssl/md5.h>
#include <unordered_map>

static void write_log(const char * s)
{
	FILE * fp = fopen("out.log", "a+");
	if (fp)
	{
		fprintf(fp, "%s\n", s);
		fclose(fp);
	}
}

class CPassDB
{
private:
	CLock m_lock;
	struct hashobj{
		unsigned char md[16];
		bool operator == (const hashobj & ho) const
		{
			return memcmp(md, ho.md, 16) == 0;
		}
	};
	struct Hasher{
		size_t operator () (const hashobj & ho) const
		{
			size_t * ps = (size_t*)ho.md;
			size_t rv = 0;
			for (int i=0; i*sizeof(size_t) < sizeof(ho.md); ++i)
			{
				rv = rv ^ ps[i];
			}
			return rv;
		}
	};
	std::unordered_map<hashobj, int, Hasher> m_hashmap;
public:
	int Lookup(unsigned char (&md)[16])
	{
		int rv = -1;
		hashobj obj;
		memcpy(obj.md, md, 16);

		m_lock.Lock();
		rv = m_hashmap[obj];
		m_lock.Unlock();
		return rv;
	}
	int Inc(unsigned char (&md)[16])
	{
		int rv = -1;
		hashobj obj;
		memcpy(obj.md, md, 16);
		m_lock.Lock();
		rv = ++ m_hashmap[obj];
		m_lock.Unlock();
		return rv;
	}
};

int g_debug = 0;

static int do_imap_auth(void * pdb, int sock)
{
	CPassDB * passdb = (CPassDB*)pdb;
	AUTO_CLOSE(closesocket, sock);
	char buf[1024*4] = { 0 };
	int rlen = 0;
	nethelper::read_with_ending(sock, "\n", 20000, buf, sizeof(buf), rlen);
	while (rlen > 0 && isspace((unsigned int)buf[rlen-1]))
		-- rlen;
	if (rlen <= 2 || rlen >= 4000) return -1;

	unsigned char md[16] = { 0 };
	MD5_CTX c;
	MD5_Init(&c);
	MD5_Update(&c, buf+1, rlen-1);
	MD5_Final(md, &c);

	int lk;
	if (buf[0] == 'Q')
		lk = passdb->Lookup(md);
	else if (buf[0] == 'A')
		lk = passdb->Inc(md);
	else
		lk = -1;
	char obuf[100];
	sprintf(obuf, "%d\r\n", lk);
	nethelper::write_all(sock, obuf);
	return 0;
}

void usage()
{
	fprintf(stderr, "usage: hashd [-D]\n"
			"  -D: debug mode, no daemon.\n"
			"  -p port: listen at this port\n");
}

int main(int argc, char ** argv)
{
#ifdef _WIN32
	WSADATA wsd;
	WSAStartup(0x202, &wsd);
#endif
	int port = 11011;
	for (;;)
	{
		int ch = getopt(argc,argv,"Dhp:");
		if (ch<0) break;
		switch (ch)
		{
		case 'D':
			g_debug = 1;
			break;
		case 'h':
			usage();
			return 0;
		case 'p':
			port = atoi(optarg);
			break;
		default:
			usage();
			return 1;
		}
	}

	struct sockaddr_in sa = { 0 };
	sa.sin_family = AF_INET;
	sa.sin_port = htons(port);
	int sock = nethelper::listen_sock((sockaddr&)sa);
	if (sock < 0) return 1;
#ifndef _WIN32
	if (! g_debug)
		daemon(1,0);
#endif

	CPassDB pdb;
	for (;;)
	{
		int w = nethelper::wait_read(sock, -1);
		if (w == nethelper::WAIT_READ)
		{
			struct sockaddr addr1;
			socklen_t addr1len = sizeof(addr1);
			int as = accept(sock, &addr1, &addr1len);
			if (as > 0)
				new_thread(do_imap_auth, &pdb, as, 0);
		}
		else
			Sleep(100);
	}
	return 0;
}
