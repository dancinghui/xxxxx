#include "stdafx.h"
#include "basichtml.h"

CBasicHtml::CBasicHtml(const char *h, size_t len)
{
	m_buf = h;
	m_len = len;
	if (m_len > 3 && m_buf[0] == '\xEF'
		&& m_buf[1] == '\xBB'
		&& m_buf[2] == '\xBF')
	{
		m_len -= 3;
		m_buf += 3;
	}
	m_ip = 0;
}

CBasicHtml::~CBasicHtml()
{
}

bool CBasicHtml::read_item(int & type, string & name, attrs_t * attrs, size_t * ps, size_t * pe)
{
	if (ps) *ps = m_ip;
	size_t oldip = m_ip;
	
	string sxx;
	if (m_buf[m_ip] == '<')
	{
		++ m_ip;
		if (isalpha(m_buf[m_ip]) || m_buf[m_ip]=='?' || m_buf[m_ip]=='!' || m_buf[m_ip]=='/')
		{
			if (m_buf[m_ip] == '!' && m_buf[m_ip+1]=='-' && m_buf[m_ip+2]=='-')
			{
				m_ip+=3;
				const char * f = (strstr(m_buf+m_ip, "-->"));
				if (f)
				{
					m_ip = f + 3 - m_buf;
					sxx = string(m_buf+oldip+1, m_ip-oldip-2);
				}
				else
				{
					m_ip = m_len;
					sxx = m_buf+oldip+1;
				}
			}
			else
			{
				char ch;
				while ((ch=m_buf[m_ip++]) != '>')
				{
					if (ch == 0) return false;
					sxx += ch;
				}
			}
			Ana(sxx, type, name, attrs);
			if (pe) *pe = m_ip;
			return true;
			//ok processed the tag.
		}
	}
	
	m_ip = oldip;
	if (m_buf[m_ip] == 0)
	{
		return false;
	}
	else
	{
		for (;;)
		{
			char ch = m_buf[m_ip];
			if (ch == 0) return false;
			if (ch == '<')
			{
				char ch2 = m_buf[m_ip+1];
				if (isalpha(ch2) || ch2=='?' || ch2=='!' || ch2=='/') break;
			}
			sxx += ch;
			m_ip++;
		}
		
		name = sxx;
		type = STRING;
		if (pe) *pe = m_ip;
		return true;
	}
}

void CBasicHtml::Ana(string & s, int & type, string & name, attrs_t * attrs)
{
	if (s.length() == 0)
	{
		name = "";
		type = OTHER;
	}
	else if (s[0] == '!')
	{
		if (s[1] == '-' && s[2] == '-')
		{
			name = s.substr(3, (std::max)((int)s.length(), 5) - 5);
			type = COMMENT;
		}
		else
		{
			type = OTHER;
			name = s.substr(1, (std::max)((int)s.length(), 1) - 1);
		}
	}
	else if (s[0] == '/')
	{
		const char * ss = s.c_str()+1;
		readw(ss, name);
		type = END_TAG;
	}
	else if (s[s.length() - 1] == '/')
	{
		s.resize(s.length()-1);
		type = EMPTY_TAG;
		
		const char * ss = s.c_str();
		readw(ss, name);
		while(*ss) read_parse (ss, attrs);
	}
	else
	{
		type = START_TAG;
		const char * ss = s.c_str();
		readw(ss, name);
		//    area, base, br, col, embed, hr, img, input, keygen, link, menuitem, meta, param, source, track, wbr
		static const char * voidtags[] = {
			"area", "base", "br", "col", "embed", "hr", "img", "input",
			"keygen", "link", "menuitem", "meta", "param", "source", "track", "wbr",
			NULL
		};
		for (int i=0; voidtags[i]; ++i)
		{
			if (_stricmp(name.c_str(), voidtags[i])==0)
				type = EMPTY_TAG;
		}
		while(*ss) read_parse (ss, attrs);
	}
}

