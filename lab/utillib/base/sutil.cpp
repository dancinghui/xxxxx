#include "stdafx.h"
#include "sutil.h"

namespace sutil
{
	int mid_s(const char * data, const char *beg, const char * end, string &code)
	{
		const char * p1 = strstr(data, beg);
		if (!p1) return 0;
		p1 += strlen(beg);
		const char * p2 = strstr(p1, end);
		if (p2)
			return code.assign(p1, p2-p1), 1;
		else
			return code.assign(p1), 2;
	}

	void s_read_word(const char * & h, string & w)
	{
		int i;
		for (i=0; ;++i)
		{
			if (h[i] == 0 || is_ansi_space(h[i])) break;
		}
		w.assign(h, i);
		h += i;
	}

	bool s_read_line(const char * & h, string & line)
	{
		int i;
		int ext = 0;
		for (i=0; ;++i)
		{
			if (h[i]=='\r' && h[i+1]=='\n')
			{
				ext = 2;
				break;
			}
			if (h[i]=='\n')
			{
				ext = 1;
				break;
			}
			if (h[i] == 0)
				return false;
		}
		line.assign(h, i);
		h += i+ext;
		return true;
	}

	bool s_eq(const char * s1, const char * s2)
	{
		return strcmp(s1, s2) == 0;
	}
	bool s_eq_ic(const char * s1, const char * s2)
	{
		return _stricmp(s1, s2) == 0;
	}
	bool s_end_with(const char * s, const char * sf)
	{
		size_t lena = strlen(s);
		size_t lenb = strlen(sf);
		return lena>=lenb && strcmp(s+lena-lenb, sf)==0;
	}
	bool s_end_with_ic(const char * s, const char * sf)
	{
		size_t lena = strlen(s);
		size_t lenb = strlen(sf);
		return lena>=lenb && _stricmp(s+lena-lenb, sf)==0;
	}
	bool s_begin_with(const char * s, const char * sf)
	{
		return strncmp(s, sf, strlen(sf)) == 0;
	}
	bool s_begin_with_ic(const char * s, const char * sf)
	{
		size_t len = strlen(sf);
		for (size_t i=0; i<len; ++i)
		{
			char ch1 = s[i];
			char ch2 = sf[i];
			if ((ch1>='a'&&ch1<='z') || (ch1>='A'&&ch1<='Z'))
			{
				ch1 |= 0x20;
				ch2 |= 0x20;
			}
			if (ch1 != ch2) return false;
		}
		return true;
	}
	template <class T>
	static bool trim_se(T * s, size_t len, size_t& start, size_t& end)
	{
		start = 0;
		end = len;
		for (size_t i=len; i>0; i--)
		{
			if (is_ansi_space(s[i-1])) end=i-1;
			else break;
		}
		for (size_t i=0; i<end; ++i)
		{
			if (is_ansi_space(s[i])) start = i+1;
			else break;
		}
		return start!=0 || end!=len;
	}
	string& trim(string & s)
	{
		size_t st, end;
		if (trim_se(s.c_str(), s.length(), st, end))
		{
			s.erase(s.begin()+end, s.end());
			s.erase(s.begin(), s.begin()+st);
		}
		return s;
	}
	char * trim(char * s)
	{
		size_t st, end;
		if (trim_se(s, strlen(s), st, end))
		{
			memmove(s, s+st, end-st);
			s[end-st] = 0;
		}
		return s;
	}
}

namespace sutil
{
	unsigned int get_hash(const wchar_t* ps)
	{
		unsigned int hh = 0;
		for (int i=0; ps[i]; ++i)
		{
			hh = (hh<<13) | (hh>>19);
			hh += ps[i];
		}
		return hh;
	}
	unsigned int get_hash(const char* ps)
	{
		unsigned int hh = 0;
		for (int i=0; ps[i]; ++i)
		{
			hh = (hh<<13) | (hh>>19);
			hh += (unsigned char)ps[i];
		}
		return hh;
	}
	unsigned int get_hash_l(const wchar_t* ps)
	{
		unsigned int hh = 0;
		for (int i=0; ps[i]; ++i)
		{
			wchar_t ch = ps[i];
			if (ch>='A'&&ch<='Z') ch=ch-'A'+'a';
			hh = (hh<<13) | (hh>>19);
			hh += ch;
		}
		return hh;
	}
	unsigned int get_hash_l(const char* ps)
	{
		unsigned int hh = 0;
		for (int i=0; ps[i]; ++i)
		{
			unsigned char ch = ps[i];
			if (ch>='A'&&ch<='Z') ch=ch-'A'+'a';
			hh = (hh<<13) | (hh>>19);
			hh += ch;
		}
		return hh;
	}
	size_t wcslcat(wchar_t * dst, const wchar_t * src, size_t len)
	{
		size_t len1 = 0;
		while (*dst)
		{
			++ len1;
			++ dst;
			if (len1>=len)
				return len;
		}
		while (len1+1 < len && *src)
		{
			*dst = *src;
			++ dst;
			++ src;
			++ len1;
		}
		* dst = 0;
		return wcslen(dst) + wcslen(src);
	}

