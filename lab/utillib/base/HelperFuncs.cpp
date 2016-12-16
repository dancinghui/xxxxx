#include "stdafx.h"
#include "HelperFuncs.h"
#include "sutil.h"

#ifndef _WIN32
#include <sys/mman.h>
#include <sys/types.h>
#include <dirent.h>
# ifndef __CYGWIN__
# include <sys/sysctl.h>
# endif
#include <unistd.h>
#endif

static inline bool Match_(BYTE * ptr, int len, int o, BYTE v1, BYTE v2)
{
	return o<len && (ptr[o] & v1) == v2;
}

namespace Helper
{
	bool IsTextUtf8(const void * ptr_, int len)
	{
		BYTE * ptr = (BYTE*)ptr_;
		for (int i=0; i<len; )
		{
			if (ptr[i] == 0) return false;
			if (ptr[i] < 0x80)
			{
				++ i;
			}
			else if (
				Match_(ptr, len, i+0, 0xe0, 0xc0) &&
				Match_(ptr, len, i+1, 0xc0, 0x80)
				)
			{
				i += 2;
			}
			else if (
				Match_(ptr, len, i+0, 0xf0, 0xe0) &&
				Match_(ptr, len, i+1, 0xc0, 0x80) &&
				Match_(ptr, len, i+2, 0xc0, 0x80)
				)
			{
				i += 3;
			}
			else if (
				Match_(ptr, len, i+0, 0xf8, 0xf0) &&
				Match_(ptr, len, i+1, 0xc0, 0x80) &&
				Match_(ptr, len, i+2, 0xc0, 0x80) &&
				Match_(ptr, len, i+3, 0xc0, 0x80)
				)
			{
				i += 4;
			}
			else
			{
				return false;
			}
		}
		return true;
	}

#ifdef _WIN32
	bool WriteTo(const wchar_t* fn, const void * data, size_t len)
	{
		DWORD wr;
		HANDLE hf = CreateFileW(fn, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
		if (hf != INVALID_HANDLE_VALUE)
		{
			WriteFile(hf, data, (DWORD)len, &wr, 0);
			CloseHandle(hf);
			return true;
		}
		return false;
	}
#endif

	bool WriteTo(const char* fn, const void * data, size_t len)
	{
#ifdef _WIN32
		DWORD wr;
		HANDLE hf = CreateFileA(fn, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, 0, 0);
		if (hf != INVALID_HANDLE_VALUE)
		{
			WriteFile(hf, data, (DWORD)len, &wr, 0);
			CloseHandle(hf);
			return true;
		}
#else
		FILE * fp = fopen(fn, "wb");
		if (fp)
		{
			fwrite(data, 1, len, fp);
			fclose(fp);
			return true;
		}
#endif
		return false;
	}

#ifdef _WIN32
	string xReadFile(LPCWSTR path)
	{
		string sa;
		HANDLE hf = ::CreateFile(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, NULL, 0);
		if (hf == INVALID_HANDLE_VALUE) return sa;
		DWORD dwSize = GetFileSize(hf, 0);
		DWORD rd = 0;
		sa.resize(dwSize);
		if (dwSize > 0)
		{
			ReadFile(hf, &sa[0], dwSize, &rd, 0);
			sa.resize(rd);
		}
		CloseHandle(hf);
		//if (sa.length() >= 3 && sa[0] == '\xef' && sa[1] == '\xbb' && sa[2] == '\xbf')
		//	return sa.substr(3);
		return sa;
	}
#endif
	char path_seperator()
	{
#ifdef _WIN32
		return '\\';
#else
		return '/';
#endif
	}

	int get_file_type(const char * fn)
	{
#ifdef _WIN32
		WIN32_FILE_ATTRIBUTE_DATA ad={0};
		if (!GetFileAttributesExA(fn, GetFileExInfoStandard, &ad)) return 0;
		if (ad.dwFileAttributes==INVALID_FILE_ATTRIBUTES) return 0;
		if (ad.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) return 2;
		return 1;
#else
		struct stat st = {0};
		if (stat(fn, &st)) return 0;
		if (S_ISREG(st.st_mode)) return 1;
		if (S_ISDIR(st.st_mode)) return 2;
		return 0;
#endif
	}
	int64_t get_file_mtime(const char * fn)
	{
#ifdef _WIN32
		WIN32_FILE_ATTRIBUTE_DATA ad={0};
		GetFileAttributesExA(fn, GetFileExInfoStandard, &ad);
		FILETIME & ft = ad.ftLastWriteTime;
		uint64_t x = ((uint64_t)ft.dwHighDateTime << 32) + ft.dwLowDateTime;
		x = (x-116444736000000000)/10000000;
		return (int64_t)x;
#else
		struct stat st = {0};
		stat(fn, &st);
		return st.st_mtime;
#endif
	}
	bool check_file_change(const char * fn, int64_t & mtime)
	{
		int64_t newtime = get_file_mtime(fn);
		if (newtime == mtime)
			return false;
		else
			return (mtime=newtime),true;
	}
	string xReadFile(const char* path)
	{
		string sa;
		FILE * fp = fopen(path, "rb");
		if (!fp) return sa;
		fseek(fp, 0, SEEK_END);
		ssize_t l = ftell(fp);
		fseek(fp, 0, SEEK_SET);
		if (l>0)
		{
			sa.resize(l);
			l = fread(&sa[0], 1, l, fp);
			sa.resize(l<0 ? 0 : l);
		}
		fclose(fp);
		//if (sa.length() >= 3 && sa[0] == '\xef' && sa[1] == '\xbb' && sa[2] == '\xbf')
		//	return sa.substr(3);
		return sa;
	}
#ifdef _WIN32
	void * map_file(const wchar_t * fn, uint64_t & fsize, uint64_t maxsizeallow)
	{
		void * m = 0;
		HANDLE hf = CreateFileW(fn, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, 0);
		LARGE_INTEGER fsz = { 0 };
		GetFileSizeEx(hf, &fsz);
		fsize = fsz.QuadPart;
		if (fsize > 0 && fsize <= maxsizeallow)
		{
			HANDLE hf1 = CreateFileMapping(hf, NULL, PAGE_READONLY, 0, 0, NULL);
			m = MapViewOfFile(hf1, FILE_MAP_READ, 0, 0, 0);
			CloseHandle(hf1);
		}
		CloseHandle(hf);
		return m;
	}
#endif
	void * map_file(const char * fn, uint64_t & fsize, uint64_t maxsizeallow)
	{
		void * m = 0;
#ifdef _WIN32
		HANDLE hf = CreateFileA(fn, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, 0);
		LARGE_INTEGER fsz = {0};
		GetFileSizeEx(hf, &fsz);
		fsize = fsz.QuadPart;
		if (fsize > 0 && fsize<=maxsizeallow)
		{
			HANDLE hf1 = CreateFileMapping(hf, NULL, PAGE_READONLY, 0, 0, NULL);
			m = MapViewOfFile(hf1, FILE_MAP_READ, 0, 0, 0);
			CloseHandle(hf1);
		}
		CloseHandle(hf);
#else
		int fin = open(fn, O_RDONLY);
		struct stat st;
		if (fin>0 && fstat(fin, &st)>=0)
		{
			fsize = st.st_size;
			if (fsize > 0 && fsize<=maxsizeallow)
				m = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fin, 0);
		}
#endif
		return m;
	}
	void * map_file_rw(const char * fn, uint64_t & fsize, uint64_t maxsizeallow, bool shared)
	{
		void * m = 0;
#ifdef _WIN32
		HANDLE hf = CreateFileA(fn, GENERIC_READ|GENERIC_WRITE,
			shared ? FILE_SHARE_READ|FILE_SHARE_WRITE : FILE_SHARE_READ, NULL, OPEN_ALWAYS, 0, 0);
		LARGE_INTEGER fsz = {0};
		GetFileSizeEx(hf, &fsz);
		fsize = fsz.QuadPart;
		if (fsize > 0 && fsize<=maxsizeallow)
		{
			HANDLE hf1 = CreateFileMapping(hf, NULL, PAGE_READWRITE, 0, 0, NULL);
			m = MapViewOfFile(hf1, FILE_MAP_READ|FILE_MAP_WRITE, 0, 0, 0);
			CloseHandle(hf1);
		}
		CloseHandle(hf);
#else
		int fin = open(fn, O_RDWR|O_CREAT
#               ifdef O_LARGEFILE
				|O_LARGEFILE
#               endif
				, 0644);
		struct stat st;
		if (fin>0 && fstat(fin, &st)>=0)
		{
			fsize = st.st_size;
			if (fsize > 0 && fsize<=maxsizeallow)
				m = mmap(NULL, st.st_size, PROT_WRITE, shared ? MAP_SHARED : MAP_PRIVATE, fin, 0);
		}
#endif
		return m;
	}

