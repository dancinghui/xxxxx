#pragma once

namespace sutil
{
	inline char lc(char c)
	{
		if (c>='A'&&c<='Z') return c-'A'+'a';
		return c;
	}
	inline bool is_ansi_space(int c){return c>=0 && c<=0x7f && isspace(c);}
	inline const char* eat_space(const char * & ptr)
	{
		while (is_ansi_space(*ptr))++ptr;
		return ptr;
	}
	inline const char* eat_onlyspace(const char * & ptr)
	{
		while (*ptr==' ') ++ptr;
		return ptr;
	}
	inline void s_make_lower(string & s)
	{
		for (size_t i=0; i<s.length(); ++i)
		{
			if (s[i]>='A'&&s[i]<='Z')
				s[i] = s[i]-'A'+'a';
		}
	}
	inline void s_make_lower(char * s)
	{
		for (size_t i=0; s[i]; ++i)
		{
			if (s[i]>='A'&&s[i]<='Z')
				s[i] = s[i]-'A'+'a';
		}
	}
	inline void s_make_upper(string & s)
	{
		for (size_t i=0; i<s.length(); ++i)
		{
			if (s[i]>='a'&&s[i]<='z')
				s[i] = s[i]-'a'+'A';
		}
	}
	inline void s_make_upper(char * s)
	{
		for (size_t i=0; s[i]; ++i)
		{
			if (s[i]>='a'&&s[i]<='z')
				s[i] = s[i]-'a'+'A';
		}
	}
	//return value: 0=>fail, 1=>ok, 2=>no end.
	int mid_s(const char * data, const char *beg, const char * end, string &code);
	void s_read_word(const char * & h, string & w);
	bool s_read_line(const char * & h, string & line);
	bool s_eq(const char * s1, const char * s2);
	bool s_eq_ic(const char * s1, const char * s2);
	bool s_begin_with(const char * s, const char * sf);
	bool s_begin_with_ic(const char * s, const char * sf);
	bool s_end_with(const char * s, const char * sf);
	bool s_end_with_ic(const char * s, const char * sf);

	string& trim(string & s);
	char * trim(char * s);

	unsigned int get_hash(const wchar_t * ps);
	unsigned int get_hash(const char* ps);
	unsigned int get_hash_l(const wchar_t * ps);
	unsigned int get_hash_l(const char* ps);

	wchar_t * wcslcat(wchar_t * dst, size_t len, const wchar_t * src);
	wchar_t * wcslcpy(wchar_t * dst, size_t len, const wchar_t * src);
	char * strlcat(char * dst, size_t len, const char * src);
	char * strlcpy(char * dst, size_t len, const char * src);
	template <int N> wchar_t * wcslcat(wchar_t (&dst)[N], const wchar_t * src){return wcslcat(dst, N, src);}
	template <int N> wchar_t * wcslcpy(wchar_t (&dst)[N], const wchar_t * src){return wcslcpy(dst, N, src);}
	template <int N> char * strlcat(char (&dst)[N], const char * src){return strlcat(dst, N, src);}
	template <int N> char * strlcpy(char (&dst)[N], const char * src){return strlcpy(dst, N, src);}

	template <class tstring>
	tstring replace_str_(const tstring & org, const tstring& a, const tstring& b)
	{
		if (a.empty()) return org;
		tstring r;
		r.reserve(org.length());
		for (size_t pos=0; ; )
		{
			size_t prepos = pos;
			pos = org.find(a, pos);
			if (pos != tstring::npos)
			{
				//[prepos, pos) [pos,pos+l)
				r.append(org.c_str()+prepos, pos-prepos);
				r.append(b);
				pos = pos + a.length();
			}
			else
			{
				//[prepos, pos)
				r.append(org.substr(prepos));
				break;
			}
		}
		return r;
	}

	template <class tstring, class T2, class T3>
	tstring replace_str(const tstring & org, const T2& a, const T3& b)
	{
		return replace_str_<tstring>(org,a,b);
	}

	bool match_wildcard(const char* pat, const char* str);
	void split_cmd_string(const char* str, vector<string> &vecStr);
	vector<string> split_str(crefstr ins, crefstr spl, int maxs = -1);
	
	inline void remove_empty(vector<string> & args)
	{
		auto it = std::remove(args.begin(), args.end(), "");
		args.erase(it, args.end());
	}
}
