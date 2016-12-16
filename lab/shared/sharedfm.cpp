#include "stdafx.h"
#include "sharedfm.h"

#ifndef _WIN32
#include <fcntl.h>
#include <sys/mman.h>
#endif

#ifdef __APPLE__
int fallocate(int fd, int mode, size_t beg, size_t cnt);
int fallocate(int fd, int mode, size_t beg, size_t cnt)
{
	size_t fsz = beg + cnt;
	fstore_t store = { F_ALLOCATECONTIG, F_PEOFPOSMODE, 0, (off_t)fsz };
	// Try to get a continous chunk of disk space
	int ret = fcntl(fd, F_PREALLOCATE, &store);
	if (ret < 0)
	{
		// OK, perhaps we are too fragmented, allocate non-continuous
		store.fst_flags = F_ALLOCATEALL;
		ret = fcntl(fd, F_PREALLOCATE, &store);
		if (ret < 0)
			return ret;
	}
	return ftruncate(fd, fsz);
}
#endif

#define BUG() do{*(int*)__LINE__ = 0;} while(0)

using namespace xptr;

uint64_t CSharedFilemap::Config::maxfilesz()
{
	return sizeof(void*) == 4 ?
		(uint64_t)(0x60000000llu) :
		(uint64_t)((0x100000000llu << packed_ptr::SHIFTV) - 1024 * 1024);
}

uint32_t CSharedFilemap::Config::initsz()
{
	return 1024 * 1024;
}

static CSharedFilemap::Config g_sample_cfg;

CSharedFilemap::Config* CSharedFilemap::Config::get_sample_config()
{
	return &g_sample_cfg;
}

CSharedFilemap::CSharedFilemap(Config * cfg):m_cfg(cfg)
{
	memset(m_fn, 0, sizeof(m_fn));
	m_handler = -1;
	m_mmhandler = 0;
	m_mapsz = 0;
	m_fileptr = 0;
}

CSharedFilemap::~CSharedFilemap()
{
#ifdef _WIN32
	UnmapViewOfFile(m_fileptr);
	CloseHandle((HANDLE)m_mmhandler);
	CloseHandle((HANDLE)m_handler);
#else
	munmap(m_fileptr, m_mapsz);
	close((int)m_handler);
#endif
}

bool CSharedFilemap::init(const char * fn)
{
	if (strlen(fn) > 500) return false;
	strcpy(m_fn, fn);

	uint64_t initsz = m_cfg->initsz();
	const uint64_t maxfilesz = m_cfg->maxfilesz();

	void * m = 0;
#ifdef _WIN32
	HANDLE hf = CreateFileA(fn, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS, 0, 0);
	if (hf == INVALID_HANDLE_VALUE)
		return false;
	LARGE_INTEGER fsz = { 0 };
	GetFileSizeEx(hf, &fsz);
	if (sizeof(void*) == 4 && fsz.QuadPart >= 0x80000000)
		return CloseHandle(hf), false;
	if (initsz < (size_t)fsz.QuadPart)
	{
		initsz = fsz.QuadPart;
		initsz -= initsz % (1024 * 1024);
	}
	if (initsz >= maxfilesz) initsz = maxfilesz;
	HANDLE hf1 = CreateFileMapping(hf, NULL, PAGE_READWRITE, (uint32_t)(initsz >> 32), (uint32_t)initsz, NULL);
	m = MapViewOfFile(hf1, FILE_MAP_READ | FILE_MAP_WRITE, 0, 0, initsz);
	m_handler = (intptr_t)hf;
	m_mmhandler = (intptr_t)hf1;
#else
	int fin = open(fn, O_RDWR | O_CREAT
#  ifdef O_LARGEFILE
		| O_LARGEFILE
#  endif
		, 0644);
	struct stat st;
	if (fin >= 0 && fstat(fin, &st) >= 0)
	{
		if (initsz < st.st_size)
			initsz = st.st_size;
		initsz -= initsz % (1024 * 1024);
		if (initsz > maxfilesz) initsz = maxfilesz;
		if (initsz > st.st_size)
		{
			if (fallocate(fin, 0, st.st_size, initsz - st.st_size) != 0)
			{
				close(fin);
				return false;
			}
		}
		m = mmap(NULL, initsz, PROT_WRITE, MAP_SHARED, fin, 0);
	}
	m_handler = fin;
	m_mmhandler = -1;
#endif
	m_mapsz = initsz;
	m_fileptr = (SFHeader*)m;
	return true;
}

