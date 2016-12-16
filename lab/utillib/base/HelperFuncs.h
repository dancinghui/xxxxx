#pragma once

namespace Helper
{
	string xReadFile(const char* path);
	int64_t get_file_mtime(const char * path);
	bool check_file_change(const char * fn, int64_t & mtime);
	inline bool strip_utf8bom(string & sa)
	{
		if (sa.length() >= 3 && sa[0] == '\xef' && sa[1] == '\xbb' && sa[2] == '\xbf')
			return sa.erase(0, 3), true;
		else
			return false;
	}
	//returns : 0:non exist, 1 file, 2 dir.
	int get_file_type(const char * path);
	char path_seperator();
	void * map_file(const char *fn, uint64_t & fsize, uint64_t maxsizeallow=0xffffffffffffffffull);
	void * map_file_rw(const char * fn, uint64_t & fsize, uint64_t maxsizeallow=0xffffffffffffffffull, bool shared=false);
	void unmap_file(void * mem, uint64_t fsize);

	bool WriteTo(const char * fn, const void * data, size_t len);
#ifdef _WIN32
	void * map_file(const wchar_t * fn, uint64_t & fsize, uint64_t maxsizeallow);
	string xReadFile(const wchar_t* path);
	bool WriteTo(const wchar_t * fn, const void * data, size_t len);
#endif
	string encode16(const void * data, size_t len);
    inline string encode16(crefstr s){return encode16(s.data(), s.length());}
	bool decode16(const char * encdata, string & res);
	bool IsTextUtf8(const void * ptr_, int len);
	const char * dump_hex(uintptr_t spos, const void * buf, size_t sz, string & s);

	template <class cs>
	void CString_Reserve(cs & s, DWORD len)
	{
		int len1 = s.GetLength();
		if (len < len1) return ;
		s.GetBuffer(len);
		s.ReleaseBuffer(len1);
	}

	template <class M, class V, class TR>
	typename M::mapped_type findmap(const M & mp, const V & v, TR tr)
	{
		typename M::const_iterator p = mp.find(v);
		if (p == mp.end()) return tr;
		return p->second;
	}

	inline size_t line_len(const char * ptr)
	{
		if (!ptr) return 0;
		size_t o = 0;
		while (ptr[o] != '\n' && ptr[o]!='\r' && ptr[o]!=0) ++ o;
		return o;
	}
	string strerr(unsigned int oserr);
	char * getlasterrstr(char * msg, int msglen);
	char * getappname();
	bool find_resource(const char * dir, const char * fname, string * rdir, string * rfile);

	unsigned int get_cpu_count();
}

namespace autoclose
{
	template <class T>
	struct autoclose_delete_helper
	{
		static void delete_func(T ptr)
		{
			delete ptr;
		}
		static void delete_arr_func(T ptr)
		{
			delete [] ptr;
		}
	};
#define AUTOCLOSE_MV_(a,b) a##b
#define AUTOCLOSE_MV(a,b) AUTOCLOSE_MV_(a,b)

	char is_lvalue(...);
	template <class T>
	uint16_t is_lvalue(T&);

	template <class FT, class VT, int N>
	struct autoclose_st2;

	template <class FT, class VT>
	struct autoclose_st2<FT, VT, 2>
	{
		FT f;
		VT & v;
		autoclose_st2(FT f, VT & v) : f(f), v(v){}
		~autoclose_st2(){f(v);}
	};
	template <class FT, class VT>
	struct autoclose_st2<FT, VT, 1>
	{
		FT f;
		VT v;
		autoclose_st2(FT f, VT v) : f(f), v(v){}
		~autoclose_st2(){f(v);}
	};
#define AUTOCLOSE(f,v) autoclose::autoclose_st2<decltype(&f),decltype(v), sizeof(autoclose::is_lvalue(v))> AUTOCLOSE_MV(autoclose_obj_,__LINE__)(&f, v);
#define AUTOCLOSE_DELETE(v) AUTOCLOSE(autoclose::autoclose_delete_helper<decltype(v)>::delete_func,v);
#define AUTOCLOSE_DELETEARR(v) AUTOCLOSE(autoclose::autoclose_delete_helper<decltype(v)>::delete_arr_func,v);
#define AUTO_CLOSE(f,v) AUTOCLOSE(f,v)

#if defined(__i386__) || defined(__amd64__) || defined(_M_IX86) || defined(_M_AMD64)
	struct autoclose_st3
	{
		std::function<void()> f;
		~autoclose_st3(){
			if (f) f();
		}
		template <class T>
		void operator = (T obj){ f = obj; }
	};
#define AUTOCLOSE_BLOCK() autoclose::autoclose_st3 AUTOCLOSE_MV(autoclose_obj3_,__LINE__); AUTOCLOSE_MV(autoclose_obj3_,__LINE__)=[&]()
#endif
}

