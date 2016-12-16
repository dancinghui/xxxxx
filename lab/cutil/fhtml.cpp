#include "stdafx.h"
#include "base/HelperFuncs.h"
#include "fileformat/basichtml.h"
#include <openssl/md5.h>
#include "fhtml.h"

CFindHtml::CFindHtml(const char *p, size_t len)
{
	m_html = p;
	m_htmle = p + len;
	m_ptr = p;
	m_text = 0;
	m_node = 0;
}

void CFindHtml::hook(string * node, string * text)
{
	m_node = node;
	m_text = text;
}

void CFindHtml::set_ip(intptr_t ip)
{
	m_ptr = m_html + ip;
	if (m_ptr < m_html) m_ptr = m_html;
	if (m_ptr > m_htmle) m_ptr = m_htmle;
}

bool CFindHtml::find_head(const char * ss, int which)
{
	const char * p;
	if (!m_ptr) return false;
	if (ss && *ss)
		p = strstr(m_ptr, ss);
	else
		p = m_ptr;
	if (!p) return (m_ptr = NULL), false;

	if (which <= 0)
	{
		for (;;)
		{
			while (p[0] != '<')
			{
				--p;
				if (p < m_html)
					return (m_ptr = NULL), false;
			}
			if (which++ == 0)
				break;
			--p;
		}
	}
	else
	{
		++p;
		for (;;)
		{
			while (p[0] != '<')
			{
				++p;
				if (p >= m_htmle)
					return (m_ptr = NULL), false;
			}
			if (--which == 0)
				break;
			--p;
		}
	}
	return (m_ptr = p), true;
}

size_t CFindHtml::execute()
{
	CBasicHtml bh(m_html, m_htmle - m_html);
	bh.setip(m_ptr - m_html);
	int type = 0;
	string name;

	vector<string> tags;
	size_t ns, ne;
	for (;;)
	{
		size_t curip = bh.getip();
		if (! bh.read_item(type, name, 0, &ns, &ne) ) break;
		on_find(type, name, ns, ne);
		if (type == CBasicHtml::START_TAG)
		{
			tags.push_back(name);
		}
		else if (type == CBasicHtml::END_TAG)
		{
			if (tags.empty()) //the first node is </div>
			{
				//ERROR
				on_mismatch(curip, name.c_str());
				break;
			}

			if (tags[tags.size() - 1] != name)
			{
				//ERROR!!.
				on_mismatch(curip, name.c_str());
				for (size_t i = 2; i < 4; ++i)
				{
					if (tags.size() >= i && tags[tags.size() - i] == name)
					{
						for (size_t j = 0; j < i; ++j)
							tags.pop_back();
						break;
					}
				}
				if (tags.empty())
				{
					//ERROR!
					break;
				}
			}
			else
			{
				tags.pop_back();
				if (tags.empty())
				{
					break;
				}
			}
		}
		else
		{
			if (tags.empty())
			{
				break;
			}
		}
	}
	//fprintf(stdout, "###%.*s###\n", (int)(m_html + endip - m_ptr), m_ptr);
	return bh.getip();
}

void CFindHtml::find_line(unsigned int pos, unsigned int &line, unsigned int &col)
{
	if (pos > m_htmle-m_html) pos = (unsigned int) (m_htmle-m_html);
	line = 1;
	unsigned int lastlinep = 0;
	for (unsigned int i=0; i<pos; ++i)
	{
		if (m_html[i] == '\n')
		{
			++line;
			lastlinep = i+1;
		}
	}
	col = pos - lastlinep + 1;
}

void CFindHtml::on_find(int type, crefstr name, size_t ns, size_t ne)
{
	if (m_node)
		m_node->append(m_html + ns, ne - ns);
	if (m_text && m_html[ns] != '<')
		m_text->append(CBasicHtml::und(name, false));
}