	size_t wcslcpy(wchar_t * dst, const wchar_t * src, size_t len)
	{
		if (!dst || len == 0) return wcslen(src);
		dst[0] = 0;
		return wcslcat(dst, src, len);
	}

	size_t strlcat(char * dst, const char * src, size_t len)
	{
		if (!dst || !src) return len;
		size_t len1 = 0;
		while (*dst)
		{
			++ len1;
			++ dst;
			if (len1>=len) return len;
		}
		while (len1+1 < len && *src)
		{
			*dst = *src;
			++ dst;
			++ src;
			++ len1;
		}
		if (len1 < len) * dst = 0;
		return strlen(dst)+strlen(src);
	}

	size_t strlcpy(char * dst, const char * src, size_t len)
	{
		if (!dst || len == 0) return len;
		dst[0] = 0;
		return strlcat(dst, src, len);
	}
}

namespace sutil
{
	bool match_wildcard(const char* pat, const char* str)
	{
		const char *s, *p;
		bool star = false;

loopStart:
		for (s = str, p = pat; *s; ++s, ++p)
		{
			switch (*p)
			{
			case '?':
				if (*s == '.') goto starCheck;
				break;
			case '*':
				star = true;
				str = s, pat = p;
				do { ++pat; } while (*pat == '*');
				if (!*pat) return true;
				goto loopStart;
			default:
				if (*s != *p)
					goto starCheck;
				break;
			} /* endswitch */
		} /* endfor */
		while (*p == '*') ++p;
		return (!*p);

starCheck:
		if (!star) return false;
		str++;
		goto loopStart;
	}

	void split_cmd_string(const char* str, vector<string> &vecStr)
	{
		BOOL bInQuotation = FALSE;
		int nBeginChar = 0;

		for (int i = 0; str[i]; )
		{
			if (str[i] == '\"')
			{
				if (!bInQuotation &&    // DEBUG: "arg1""arg2" 被解析成arg2，因""被优先于InQuotation处理
					str[i+1] == '\"')
				{
					i = i + 2;
					nBeginChar = i; // DEBUG: arg1 "" arg2 被解析成3参数，由于beginChar没有相应移位导致
					continue;
				}

				if (bInQuotation)
				{
					bInQuotation = FALSE;
					vecStr.push_back(string(str+nBeginChar, i - nBeginChar));
					nBeginChar  = i+1;
				}
				else
				{
					if (i==0 || str[i-1]==' ')
					{
						nBeginChar  = i + 1;
						bInQuotation= TRUE;
					}
				}
				++i;
			}
			else if (str[i] == ' ' || str[i] == '\t')
			{
				if (bInQuotation)
				{
					++i;
					continue;
				}

				if (nBeginChar < i)
				{
					vecStr.push_back(string(str+nBeginChar, i - nBeginChar));
				}
				nBeginChar = ++i;
			}
			else
			{
				++i;
			}
		}
		if (str[nBeginChar])
		{
			vecStr.push_back(str+nBeginChar);
		}
	}

	vector<string> split_str(crefstr ins, crefstr spl, int maxs)
	{
		vector<string> vr;
		if (spl.empty())
		{
			vr.push_back(ins);
			return vr;
		}

		for (size_t pos=0; ; )
		{
			size_t prepos = pos;
			pos = (maxs>1||maxs<0) ? ins.find(spl, prepos) : string::npos;
			if (pos == string::npos)
			{
				vr.push_back(ins.substr(prepos));
				break;
			}
			else
				vr.push_back(ins.substr(prepos, pos-prepos));
			pos += spl.length();
			if (maxs > 0) --maxs;
		}
		return vr;
	}
}
#ifndef __APPLE__
extern "C" size_t strlcat(char * dst, const char * src, size_t len)
{
	return sutil::strlcat(dst, src, len);
}

extern "C" size_t strlcpy(char * dst, const char * src, size_t len)
{
	return sutil::strlcpy(dst, src, len);
}
#endif
