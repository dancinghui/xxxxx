#ifdef _WIN32

#define _WIN32_WINNT 0x0600
#define NOMINMAX
#include <SDKDDKVer.h>
#include <tchar.h>
#include <WinSock2.h>
#include <WS2tcpip.h>
#include <Windows.h>
#include <process.h>
#include <intrin.h>
#include <time.h>
#include <stdint.h>

#ifndef va_copy
#define va_copy(a, b) a=b
#endif

#else //non-win32

#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wchar.h>
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>
#include <stddef.h>

#endif //win32_or_not

#ifdef __cplusplus
#include <utility>
#include <vector>
#include <algorithm>
#include <string>
#include <map>
#include <deque>
#include <sstream>
#include <set>
#include <list>
#include <functional>

using std::string;
using std::vector;
using std::map;
using std::deque;
using std::wstring;
using std::set;

typedef const std::string & crefstr;
#endif

#include "cptfuncs.h"
#include "basicrt.h"

#ifdef _MSC_VER
#pragma warning(error:4715)
#pragma warning(disable:4068)

__inline int my_isspace(int c){ return isspace((c <= -1 && c >= -128) ? (int)(unsigned char)c : c); }
__inline int my_isalpha(int c){ return isalpha((c <= -1 && c >= -128) ? (int)(unsigned char)c : c); }
__inline int my_isalnum(int c){ return isalnum((c <= -1 && c >= -128) ? (int)(unsigned char)c : c); }
__inline int my_isprint(int c){ return isprint((c <= -1 && c >= -128) ? (int)(unsigned char)c : c); }
#define isspace(x) my_isspace(x)
#define isalpha(x) my_isalpha(x)
#define isalnum(x) my_isalnum(x)
#define isprint(x) my_isprint(x)
#endif