void CBasicHtml::readw(const char * & s, string & name)
{
	string n;
	while (*s && isspace(*s))
	{
		++s;
	}
	while (*s && !isspace(*s))
	{
		n += *s++;
	}
	name = n;
	while (*s && isspace(*s))
	{
		++s;
	}
}

void CBasicHtml::read_parse(const char * & s, attrs_t * attrs)
{
	while (*s) ++s;
}

template <class I, class F>
bool every_is(I beg, I end, F f)
{
	bool r = true;
	for (I t = beg; t != end; ++t)
	{
		r = r && f(*t);
	}
	return r;
}

static bool to_utf8(long ch, char * b)
{
	if (ch < 0) return false;
	if (ch < 0x80 && ch!=0) *b++ = (char) ch;
	else if (ch <= 0x3ff)
	{
		*b++ = 0xc0 | (char)(ch >> 6);
		*b++ = 0x80 | (ch & 0x3f);
	}
	else if (ch<=0xffff)
	{
		*b++ = 0xe0 | (char)(ch >> 12);
		*b++ = 0x80 | ((ch >> 6) & 0x3f);
		*b++ = 0x80 | (ch & 0x3f);
	}
	else if (ch <= 0x1ffff)
	{
		// 	11110xxx 	10xxxxxx 	10xxxxxx 	10xxxxxx
		*b++ = 0xf0 | (char)(ch >> 18);
		*b++ = 0x80 | ((ch >> 12) & 0x3f);
		*b++ = 0x80 | ((ch >> 6) & 0x3f);
		*b++ = 0x80 | ((ch >> 0) & 0x3f);
	}
	else
		return false; //assume not so large...
	*b++ = 0;
	return true;
}

string CBasicHtml::und(const string & s0, bool bStripSpace)
{
	string r, s = s0;
	if (bStripSpace)
	{
		s.resize(0);
		size_t i, nn = s0.length(), x = nn;
		for (i = 0; i<nn; ++i)
		{
			char ch = s0[i];
			if (ch == ' ' || ch == '\t')
			{

			}
			else if (ch == '\n' || ch == '\r')
			{
				x = nn;
			}
			else
			{
				for (size_t j = x; j<i; ++j)
				{
					s += s0[j];
				}
				x = i + 1;
				s += ch;
			}
		}
	}
	for (size_t i = 0, nn = s.length(); i<nn; ++i)
	{
		char ch = s[i];
		if (ch == '&' && i + 1 < nn)
		{
			size_t i2 = i + 1;
			char tmp[9] = { 0 };
			while (i2 < nn && i2 < i + 7)
			{
				if (s[i2] == ';') break;
				tmp[i2 - i - 1] = s[i2];
				i2++;
			}

			if (s[i2] == ';')
			{
				bool o = true;
				if (strcmp(tmp, "nbsp") == 0) r += "\xc2\xa0"; //utf-8 form of \xa0.
				else if (strcmp(tmp, "lt") == 0) r += "<";
				else if (strcmp(tmp, "gt") == 0) r += ">";
				else if (strcmp(tmp, "quot") == 0) r += "\"";
				else if (strcmp(tmp, "amp") == 0) r += "&";
				else if (tmp[0] == '#' && tmp[1] && every_is(tmp+1, tmp+strlen(tmp), isdigit))
				{
					char ooo[12];
					if (to_utf8(atoi(tmp+1), ooo)) r += ooo;
					else o = false;
				}
				else if (tmp[0] == '#' && (tmp[1]|0x20) == 'x' && tmp[2] && every_is(tmp+2, tmp + strlen(tmp), isxdigit))
				{
					char ooo[12];
					long lv = strtol(tmp+2, 0, 16);
					if (to_utf8(lv, ooo)) r += ooo;
					else o = false;
				}
				else o = false;
				if (o)
				{
					i = i2;
					continue;
				}
			}
		}
		r += ch;
	}
	return r;
}