	void unmap_file(void * mem, uint64_t fsize)
	{
#ifdef _WIN32
		(void)fsize;
		UnmapViewOfFile(mem);
#else
		munmap(mem, fsize);
#endif
	}
	bool ComputeRela(LPCSTR root0, LPCSTR urlto0, LPCSTR urlfrom0, string & res, bool ic)
	{
		string root = root0;
		string urlfrom = urlfrom0;
		string urlto = urlto0;
		std::replace(root.begin(), root.end(), '\\', '/');
		std::replace(urlfrom.begin(), urlfrom.end(), '\\', '/');
		std::replace(urlto.begin(), urlto.end(), '\\', '/');

		if (root.length() == 0 || root[root.length()-1]!='/')
		{
			root += '/';
		}
		//int (*scmp)(const char *,const char *) = ic ? &strcmp : &_stricmp;
		int (*sncmp)(const char *,const char *, size_t) = ic ? &strncmp : &_strnicmp;

		int min_sp = (int) (std::min)(urlfrom.length(), urlto.length());
		int share_n = -1;
		for (int i=min_sp; --i>=0; )
		{
			if (urlfrom[i] == urlto[i] && urlfrom[i] == '/')
			{
				if (sncmp(urlfrom.c_str(), urlto.c_str(), i) == 0)
				{
					//ok, find common part.
					share_n = i+1;
					break;
				}
			}
		}
		if (share_n > 0 && sncmp(root.c_str(), urlfrom.substr(0, share_n).c_str(), root.length()) == 0)
		{
			string tail = urlto.substr(share_n);
			string toShare;
			for (int i=share_n, im=(int)urlfrom.length(); i<im; ++i)
			{
				if (urlfrom[i] == '/')
				{
					toShare += "../";
				}
			}
			res = toShare + tail;
			return true;
		}
		return false;
	}