CFindForm::CFindForm(const char* p, size_t len) : CFindHtml(p, len)
{
}
void CFindForm::on_find(int type, crefstr name, size_t ns, size_t ne)
{
	if (type != CBasicHtml::START_TAG && type != CBasicHtml::EMPTY_TAG)
		return;
	if (_stricmp(name.c_str(), "input") != 0)
		return;

	string name_, type_, value_;
	auto on_nv = [&](crefstr name, crefstr value){
		if (_stricmp(name.c_str(), "type") == 0)
			type_ = value;
		else if (_stricmp(name.c_str(), "name") == 0)
			name_ = value;
		else if (_stricmp(name.c_str(), "value") == 0)
			value_ = value;
	};

	const char * ps = m_html + ns;
	const char * pe = m_html + ne;
	const char *p;

	while (ps < pe && !isspace(*ps)) ++ps;
	for (;;)
	{
		if (ps >= pe) break;
		while (ps < pe && isspace(*ps)) ++ps;
		for (p = ps; p < pe && *p != '=' && !isspace(*p); ++p){}
		//[ps, p) is name.
		if (p >= pe)break;
		if (isspace(*p))continue;

		string name(ps, p - ps);
		ps = ++p;
		while (ps < pe && isspace(*ps)) ++ps;
		p = ps;
		if (*p == '\'' || *p == '"')
		{
			char oldc = *p++;
			ps = p;
			while (p < pe && *p != oldc) ++p;
			if (p >= pe) return;
			string value(ps, p - ps);
			++p;
			ps = p;
			on_nv(name, value);
		}
		else
		{
			while (p < pe && !isspace(*p)) ++p;
			string value(ps, p - ps);
			on_nv(name, value);
		}
	}
	if (!name_.empty())
	{
		if (_stricmp(type_.c_str(), "submit") == 0)
			m_submit[name_] = value_;
		else
			m_kvs[name_] = value_;
	}
}

void * CFindHtmlFuncs::get_html_node(const char * html, int len, int place, int which)
{
	if (place >= len)
		return on_error(__LINE__, "invalid place"), nullptr;
	CFindHtml fh(html, len);
	fh.set_ip(place);
	if (fh.find_head(0, which))
	{
		string node;
		fh.hook(&node, 0);
		if (fh.execute())
			return build_s(node.c_str(), node.length());
	}
	return on_error(__LINE__, "invalid html"), nullptr;
}
void * CFindHtmlFuncs::get_html_text(const char * html, int len, int place, int which)
{
	return get_html_text_(html, len, place, which, false);
}
void * CFindHtmlFuncs::get_html_text_hash(const char * html, int len, int place, int which)
{
	return get_html_text_(html, len, place, which, true);
}

void * CFindHtmlFuncs::get_html_text_(const char * html, int len, int place, int which, bool hash)
{
	if (place >= len)
		return on_error(__LINE__, "invalid place"), nullptr;
	CFindHtml fh(html, len);
	fh.set_ip(place);
	if (fh.find_head(0, which))
	{
		string text;
		fh.hook(0, &text);
		if (fh.execute())
		{
			//strip text.
			const char * ptr = text.c_str();
			size_t len = text.length();
			while (len > 0 && isspace(*ptr))
			{
				++ptr;
				--len;
			}
			while (len > 0 && isspace(ptr[len - 1]))
			{
				--len;
			}
			if (hash)
			{
				const char * tbl = "0123456789abcdef";
				unsigned char md[16];
				MD5_CTX ctx;
				MD5_Init(&ctx);
				MD5_Update(&ctx, ptr, len);
				MD5_Final(md, &ctx);
				char retstr[32 + 8];
				for (unsigned int i = 0; i < sizeof(md); ++i)
				{
					retstr[i * 2 + 0] = tbl[md[i] >> 4];
					retstr[i * 2 + 1] = tbl[md[i] & 15];
				}
				return build_s(retstr, 2 * sizeof(md));
			}
			else
				return build_s(ptr, len);
		}
	}
	return on_error(__LINE__, "invalid html"), nullptr;
}

void * CFindHtmlFuncs::process_form(const char * html, int len, int place, int which)
{
	if (place >= len)
		return on_error(__LINE__, "invalid place"), nullptr;
	CFindForm fh(html, len);
	fh.set_ip(place);
	if (fh.find_head(0, which) && fh.execute())
	{
		return fh.pyobj();
	}
	return on_error(__LINE__, "invalid html"), nullptr;
}

class CFindHtml1 : public CFindHtml
{
public:
	size_t error;
	size_t invalidpos;
	string invalidname;

	CFindHtml1(const char * p, int len) : CFindHtml(p, len)
	{
		error = 0;
		invalidpos = -1;
	}

	virtual void on_mismatch(size_t pos, const char * name)
	{
		if (error) return;
		error = 1;
		invalidpos = pos;
		invalidname = name;
	}
};

bool CFindHtmlFuncs::check_html(const char * html, int len)
{
	CFindHtml1 fh(html, len);
	fh.set_ip(0);
	size_t x = fh.execute();
	if (! fh.error)
	{
		if (x != len)
		{
			while (x<len && isspace(html[x])) ++ x;
			if (x!=len)
			{
				fh.error = 1;
				fh.invalidpos = x;
			}
		}
	}
	if (fh.error)
	{
		unsigned int pos = (unsigned int) fh.invalidpos;
		unsigned int line, col;
		fh.find_line(pos, line, col);
		char error[300];
		sprintf(error, "mismatch at pos,line,col:(%u,%u,%u)", pos, line, col);
		on_error(-1, error);
		return false;
	}
	return true;
}