void CSharedFilemap::RLock()
{
	CSimpRWLock * rwlock = CSimpRWLock::from(&m_fileptr->rwlock_file);
	lock.RLock();
	rwlock->RLock();

	size_t sz = m_fileptr->lastspace.endptr.value_;
	sz = sz << packed_ptr::SHIFTV;
	if (sz != m_mapsz)
	{
		rwlock->RUnlock();
		lock.RUnlock();
		do_resize_file(0);
		return RLock();
	}
}

void CSharedFilemap::RUnlock()
{
	CSimpRWLock * rwlock = CSimpRWLock::from(&m_fileptr->rwlock_file);
	rwlock->RUnlock();
	lock.RUnlock();
}

bool CSharedFilemap::do_resize_file(size_t incsz)
{
	const uint64_t maxfilesz = m_cfg->maxfilesz();

	CRWLock::AutoWLock file_expand(this->lock);
	CSimpRWLock * rwl = CSimpRWLock::from(&m_fileptr->rwlock_file);
	printf("%p -> %x\n", rwl, *(int*)rwl);
	rwl->WLock();

	uint64_t loldsz = ((uint64_t)m_fileptr->lastspace.endptr.value_ << packed_ptr::SHIFTV), lnewsz;
	if (loldsz != m_mapsz)
	{
		incsz = 0;
		lnewsz = loldsz;
	}
	else
	{
		//now m_map == loldsz
		lnewsz = loldsz + incsz;
		if (lnewsz == loldsz)
		{
			//nothing to do.
			rwl->WUnlock();
			return false;
		}
	}

	if (lnewsz > maxfilesz)
	{
		//file too large. we support at most 32G.
		rwl->WUnlock();
		return false;
	}

#ifdef _WIN32
	if (m_handler == (uintptr_t)-1)
	{
		rwl->WUnlock();
		BUG();
		return false;
	}

	UnmapViewOfFile(m_fileptr);
	CloseHandle((HANDLE)m_mmhandler);

	HANDLE hf1 = CreateFileMapping((HANDLE)m_handler, NULL, PAGE_READWRITE, (uint32_t)(lnewsz >> 32), (uint32_t)lnewsz, NULL);
	if (!hf1) goto fatal_error1;
	void * m = MapViewOfFile(hf1, FILE_MAP_READ | FILE_MAP_WRITE, 0, 0, (size_t)lnewsz);
	if (!m) goto fatal_error1;
	m_mmhandler = (intptr_t)hf1;
	m_fileptr = (SFHeader*)m;
	m_fileptr->lastspace.endptr.value_ = (unsigned int)(lnewsz >> packed_ptr::SHIFTV);
	m_mapsz = lnewsz;
	rwl = CSimpRWLock::from(&m_fileptr->rwlock_file);
	rwl->WUnlock();
	return !!m_fileptr;

fatal_error1:
	if (hf1)
	{
		m = MapViewOfFile(hf1, FILE_MAP_READ | FILE_MAP_WRITE, 0, 0, PAGE_SIZE);
		if (m)
		{
			rwl = CSimpRWLock::from(&((SFHeader*)m)->rwlock_file);
			rwl->WUnlock();
		}
	}
#else
	munmap(m_fileptr, m_mapsz);
	if (loldsz != lnewsz)
	{
		if (fallocate((int)m_handler, 0, m_mapsz, incsz) != 0)
		{
			m_fileptr = 0;
			goto fatal_error;
		}
	}
	m_fileptr = (SFHeader*)mmap(NULL, lnewsz, PROT_WRITE, MAP_SHARED, (int)m_handler, 0);
	if (m_fileptr == 0)
		goto fatal_error;
	m_mapsz = lnewsz;
	m_fileptr->lastspace.endptr.value_ = (unsigned int)(m_mapsz >> packed_ptr::SHIFTV);
	rwl = CSimpRWLock::from(&m_fileptr->rwlock_file);
	rwl->WUnlock();
	return !!m_fileptr;

fatal_error:
	m_fileptr = (SFHeader*)mmap(NULL, PAGE_SIZE, PROT_WRITE, MAP_SHARED, (int)m_handler, 0);
	if (m_fileptr)
	{
		rwl = CSimpRWLock::from(&m_fileptr->rwlock_file);
		rwl->WUnlock();
		munmap(m_fileptr, PAGE_SIZE);
		m_fileptr = 0;
	}
#endif
	fprintf(stderr, "fatal error: unable to remap file\n");
	BUG();
	abort();
	return false;
}