	string encode16(const void * data, size_t len)
	{
		BYTE * pb = (BYTE*)data;
		const char * h = "0123456789abcdef";
		string s;
		s.resize(len*2);
		char * q = (char*)s.data();
		for (size_t i=0; i<len; ++i)
		{
			q[i*2+0] = h[pb[i]>>4];
			q[i*2+1] = h[pb[i]&0xf];
		}
		return s;
	}

	bool decode16(const char * encdata, string & res)
	{
		size_t len = strlen(encdata);
		string r;
		r.reserve(len/2);
		int pos = 0;
		BYTE k = 0;
		for (size_t i=0; i<len; ++i)
		{
			char ch = encdata[i];
			if (ch>='0' && ch<='9')
			{
				k = (k<<4) + ch-'0';
			}
			else if (ch>='a' && ch<='f')
			{
				k = (k<<4) + ch-'a' + 10;
			}
			else if (ch>='A' && ch<='F')
			{
				k = (k<<4) + ch-'A' + 10;
			}
			else
			{
				continue;
			}
			if ((++pos & 1) == 0)
			{
				r += k;
			}
		}
		res.swap(r);
		return (pos&1) == 0;
	}

	const char * dump_hex(uintptr_t stpos, const void * buf, size_t sz, string & s)
	{
		if (!buf)
		{
			return "(null)\r\n\r\n";
		}

		const char * hextbl = "0123456789abcdef";
		string & sa = const_cast<string&>(s);

		char cbuf[100];

		for (size_t i=0; i<sz; i+=16)
		{
			const char * ptr = (const char *)buf + i;
			uintptr_t addr = stpos + i;
			size_t l = sz-i; if (l>16) l = 16;
			char * os = cbuf;

			for (int j=0; j<8; ++j)
			{
				int o = 4 * (8-j-1);
				*os++ = hextbl[0xf & (addr>>o)];
			}
			*os++ = ':';
			*os++ = ' ';
			*os++ = ' ';

			for (uint32_t i=0; i<16; ++i)
			{
				if (i<l)
				{
					*os++ = hextbl[0xf&(ptr[i]>>4)];
					*os++ = hextbl[0xf&(ptr[i])];
					*os++ = (i==7&&l>8) ? '-' : ' ';
				}
				else
				{
					*os ++ = ' ';
					*os ++ = ' ';
					*os ++ = ' ';
				}
			}
			*os++ = ' ';
			*os++ = ' ';
			*os++ = ' ';

			for (uint32_t i=0; i<l; ++i)
			{
				unsigned char ch = ptr[i];
				*os++ = isprint(ch) ? ch : '.';
			}
			*os ++ = '\r';
			*os ++ = '\n';
			*os ++ = 0;
			sa += cbuf;
		}
		sa += "\r\n";
		return sa.c_str();
	}

