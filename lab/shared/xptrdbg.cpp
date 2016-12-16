#include "stdafx.h"

#ifndef DEBUG
#define DEBUG
#endif

#include "xptr.h"

namespace xptr
{
#if (defined(_DEBUG) || defined (DEBUG)) && (defined(_M_AMD64) || defined(__amd64__))
	shift_type_t packed_ptr::SHIFTV(3);
#endif
}
