#pragma once

class CFindHtml
{
protected:
	const char * m_html, *m_htmle;
	const char * m_ptr;
	string * m_text;
	string * m_node;
public:
	CFindHtml(const char *p, size_t len);
	void hook(string * node, string * text);
	void set_ip(intptr_t ip);
	bool find_head(const char * ss, int which);
	size_t execute();
	void find_line(unsigned int pos, unsigned int & line, unsigned int & col);
protected:
	virtual void on_find(int type, crefstr name, size_t ns, size_t ne);
	virtual void on_mismatch(size_t ip, const char * name){}
};

class CFindForm: public CFindHtml
{
protected:
	map<string, string> m_kvs, m_submit;
public:
	CFindForm(const char* p, size_t len);
	void * pyobj();
protected:
	void on_find(int type, crefstr name, size_t ns, size_t ne);
};

class CFindHtmlFuncs
{
protected:
	virtual ~CFindHtmlFuncs(){}
	virtual void * build_s(const char * s, size_t len) = 0;
	virtual void on_error(int code, const char * err) = 0;

public:
	void * get_html_node(const char * html, int len, int place, int which);
	void * get_html_text(const char * html, int len, int place, int which);
	void * get_html_text_hash(const char * html, int len, int place, int which);
	void * process_form(const char * html, int len, int place, int which);
	bool check_html(const char * html, int len);
protected:
	void * get_html_text_(const char * html, int len, int place, int which, bool hash);
};