	string strerr(unsigned int oserr)
	{
#ifdef _WIN32
		LPTSTR lpMsgBuf = 0;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL, oserr, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
			(LPTSTR)&lpMsgBuf, 0, NULL);
		string sa;
		sa.resize(wcslen(lpMsgBuf) * 3 + 10);
		int n = WideCharToMultiByte(CP_UTF8, 0, lpMsgBuf, -1, &sa[0], (int)sa.length(), 0, 0);
		if (n <= 0) sa.clear();
		else sa.resize(n);
		LocalFree(lpMsgBuf);
		return sa;
#else
		string sa = strerror(errno);
		return sa;
#endif
	}

	char * getlasterrstr(char * msg, int msglen)
	{
#ifdef _WIN32
		DWORD err = GetLastError();
		LPTSTR lpMsgBuf = 0;
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL, err, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
			(LPTSTR) &lpMsgBuf, 0, NULL );
		string sa;
		sa.resize(wcslen(lpMsgBuf)*3+10);
		int n = WideCharToMultiByte(CP_UTF8, 0, lpMsgBuf, -1, &sa[0], (int)sa.length(), 0, 0);
		if (n <= 0) sa.clear();
		else sa.resize(n);
		LocalFree(lpMsgBuf);
		sutil::strlcpy(msg, msglen, sa.c_str());
		return msg;
#elif defined(__linux__)
		return strerror_r(errno, msg, msglen);
#else
        char * s = strerror(errno);
        strlcpy(msg, s, msglen);
        return msg;
#endif
	}
#if defined(_WIN32)
	char * getappname()
	{
		char fn[MAX_PATH] = {0};
		GetModuleFileNameA(0, fn, MAX_PATH);
		char * pch = fn + strlen(fn);
		while (pch > fn && !(pch[-1] == '\\' || pch[-1] == '/')) --pch;
		memmove(fn, pch, strlen(pch)+1);
		pch = strrchr(fn, '.');
		if (pch) *pch = 0;
		return _strdup(fn);
	}
#elif  defined(__APPLE__)
	char * getappname()
	{
		struct kinfo_proc process_info;
		size_t process_info_len = sizeof(process_info);
		int process_info_mib[4] = { CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid() };
		int process_info_mib_len = 4;
		memset(&process_info, 0, sizeof(process_info));
		if (sysctl(process_info_mib, process_info_mib_len, &process_info, &process_info_len, NULL, 0) == 0)
		{
			return strdup(process_info.kp_proc.p_comm);
		}

		return strdup("unkapp");
	}
#elif defined(__linux__)
	char * getappname()
	{
		char path[1024] = {0};
		char id[256];
		sprintf(id, "/proc/%d/exe", getpid());
		if (readlink(id, path, sizeof(path)-1) <= 0) path[0]=0;
		const char * pf = strrchr(path, '/');
		if (pf) pf++;
		else pf = path;
		if (pf[0] == 0) pf = "unkapp";
		return strdup(pf);
	}
