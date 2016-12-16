#pragma once

#ifdef _WIN32
#define PRINTF_FORMAT_CHECK(a,b)
#else
#define PRINTF_FORMAT_CHECK(format_index, args_index) __attribute__((__format__(printf, format_index, args_index)))
#endif

namespace UFmtStr
{
	template <class T> struct mpstrtype;
	template <>
	struct mpstrtype<string>
	{
		typedef std::stringstream s_stream;
		typedef char chartype;
		static int toi(const char * p){return atoi(p);}
	};
	template <>
	struct mpstrtype<wstring>
	{
		typedef std::wstringstream s_stream;
		typedef wchar_t chartype;
		static int toi(const wchar_t * p){return _wtoi(p);}
	};

	template <class tstring>
	struct tagStringItem
	{
		tstring str;
		int nProperty;
	};

	template <class tstring>
	class UParamBase
	{
	public:
		virtual tstring gets(const tstring& var, size_t index) const = 0;
	};

	template <class tstring>
	class UParam : public UParamBase<tstring>
	{
	public:
		template <class TT>
		static tstring getsv(TT value)
		{
			typename mpstrtype<tstring>::s_stream ss;
			ss << value;
			return ss.str();
		}
		static const tstring& getsv(const tstring& value)
		{
			return value;
		}

	public:
		std::map<tstring, tstring> mvv;

		tstring gets(const tstring & var, size_t) const
		{
			typename std::map<tstring, tstring>::const_iterator p = mvv.find(var);
			if (p!=mvv.end()) return p->second;
			MYASSERT(FALSE);
			return tstring();
		}

		template<class TT>
		UParam & Add(const tstring& name, TT value)
		{
			mvv[name]= getsv(value);
			return *this;
		}
		template<class TT>
		UParam & operator () (LPCTSTR name, TT value)
		{
			return Add(name, value);
		}
		UParam & operator() (void)
		{
			mvv.clear();
			return *this;
		}
		
		template<class TT>
		UParam(LPCTSTR name, TT value)
		{
			Add(name, value);
		}
		UParam(){}
	};

	template <class tstring , class TT>
	static UParam<tstring> p(const tstring name, TT value)
	{
		UParam<tstring> up;
		return up(name, value);
	}

	template <class tstring>
	tstring UFormatEx(const tstring& strFmt, std::vector<tagStringItem<tstring> > & item, 
		const UParamBase<tstring> & up, size_t * fmtbase);
	template <class tstring>
	inline tstring UFormat(const tstring& fmt, const UParamBase<tstring> & up, size_t * fmtbase = 0)
	{
		std::vector<tagStringItem<tstring> > item;
		return UFormatEx(fmt, item, up, fmtbase);
	}

	std::string FmtString(LPCSTR fmt, ...) PRINTF_FORMAT_CHECK(1,2);
	std::wstring FmtString(LPCWSTR fmt, ...);
	std::string FmtStringV(LPCSTR fmt, va_list vg);
	std::wstring FmtStringV(LPCWSTR fmt, va_list vg);
}