template <class T>
int cmp(const T&a, const T&b)
{
	if (a==b) return 0;
	return a<b ? -1 : 1;
}

template <class T, int cnt>
struct bufextend : T
{
	char buf[cnt];
	bufextend(){memset(this,0,sizeof(*this));}
};
template <unsigned int cnt>
struct buf_scalable
{
protected:
	char * pbuf;
	char buf[cnt];
public:
	size_t sz;

	buf_scalable():sz(cnt),pbuf(0){}
	~buf_scalable(){free(pbuf);}
	void expand(size_t newsz)
	{
		if (newsz<=sz) return ;
		sz = newsz;
		pbuf = (char*) realloc(pbuf, sz);
	}
	char* ptr(){return sz<=cnt ? buf : pbuf;}
};

template <int cnt>
struct buf_st
{
	char buf[cnt];
	buf_st(const char* p){if (p)strncpy(buf,p,cnt);}
	buf_st(){}
	void z(){memset(buf,0,cnt);}
	operator char * () const {return (char*)buf;}
	operator unsigned char * () const {return (unsigned char*)buf;}
	char* ptr()const{return (char*)buf;}
};

template <class T>
struct ObjIf
{
	T * pobj;
	char mem[sizeof(T)];
	bool usemem;
	ObjIf(T * ptr)
	{
		usemem =  false;
		pobj = ptr;
		if (!pobj)
		{
			usemem = true;
			pobj = new (mem) T;
		}
	}
	~ObjIf()
	{
		if (usemem)
		{
			pobj->~T();
		}
	}
};

#define ENSURE_NON_EMPTY(type, obj, ptr)\
	ObjIf<type> obj##_(ptr); type & obj = *obj##_.pobj;

template <class T1, class T2>
inline void force_assign(T1& a, const T2& b)
{
	//static_assert(sizeof(T1) == sizeof(T2), "must be same size");
	typedef int static_assert_size_equal [ sizeof(T1)==sizeof(T2) ? 1 : -1 ];
	a = *(T1*)&b;
}


struct clear_mem_t{};
const clear_mem_t* const clearmem=0;
inline void * operator new (size_t sz, const clear_mem_t*)
{
	return calloc(1, sz);
}
inline void zero_range(void* a, void *b)
{
	memset(a, 0, (char*)b-(char*)a);
}

#define _BX(a,b) (unsigned char)(0x##a >> (8*b))
#define MAKE_GUID(name, a,b,c,d,e) GUID name = {0x##a,0x##b,0x##c,{_BX(d,1),_BX(d,0),_BX(e,5),_BX(e,4),_BX(e,3),_BX(e,2),_BX(e,1),_BX(e,0)}}

class CTranverseDIR
{
public:
	struct FileAttr
	{
		enum{
			FA_DIR = 1,
			FA_NORMAL = 2,
			FA_LINK = 3,
			FA_OTHER = 4
		}type;
		int os_type;
		int64_t size;
		int64_t atime, mtime, ctime;
	};
	struct DIRINFO
	{
		string name;
		int depth;
		//note: don't write dtor to free dirhd, since we can't write a copy-ctor to copy it.
#ifdef _WIN32
		HANDLE dirhd;
		DIRINFO():depth(0),dirhd(INVALID_HANDLE_VALUE){}
#else
		void * dirhd;
		DIRINFO():depth(0),dirhd(0){}
#endif
		static DIRINFO make(const std::string& n)
		{
			DIRINFO d;
			d.name = n;
			return d;
		}
	};
private:
	const bool m_dfirst;
	vector<DIRINFO> m_dirs, m_dirs2;
public:
	CTranverseDIR(const char * basedir, bool dfirst=true);
	virtual ~CTranverseDIR();
	void skip();
	bool skip_current();
	bool next(string & name, FileAttr & fa, string * fn=0);
protected:
	void Clear(vector<DIRINFO>& dir);
	void Clear(DIRINFO & info);
	virtual void add_dirinfo(vector<DIRINFO>& dir, const DIRINFO & info)
	{
		dir.push_back(info);
	}
};