#endif

	bool find_resource(const char * dir, const char * fname, string * rdir, string * rfile)
	{
#ifdef _WIN32
		char filename[MAX_PATH] = { 0 };
		GetModuleFileNameA(0, filename, sizeof(filename));
		strrchr(filename, '\\')[1] = 0;
		string s0 = filename;
		for (int i = 0; i < 3; ++i)
		{
			string s = s0 + fname;
			DWORD d = GetFileAttributesA(s.c_str());
			if (d != INVALID_FILE_ATTRIBUTES && (d&FILE_ATTRIBUTE_DIRECTORY) == 0)
			{
				if (rfile) *rfile = s;
				if (rdir) *rdir = s0;
				return true;
			}
			size_t pos = s0.rfind('\\', s0.length() - 2);
			if (pos < s0.length() && pos + 1 < s0.length() && pos >= 2)
			{
				s0.resize(pos + 1);
			}
			else
				return false;
		}
		return false;
#else
		string fn;
		char path[300];
		fn.reserve(300);

		auto is_file = [&]()->bool{
			fn = path;
			fn += fname;
			struct stat st;
			if (stat(fn.c_str(), &st) == 0 && S_ISREG(st.st_mode))
			{
				if (rdir) *rdir = path;
				if (rfile) *rfile = fn;
				return true;
			}
			return false;
		};

		sprintf(path, "/usr/share/%s/", dir);
		if (is_file()) return true;

		sprintf(path, "/usr/local/share/%s/", dir);
		if (is_file()) return true;

		const char * homedir = getenv("HOME");
		if (!homedir || strlen(homedir)>100) return false;

		sprintf(path, "%s/.%s/", homedir, dir);
		if (is_file()) return true;

		sprintf(path, "%s/.swigger/%s/", homedir, dir);
		if (is_file()) return true;

		return false;
#endif
	}

	unsigned int get_cpu_count()
	{
#if defined(CTL_HW) && defined(HW_NCPU)
		unsigned n;
		int mib[2] = { CTL_HW, HW_NCPU };
		std::size_t s = sizeof(n);
		sysctl(mib, 2, &n, &s, 0, 0);
		return n;
#elif defined(_SC_NPROCESSORS_ONLN)
		long result = sysconf(_SC_NPROCESSORS_ONLN);
		// sysconf returns -1 if the name is invalid, the option does not exist or
		// does not have a definite limit.
		// if sysconf returns some other negative number, we have no idea
		// what is going on. Default to something safe.
		if (result < 0)
			return 0;
		return static_cast<unsigned>(result);
#elif defined(_WIN32)
		SYSTEM_INFO info;
		GetSystemInfo(&info);
		return info.dwNumberOfProcessors;
#else
		// TODO: grovel through /proc or check cpuid on x86 and similar
		// instructions on other architectures.
		return 0;  // Means not computable [thread.thread.static]
#endif
	}
}

#ifndef _WIN32
static int64_t x_time(const timespec & ts)
{
	int64_t r = ts.tv_sec;
	r = r*1000 + ts.tv_nsec/1000000;
	return r;
}
static void get_result(crefstr name, struct dirent * pde, CTranverseDIR::FileAttr & fa)
{
	fa.os_type = pde->d_type;
	struct stat st;
	memset(&st, 0, sizeof(st));
	lstat(name.c_str(), &st);
	fa.size = st.st_size;
	switch (pde->d_type)
	{
	case DT_DIR: fa.type = CTranverseDIR::FileAttr::FA_DIR; break;
	case DT_LNK: fa.type = CTranverseDIR::FileAttr::FA_LINK; break;
	case DT_REG: fa.type = CTranverseDIR::FileAttr::FA_NORMAL; break;
	default: fa.type = CTranverseDIR::FileAttr::FA_OTHER; break;
	}
#ifdef __MACH__
	fa.atime = x_time(st.st_atimespec);
	fa.mtime = x_time(st.st_mtimespec);
	fa.ctime = x_time(st.st_ctimespec);
#else
	fa.atime = x_time(st.st_atim);
	fa.mtime = x_time(st.st_mtim);
	fa.ctime = x_time(st.st_ctim);
#endif
}
void CTranverseDIR::Clear(vector<DIRINFO> & dirs)
{
	for (size_t i=0,mi=dirs.size(); i<mi; ++i)
	{
		DIR * p = (DIR*) dirs[i].dirhd;
		if (p) closedir(p);
	}
	dirs.clear();
}
void CTranverseDIR::Clear(DIRINFO & info)
{
	DIR * p = (DIR*) info.dirhd;
	if (p) closedir(p);
	info.dirhd = 0;
}

CTranverseDIR::CTranverseDIR(const char * basedir, bool dfirst):m_dfirst(dfirst)
{
	string nbasedir;
	if (!basedir || !*basedir) basedir = ".";
	nbasedir = basedir;
	if (nbasedir[nbasedir.length()-1] != '/')
	{
		nbasedir += '/';
	}
	m_dirs.push_back(DIRINFO::make(nbasedir));
}

