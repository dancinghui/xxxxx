#pragma once

#ifdef __cplusplus

template<class T> inline void zero_object(T & obj)
{
	memset(&obj,0,sizeof(T));
}


__inline void zero_range(void * a, void *b, int adj)
{
	memset(a, 0, (char*)b+adj-(char*)a);
}

#endif


#ifndef _countof
# ifdef __cplusplus
template <size_t cnt> struct __countof_helper_st{ char dummy[cnt]; };
template <typename _CountofType, size_t _SizeOfArray>
__countof_helper_st<_SizeOfArray> __countof_helper(_CountofType (&_Array)[_SizeOfArray]);
# define _countof(_Array) sizeof(__countof_helper(_Array))
# else
# define _countof(x) (sizeof(x)/sizeof(x[0]))
# endif
#endif

