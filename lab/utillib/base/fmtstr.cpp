#include "stdafx.h"
#include "fmtstr.h"

namespace UFmtStr
{
	string FmtStringV(LPCSTR fmt, va_list vl)
	{
		va_list vlc;
		va_copy(vlc, vl);
		int nc = _vscprintf(fmt, vlc)+2;
		va_end(vlc);
		string s;
		if (nc >= 0)
		{
			s.resize(nc);
			int len = _vsnprintf(&s[0], nc, fmt, vl);
			if (len>=0) s.resize(len);
			else s.resize(0);
		}
		return s;
	}

	wstring FmtStringV(LPCWSTR fmt, va_list vl)
	{
		va_list vlc;
		va_copy(vlc, vl);
		int nc = _vscwprintf(fmt, vlc)+2;
		va_end(vlc);
		wstring s;
		if (nc >= 0)
		{
			s.resize(nc);
			int len = _vsnwprintf(&s[0], nc, fmt, vl);
			if (len>=0) s.resize(len);
			else s.resize(0);
		}
		return s;
	}

	string FmtString(LPCSTR fmt, ...)
	{
		va_list vl;
		va_start(vl, fmt);
		string ss = FmtStringV(fmt, vl);
		va_end(vl);
		return ss;
	}

	wstring FmtString(LPCWSTR fmt, ...)
	{
		va_list vl;
		va_start(vl, fmt);
		wstring sw= FmtStringV(fmt, vl);
		va_end(vl);
		return sw;
	}

	template <class tstring>
	static void AddByVar(const tstring & var, UFmtStr::tagStringItem<tstring> & item, const UFmtStr::UParamBase<tstring> & up, tstring & str, int index)
	{
		tstring add = up.gets(var, index);
		str += add;
		item.str += add;
	}
#define CHANGE_STATE(cond, st, doit) if (cond){ state = st; doit; continue;}
#define ADDCH(ch) {m_str+=ch; cur.str += ch; }
#define ADDITEM(pro) if(cur.str.length()) {item.push_back(cur); cur.str.clear();}; cur.nProperty = pro;
	template <class tstring>
	tstring UFormatEx(const tstring& strFmt, std::vector<tagStringItem<tstring> > & item, const UParamBase<tstring> & up, size_t * fmtbase)
	{
		tagStringItem<tstring> cur;
		int nProperty = 0;
		tstring var;
		UINT len = (UINT)strFmt.length();
		tstring m_str;

		m_str.clear();
		m_str.reserve(len*2);
		cur.str.reserve(len);
		cur.nProperty = 0;

		size_t maxAte = 0, fmtBase_ = fmtbase ? *fmtbase : 0;
		int state = 0;
		for (UINT i=0; ; ++i)
		{
			typename mpstrtype<tstring>::chartype ch = strFmt[i];
			switch (state)
			{
			case 0:
				if (ch == 0)
				{
					//EOF.
					ADDITEM(0);
					if (fmtbase) *fmtbase += maxAte+1;
					return m_str;
				}
				CHANGE_STATE(     ch=='$', 1, (void)0);
				ADDCH(ch);
				continue;
			case 1:
				CHANGE_STATE(iswdigit(ch), 2, nProperty=ch-'0');
				CHANGE_STATE(iswalpha(ch)||ch=='_', 3, (var.clear(),var += ch));
				CHANGE_STATE(   ch == '$', 0, ADDCH(ch) );
				CHANGE_STATE(   ch == '>', 0, ADDITEM(0));
				break;
			case 2:
				CHANGE_STATE(iswdigit(ch), 2, nProperty=nProperty*10 + ch-'0');
				CHANGE_STATE(   ch == '<', 0, ADDITEM(nProperty));
				break;
			case 3:
				{
					CHANGE_STATE( (iswalnum(ch)||ch=='.'||ch=='_'), 3, var += ch);
					if (ch == '$')
					{
						size_t pos = var.find('.');
						size_t index = 0;
						if (pos != string::npos)
						{
							index = mpstrtype<tstring>::toi(var.substr(pos+1).c_str());
							var = var.substr(0, pos);
						}
						maxAte = (std::max)(maxAte, index);
						CHANGE_STATE(   ch == '$', 0, AddByVar(var, cur, up, m_str, (int)(fmtBase_+index) ));
					}
				}
				break;
			default:
				__assume(0);
				MYASSERT(FALSE);
				break;
			}
			MYASSERT(! "??那??‘∩?車D∩赤?車㏒?2?﹞?o?辰a?車㏒????足2谷㏒?");
		}
		if (fmtbase) *fmtbase += maxAte+1;
		return m_str;
	}

	void intro_ufmt()
	{
		if (1)
		{
			wstring ws;
			vector<tagStringItem<wstring> > oo;
			UParam<wstring> up;
			up.Add(L"aa", 1);
			up.Add(L"bb", L"dd");
			UFormatEx(ws, oo, up, 0);
		}
		if (1)
		{
			string ws;
			vector<tagStringItem<string> > oo;
			UParam<string> up;
			up.Add("aa", 1);
			up.Add("bb", "dd");
			UFormatEx(ws, oo, up, 0);
		}
	}
}