bool CTranverseDIR::skip_current()
{
	if (m_dirs.empty()) return false;
	vector<DIRINFO>::iterator it;
	it = m_dfirst ? m_dirs.end()-1 : m_dirs.begin();
	if (it->dirhd)closedir((DIR*)it->dirhd);
	m_dirs.erase(it);
	return true;
}
bool CTranverseDIR::next(string & name, FileAttr & fa, string * fn)
{
	m_dirs.insert(m_dirs.end(), m_dirs2.begin(), m_dirs2.end());
	m_dirs2.clear();
	if (m_dirs.empty()) return false;

	DIRINFO & x = m_dfirst ? m_dirs.back() : m_dirs.front();
	if (x.dirhd == 0) x.dirhd = opendir(x.name.c_str());
	if (x.dirhd != 0)
	{
		struct dirent de, *pde = 0;
		while (readdir_r((DIR*)x.dirhd, &de, &pde)==0)
		{
			if (pde == 0) break;
			if (strcmp(pde->d_name, ".")==0) continue;
			if (strcmp(pde->d_name, "..")==0) continue;

			name = x.name + pde->d_name;
			if (fn)*fn = pde->d_name;
			get_result(name, pde, fa);
			if (pde->d_type == DT_DIR)
			{
				add_dirinfo(m_dirs2, DIRINFO::make(name+"/"));
			}
			return true;
		}
	}
	if (x.dirhd) closedir((DIR*)x.dirhd);
	if (m_dfirst)
		m_dirs.pop_back();
	else
		m_dirs.erase(m_dirs.begin());
	return next(name, fa, fn);
}
#else
static int64_t x_time(const FILETIME & ts)
{
	int64_t r = ((int64_t)ts.dwHighDateTime<<32) + ts.dwLowDateTime;
	return  (r/10000 - 11644473600000LL);
}

