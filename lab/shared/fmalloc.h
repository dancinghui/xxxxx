#pragma once
#include "base/lock.h"
#include "xptr.h"
#include "sharedfm.h"


namespace fmallocns
{
	const uint64_t file_head_sig = 0x454c49464d454d46ll;
	const unsigned int file_version = 0x10001;
	struct file_st;
	struct RBItemAlloc;
}

class CFMalloc : public CSharedFilemap
{
private:
	size_t m_needspace;
	
public:
	static size_t to_page(size_t sz)
	{
		sz += PAGE_SIZE-1;
		sz &= ~(size_t)(PAGE_SIZE-1);
		return sz;
	}

	CFMalloc();
	~CFMalloc();
public:
	bool init(const char * fn);

	xptr::packed_ptr do_alloc(size_t sz);
	void do_free(xptr::packed_ptr ptr);
	size_t do_getsize(xptr::packed_ptr ptr);
	void do_free(void * ptr);
	template <class T>
	T * get_app_space()
	{
		static_assert(__is_pod(T), "must be POD");
		static_assert(sizeof(T) <= 512*6, "too large.");
		return (T*)get_app_space_();
	}

	xptr::baseaddr_t base()
	{
		return (xptr::baseaddr_t) m_fileptr;
	}
private:
	void * do_inner_alloc(size_t sz);
	void * do_page_alloc(size_t sz);
	void * do_page_alloc_withrb(size_t sz);
	fmallocns::RBItemAlloc * alloc_rbitem();

protected:
	fmallocns::file_st * file(){ return (fmallocns::file_st*)m_fileptr; }
	bool set_rb(void * mem, size_t sz, size_t diff);
	void * get_app_space_();
	static size_t compute_alloc_size(size_t sz0);
	static size_t compute_alloc_tail(size_t sz);
	static int alloc_size_to_index(size_t from);
};
