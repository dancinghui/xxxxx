#pragma once

class CBasicHtml
{
public:
	typedef vector<std::pair<string, string> > attrs_t;
	enum
	{
		EMPTY_TAG = 1,
		START_TAG = 2,
		END_TAG   = 4,
		STRING    = 8,
		COMMENT   = 16,
		OTHER     = 32,
	};
	
protected:
	const char* m_buf;
	size_t m_len;
	size_t m_ip;
	
public:
	CBasicHtml(const char * h, size_t len);
	~CBasicHtml();
	
	size_t getip() {return m_ip;}
	void setip(size_t ip) {m_ip = ip; if (m_ip>m_len) m_ip = m_len;}
	bool read_item(int & type, string & name, attrs_t * attrs = 0, size_t * ps = 0, size_t * pe = 0);
	static string und(const string & s0, bool bStripSpace);

protected:
	void Ana(string & s, int & type, string & name, attrs_t * attrs);
	void readw(const char * & s, string & name);
	virtual void read_parse(const char * & s, attrs_t * attrs);
};