static void get_result(crefstr name, WIN32_FIND_DATAA & wfd, CTranverseDIR::FileAttr & fa)
{
	fa.os_type = wfd.dwFileAttributes;
	fa.size = ((int64_t)wfd.nFileSizeHigh<<32) + wfd.nFileSizeLow;
	if (wfd.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)
	{
		fa.type = CTranverseDIR::FileAttr::FA_LINK;
	}
	else if (wfd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
	{
		fa.type = CTranverseDIR::FileAttr::FA_DIR;
	}
	else
	{
		fa.type = CTranverseDIR::FileAttr::FA_NORMAL;
	}
	fa.atime = x_time(wfd.ftLastAccessTime);
	fa.mtime = x_time(wfd.ftLastWriteTime);
	fa.ctime = x_time(wfd.ftCreationTime);
}
void CTranverseDIR::Clear(vector<DIRINFO> & dirs)
{
	for (size_t i=0,mi=dirs.size(); i<mi; ++i)
	{
		HANDLE d = dirs[i].dirhd;
		if (d != INVALID_HANDLE_VALUE) CloseHandle(d);
	}
	dirs.clear();
}
void CTranverseDIR::Clear(DIRINFO & info)
{
	HANDLE d = info.dirhd;
	if (d != INVALID_HANDLE_VALUE) CloseHandle(d);
	info.dirhd = INVALID_HANDLE_VALUE;
}
CTranverseDIR::CTranverseDIR(const char * basedir, bool dfirst):m_dfirst(dfirst)
{
	string nbasedir;
	if (!basedir || !*basedir) basedir = ".";
	nbasedir = basedir;
	std::replace(nbasedir.begin(),nbasedir.end(), '/', '\\');
	if (nbasedir[nbasedir.length()-1] != '\\')
	{
		nbasedir += '\\';
	}
	m_dirs.push_back(DIRINFO::make(nbasedir));
}

bool CTranverseDIR::skip_current()
{
	if (m_dirs.empty()) return false;
	vector<DIRINFO>::iterator it;
	it = m_dfirst ? m_dirs.end()-1 : m_dirs.begin();
	if (it->dirhd != INVALID_HANDLE_VALUE) CloseHandle(it->dirhd);
	m_dirs.erase(it);
	return true;
}

bool CTranverseDIR::next(string & name, FileAttr & fa, string * fn)
{
	m_dirs.insert(m_dirs.end(), m_dirs2.begin(), m_dirs2.end());
	m_dirs2.clear();
	if (m_dirs.empty()) return false;

	DIRINFO & x = m_dfirst ? m_dirs.back() : m_dirs.front();
	bool first = false;
	WIN32_FIND_DATAA wfd;
	if (x.dirhd == INVALID_HANDLE_VALUE)
	{
		x.dirhd = FindFirstFileA((x.name+"*").c_str(), &wfd);
		first = true;
	}
	if (x.dirhd != INVALID_HANDLE_VALUE)
	{
		while (first || FindNextFileA(x.dirhd, &wfd))
		{
			first = false;
			if (strcmp(wfd.cFileName, ".")==0) continue;
			if (strcmp(wfd.cFileName, "..")==0) continue;

			name = x.name + wfd.cFileName;
			if (fn)*fn = wfd.cFileName;
			get_result(name, wfd, fa);
			if (fa.type == FileAttr::FA_DIR)
			{
				add_dirinfo(m_dirs2, DIRINFO::make(name+"\\"));
			}
			return true;
		}
	}
	if (x.dirhd != INVALID_HANDLE_VALUE) FindClose(x.dirhd);
	if (m_dfirst)
		m_dirs.pop_back();
	else
		m_dirs.erase(m_dirs.begin());
	return next(name, fa, fn);
}
#endif

CTranverseDIR::~CTranverseDIR()
{
	Clear(m_dirs);
	Clear(m_dirs2);
}
void CTranverseDIR::skip()
{
	Clear(m_dirs2);
}

#ifdef _WIN32
#include <io.h>
#include <windows.h>
#include <stdio.h>

static DWORD old_mode;
static HANDLE cons_handle;

static BOOL WINAPI GetPassConsoleControlHandler(DWORD dwCtrlType)
{
	switch (dwCtrlType){
	case CTRL_BREAK_EVENT:
	case CTRL_C_EVENT:
		printf("Interrupt\n");
		fflush(stdout);
		(void)SetConsoleMode(cons_handle, old_mode);
		ExitProcess(-1);
		break;
	default:
		break;
	}
	return TRUE;
}

extern "C" char * getpass(const char *prompt)
{
	DWORD new_mode;
	char *ptr;
	int scratchchar;
	static char password[100 + 1];
	int pwsize = sizeof(password);

	cons_handle = GetStdHandle(STD_INPUT_HANDLE);
	if (cons_handle == INVALID_HANDLE_VALUE)
		return NULL;
	if (!GetConsoleMode(cons_handle, &old_mode))
		return NULL;

	new_mode = old_mode;
	new_mode |= (ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT);
	new_mode &= ~(ENABLE_ECHO_INPUT);

	if (!SetConsoleMode(cons_handle, new_mode))
		return NULL;

	SetConsoleCtrlHandler(&GetPassConsoleControlHandler, TRUE);

	(void)fputs(prompt, stderr);
	(void)fflush(stderr);
	(void)memset(password, 0, pwsize);

	if (fgets(password, pwsize, stdin) == NULL) {
		if (ferror(stdin))
			goto out;
		(void)fputc('\n', stderr);
	}
	else {
		(void)fputc('\n', stderr);

		if ((ptr = strchr(password, '\n')))
			*ptr = '\0';
		else /* need to flush */
			do {
				scratchchar = getchar();
			} while (scratchchar != EOF && scratchchar != '\n');
	}

out:
	(void)SetConsoleMode(cons_handle, old_mode);
	SetConsoleCtrlHandler(&GetPassConsoleControlHandler, FALSE);

	return password;
}
#endif


//#ifdef _DEBUG
//#include "tdd.h"
//
//BEG_TEST(CombineUrl)
//string s;
//TDD_ASSERT((Helper::CombineUrl("http://a/x", "../a.jpg", s) && s == "http://a/a.jpg"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/", "../a.jpg", s) && s == "http://a/a.jpg"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/u", "../a.jpg", s) && s == "http://a/a.jpg"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/u/", "../a.jpg", s) && s == "http://a/x/a.jpg"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/u/", "../a.jpg?a", s) && s == "http://a/x/a.jpg?a"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/u/", "../a.jpg#b", s) && s == "http://a/x/a.jpg#b"));
//TDD_ASSERT((Helper::CombineUrl("http://a/x/u/?a=/a/b/x", "../a.jpg?#b", s) && s == "http://a/x/a.jpg?#b"));
//END_TEST()
//
//#endif
