#include "stdafx.h"
#include "base/atomic.h"
#include "fmalloc.h"
#include "xptr.h"
#include "xptrrb.h"

#define BUG() do{*(int*)__LINE__ = 0;} while(0)

using namespace xptr;

#define is_paged(sz) ((sz & (PAGE_SIZE-1)) == 0)

namespace fmallocns
{
	struct span{
		double_list lst;
		packed_ptr startptr;
		packed_ptr endptr;
	};

	struct RBItemAlloc : RBItem
	{
		enum { IS_PAGED_ALLOC = 0x8 };
		packed_ptr memptr;
		unsigned short headersize; //12bits used, <=0c00
		unsigned short sizediff; //12bits used, <=fff
		unsigned int othersize;
		unsigned int reserved;

		size_t get_allsz()
		{
			size_t asz = othersize + headersize;
			return asz < PAGE_SIZE ? PAGE_SIZE : asz;
		}
	};
	static_assert(sizeof(RBItemAlloc) == 32, "");

	struct CRBTreeAlloc
	{
		packed_ptr m_root;
		volatile int rwlock;

		RBItemAlloc * Delete(void * mem, baseaddr_t ba);
		bool Find(void * mem, RBItemAlloc & ra, baseaddr_t ba);
		bool Insert(RBItemAlloc * item, baseaddr_t ba);
	};
	struct rballoc_page {
		enum { NITEM = 128 };
		char data[NITEM][32];
	};

	struct file_head_base{
		int64_t sig;
		int version;
		int rwlock_file;
		space_span lastspace; //many empty pages at last

		single_list nonpaged_allocs[72];
		single_list rbitems;
		single_list center_pages[31]; //1page,2page,...31page
		double_list_lk center_npage; //span list. npage需要在中间插入。所以必须是double list带锁。..
		CRBTreeAlloc allocmap;  //ptr=> {size}
		//bytes: 16 + 8 + 72*4 + 32*4 + 16 + 8
	};
	struct file_head : file_head_base{
		char reserved[512 * 2 - sizeof(file_head_base)];
		char appspace[512 * 6];

		void first_init()
		{
			baseaddr_t baseaddr = (baseaddr_t) this;
			center_npage.base.first_init(baseaddr);
			sig = file_head_sig;
			version = file_version;
		}
	};

	struct file_st{
		file_head head;
		rballoc_page rbp[31];

		void checked_init(size_t initsz)
		{
			baseaddr_t baseaddr = (baseaddr_t) this;

			if (head.sig != file_head_sig || head.version != file_version)
			{
				memset(this, 0, sizeof(*this));
				CSimpRWLock * p = CSimpRWLock::from(&head.rwlock_file);
				CSimpRWLock::AutoWLock _(*p);

				head.first_init();
				head.lastspace.startptr.setptr(this + 1, baseaddr);
				head.lastspace.endptr.setptr((char*)this + initsz, baseaddr);

				for (unsigned int j = 0; j < _countof(rbp); ++j)
				{
					for (unsigned int i = 0; i < rballoc_page::NITEM; ++i)
					{
						single_list * dl = (single_list *)& rbp[j].data[i][0];
						head.rbitems.push(dl, baseaddr);
					}
				}
			}
		}
	};

	static_assert(sizeof(file_head) == PAGE_SIZE, "");
	static_assert(sizeof(rballoc_page) == PAGE_SIZE, "");
}

namespace fmallocns
{
	static int compare_rbia(const RBItemAlloc * a, const RBItemAlloc * b)
	{
		return a->memptr.value_ - b->memptr.value_;
	}

	typedef CRBTreeBase<RBItemPtrImpl>::RBItemX RBItemX;
	static_assert(sizeof(RBItem) == sizeof(RBItemX), "must be same memory layout");

	RBItemAlloc* CRBTreeAlloc::Delete(void * mem, baseaddr_t ba)
	{
		RBItemAlloc rba;
		memset(&rba, 0, sizeof(rba));
		rba.memptr.setptr(mem, ba);

		typedef CRBTreeTemp<RBItemPtrImpl> mytype;
		CRBTreeTemp<RBItemPtrImpl>::compare_func comp = (CRBTreeTemp<RBItemPtrImpl>::compare_func) &compare_rbia;
		mytype * this_ = (mytype*)this;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return (RBItemAlloc*)this_->Delete((RBItemX*)&rba, comp, (void*)ba);
	}
	bool CRBTreeAlloc::Find(void * mem, RBItemAlloc & ra, baseaddr_t ba)
	{
		RBItemAlloc rba;
		memset(&rba, 0, sizeof(rba));
		rba.memptr.setptr(mem, ba);

		typedef CRBTreeTemp<RBItemPtrImpl> mytype;
		CRBTreeTemp<RBItemPtrImpl>::compare_func comp = (CRBTreeTemp<RBItemPtrImpl>::compare_func) &compare_rbia;
		mytype * this_ = (mytype*)this;
		CSimpRWLock::AutoRLock _(*CSimpRWLock::from(&rwlock));
		RBItemAlloc * r = (RBItemAlloc*) this_->Find((RBItemX*)&rba, comp, (void*)ba);
		if (!r) return false;
		ra = *r;
		return true;
	}
	bool CRBTreeAlloc::Insert(RBItemAlloc * item, baseaddr_t ba)
	{
		typedef CRBTreeTemp<RBItemPtrImpl> mytype;
		CRBTreeTemp<RBItemPtrImpl>::compare_func comp = (CRBTreeTemp<RBItemPtrImpl>::compare_func) &compare_rbia;
		mytype * this_ = (mytype*)this;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return this_->Insert((RBItemX*)item, comp, (void*)ba);
	}
}

CFMalloc::CFMalloc() : CSharedFilemap(CSharedFilemap::Config::get_sample_config())
{
}

CFMalloc::~CFMalloc()
{
}

bool CFMalloc::init(const char * fn)
{
	if (! CSharedFilemap::init(fn))
		return false;
	fmallocns::file_st * fs = (fmallocns::file_st *)m_fileptr;
	fs->checked_init(m_mapsz);
	return true;
}

void * CFMalloc::get_app_space_()
{
	return ((fmallocns::file_st*)m_fileptr)->head.appspace;
}

packed_ptr CFMalloc::do_alloc(size_t sz)
{
	packed_ptr ppnull;
	ppnull.clear();

	for (;;)
	{
		void * p = 0;
		unsigned int oldsz = 0;
		{
			ENTER_FUNC();
			m_needspace = 0;
			size_t alcsz = compute_alloc_size(sz);
			oldsz = file()->head.lastspace.endptr.value_;
			size_t filesz = (size_t)oldsz << packed_ptr::SHIFTV;
			if (filesz > m_mapsz)
				m_needspace = 1;
			else if (alcsz & (PAGE_SIZE-1))
				p = do_inner_alloc(sz);
			else
				p = do_page_alloc_withrb(sz);

			if (p)
			{
				packed_ptr r;
				baseaddr_t ba = (baseaddr_t)m_fileptr;
				r.setptr(p, ba);
				return r;
			}
		}

		if (m_needspace)
		{
			const size_t M1 = 1024*1024;
			uint64_t incsz = oldsz;
			if (incsz < m_needspace) incsz = m_needspace;
			if (incsz < M1) incsz = M1;
			if (incsz + m_mapsz > m_cfg->maxfilesz())
			{
				incsz = m_cfg->maxfilesz() - m_mapsz;
			}
			incsz = (incsz + M1 - 1) & ~(M1-1);
			if (incsz > 512*M1) incsz = 512*M1;
			if (incsz == 0 && m_mapsz == ((size_t)oldsz << packed_ptr::SHIFTV))
			{
				//nothing to do.
				m_needspace = 0;
				return ppnull;
			}
			if (do_resize_file(incsz))
				continue;
		}
		break;
	}
	return ppnull;
}

void * CFMalloc::do_page_alloc_withrb(size_t sz0)
{
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	size_t sz = to_page(sz0);
	void * ptr = do_page_alloc(sz);
	if (!ptr) return NULL;
	if (set_rb(ptr, sz, sz-sz0))
	{
		return ptr;
	}
	else
	{
		//run out of rbitem. return back memory.
		if (sz/PAGE_SIZE <= 31)
		{
			unsigned int sindex = (unsigned int)(sz/PAGE_SIZE) - 1;
			file()->head.center_pages[sindex].push((single_list*)ptr, ba);
		}
		else
		{
			fmallocns::span * sp = (fmallocns::span*) ptr;
			sp->startptr.setptr((char*)ptr,ba);
			sp->endptr.setptr((char*)ptr + sz,ba);
			file()->head.center_npage.lk_addprev(&sp->lst, ba);
		}
		return NULL;
	}
}

void * CFMalloc::do_inner_alloc(size_t sz0)
{
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	size_t sz = compute_alloc_size(sz0);
	unsigned int npidx = alloc_size_to_index(sz);
	if ((int)npidx == -1 || npidx > _countof(file()->head.nonpaged_allocs))
	{
		BUG();
		return 0;
	}

	single_list * dl = file()->head.nonpaged_allocs[npidx].pop(ba);
	if (dl) return dl;

	//failed look at free list. require from center pages.
	size_t pgsz = to_page(sz);
	char * const optr = (char*) do_page_alloc(pgsz);
	if (!optr) return NULL;
	char * optre = optr + pgsz;

	if (! set_rb(optr, sz, sz-sz0))
	{
		//return back optr.
		int cpindex = (int)(pgsz/PAGE_SIZE) - 1;
		MYASSERT(cpindex < 31 && cpindex >= 0);
		file()->head.center_pages[cpindex].push((single_list*)optr, ba);
		return 0;
	}

	size_t tailsz = compute_alloc_tail(sz);
	if (tailsz)
	{
		unsigned int idx = alloc_size_to_index(tailsz);
		file()->head.nonpaged_allocs[idx].push((single_list*)optr, ba);
	}

	for (char * p = optr+tailsz+sz; p < optre; p += sz)
	{
		file()->head.nonpaged_allocs[npidx].push((single_list*)p, ba);
	}
	return optr+tailsz;
}

void * CFMalloc::do_page_alloc(size_t sz0)
{
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	if (sz0 == 0 || ! is_paged(sz0))
	{
		BUG();
		return NULL;
	}

	if (sz0 / PAGE_SIZE >= 0x800000) return NULL /*too large, we support at most 32G. */;
	unsigned int index = (unsigned int) (sz0/PAGE_SIZE)-1;

	for (unsigned int tryidx = index; tryidx < 31; ++tryidx)
	{
		single_list * dl = file()->head.center_pages[tryidx].pop(ba);
		if (dl)
		{
			if (tryidx != index)
			{
				unsigned int extra_pages = tryidx - index;
				unsigned int extra_idx = extra_pages - 1;
				single_list * extra_ptr = (single_list*) ((char*)dl + sz0);
				file()->head.center_pages[extra_idx].push(extra_ptr, ba);
				return dl;
			}
			else
				return dl;
		}
	}
	//find in the n pages.
	{
		void * m = 0;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&file()->head.center_npage.rwlock));
		for (double_list * d = &file()->head.center_npage.base;
			 d->next.rawptr(ba) != d;
			 d = (double_list*) d->next.rawptr(ba))
		{
			fmallocns::span * s1 = (fmallocns::span*) d->next.rawptr(ba);
			size_t ssz = (char*)s1->endptr.rawptr(ba) - (char*)s1->startptr.rawptr(ba);
			if (ssz >= sz0)
			{
				//use this ptr.
				void * endofmem = (char*)s1->startptr.rawptr(ba) + sz0;
				if (ssz - sz0 >= 32*PAGE_SIZE)
				{
					uint32_t endxx = s1->endptr.value_;
					m = (void*)s1;
					s1->lst.remove_self(ba);
					
					s1 = (fmallocns::span*) endofmem;
					s1->lst.first_init(ba);
					s1->startptr.setptr(endofmem, ba);
					s1->endptr.value_ = endxx;
					file()->head.center_npage.base.addnext(& s1->lst, ba);
				}
				else if (ssz-sz0 > 0)
				{
					unsigned int sindex = (unsigned int) ((ssz-sz0)/PAGE_SIZE) - 1; //[1,31]-1
					file()->head.center_pages[sindex].push((single_list*)endofmem, ba);
					s1->lst.remove_self(ba);
					m = (void*)s1;
				}
				else //==0
				{
					s1->lst.remove_self(ba);
					m = (void*)s1;
				}
				
				break;
			}
		}
		if (m) return m;
	}
	//still not found. find in the file span.
	for (;;)
	{
		space_span hlf = file()->head.lastspace;
		if (hlf.endptr.value_ != (m_mapsz >> packed_ptr::SHIFTV))
		{
			MYASSERT(!"changed by other process.");
			break;
		}
		size_t hlfsz = ((size_t)(hlf.endptr.value_ - hlf.startptr.value_)) << packed_ptr::SHIFTV;

		if (hlfsz >= sz0)
		{
			void * m = (void*) hlf.startptr.rawptr(ba);
			unsigned int newvalue = hlf.startptr.value_ + (unsigned int)(sz0 >> packed_ptr::SHIFTV);
			if (atomops::lock_comp_swap(&file()->head.lastspace.startptr.value_, hlf.startptr.value_, newvalue))
			{
				return m;
			}
			else
			{
				continue;
			}
		}
		else
			break;
	}

	//finally, we don't have so much memory.
	m_needspace = sz0;
	return NULL;
}

fmallocns::RBItemAlloc * CFMalloc::alloc_rbitem()
{
	baseaddr_t ba = (baseaddr_t)m_fileptr;

retry1:
	single_list * dl = file()->head.rbitems.pop(ba);
	if (dl)
	{
		return (fmallocns::RBItemAlloc*)dl;
	}
	//run out of rbitems, require one more page.
	fmallocns::rballoc_page * rp = (fmallocns::rballoc_page*) do_page_alloc( sizeof(fmallocns::rballoc_page) );
	if (rp==0)
	{
		return NULL;
	}
	else
	{
		for (unsigned int i=0; i<fmallocns::rballoc_page::NITEM; ++i)
		{
			single_list * x = (single_list*)  & rp->data[i][0];
			file()->head.rbitems.push(x, ba);
		}
		goto retry1;
	}
}

bool CFMalloc::set_rb(void * mem, size_t sz, size_t diff)
{
	MYASSERT(sz<32*1024*1024 && diff<PAGE_SIZE);
	MYASSERT( ((intptr_t)mem & (PAGE_SIZE-1)) == 0 );
	fmallocns::RBItemAlloc * ra = alloc_rbitem();
	if (ra == 0) return false;

	ra->flags = 1;
	ra->reserved = 0;
	ra->othersize = (unsigned int) (sz >> packed_ptr::SHIFTV);
	if ((sz & (PAGE_SIZE-1)) == 0)
	{
		ra->flags |= fmallocns::RBItemAlloc::IS_PAGED_ALLOC;
		ra->headersize = 0;
		ra->sizediff = 0;
	}
	else
	{
		ra->headersize = (unsigned short) compute_alloc_tail(sz);
		if (sz > PAGE_SIZE/2)
			ra->sizediff = (unsigned short) diff;
	}
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	ra->memptr.setptr(mem, ba);
	if (!file()->head.allocmap.Insert(ra, ba))
	{
		BUG();
		return false;
	}
	return true;
}

size_t CFMalloc::do_getsize(packed_ptr pp)
{
	if (! pp.notnull())
	{
		//are you kidding me ?
		return 0;
	}

	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	void * ptr = pp.rawptr(ba);

	//find in rb tree page.
	void * ptrpage = (void*) ((intptr_t)ptr & ~(intptr_t)(PAGE_SIZE-1));
	fmallocns::RBItemAlloc ra;
	if (file()->head.allocmap.Find(ptrpage, ra, ba))
	{
		if (ptrpage == ptr && ra.headersize != 0)
		{
			return ra.headersize;
		}
		else
		{
			size_t osz = ra.othersize;
			osz = (osz << packed_ptr::SHIFTV) - ra.sizediff;
			return osz;
		}
	}
	fflush(stdout);
	BUG();
	return 0;
}

void CFMalloc::do_free(void * ptr)
{
	if (!ptr) return;
	packed_ptr pp;
	pp.setptr(ptr, (baseaddr_t)m_fileptr);
	do_free(pp);
}

void CFMalloc::do_free(packed_ptr pp)
{
	if (! pp.notnull())
	{
		//are you kidding me ?
		return;
	}

	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	void * ptr = pp.rawptr(ba);

	//find in rb tree page.
	void * ptrpage = (void*) ((intptr_t)ptr & ~(intptr_t)(PAGE_SIZE-1));
	fmallocns::RBItemAlloc ra;
	if (!file()->head.allocmap.Find(ptrpage, ra, ba))
	{
		//free a pointer that is not allocated.
		MYASSERT(! "ptr is not allocated");
		BUG();
		return;
	}

	if (ra.flags & ra.IS_PAGED_ALLOC)
	{
		//this is a paged alloc.
		size_t sz = (size_t)ra.othersize << packed_ptr::SHIFTV;
		size_t npg = sz / PAGE_SIZE;

		if (ptr != ptrpage || npg == 0)
		{
			MYASSERT(! "ptr must be paged");
			BUG();
			return;
		}
		//remove pointer in rbtree.
		//warn: we should first remove this pointer from rbtree, then
		//return the memory block to centra pages. otherwise other processes my got the memory
		//and failed to set a rbtree item.
		fmallocns::RBItemAlloc * prb = file()->head.allocmap.Delete(ptrpage, ba);
		file()->head.rbitems.push((single_list*)prb, ba);
		if (npg >= 32)
		{
			fmallocns::span * sp = (fmallocns::span*)ptrpage;
			sp->startptr.setptr(ptrpage, ba);
			sp->endptr.setptr((char*)ptrpage + sz, ba);
			sp->lst.next.clear();
			sp->lst.prev.clear();
			file()->head.center_npage.lk_addprev(&sp->lst, ba);
		}
		else
		{
			unsigned int index = (unsigned int) (npg-1);
			single_list * a = (single_list*) ptrpage;
			a->next.clear();
			file()->head.center_pages[index].push(a, ba);
		}
	}
	else
	{
		//not paged align. return to memory list.
		size_t memsz;
		if (ptrpage == ptr && ra.headersize != 0)
			memsz = ra.headersize;
		else
			memsz = (size_t)ra.othersize << packed_ptr::SHIFTV;
		size_t allocsz = compute_alloc_size(memsz);
		MYASSERT(memsz == allocsz);
		if (memsz != allocsz || (allocsz & (PAGE_SIZE-1)) == 0)
		{
			MYASSERT("freeing memory size invalid!");
			BUG();
			return ;
		}
		size_t pdiff = (char*)ptr - (char*)ptrpage;
		size_t othersize = (size_t)ra.othersize << packed_ptr::SHIFTV;
		if (pdiff != 0 && (pdiff-ra.headersize) % othersize != 0)
		{
			MYASSERT(!"pointer is not pointed to valid position.");
			BUG();
			return ;
		}
		unsigned int index = alloc_size_to_index(allocsz);
		if ((int)index < 0)
		{
			BUG();
			return;
		}
		single_list * a = (single_list*)ptr;
		a->next.clear();
		file()->head.nonpaged_allocs[index].push(a, ba);
	}
}


/******* 分配办法：
 1. 按low(2**n, 2**n<=x)对齐到 2**n/8。
 eg: low(2**n, 2**n<=511)is 256,256/8=32, align at 32.
 这样算出来，非整页分配的情况只有72种。

 NOTE：对于非整页的分配，不进行切分。即如果想要分配16字节但是整体页数不够扩展了，
 即使此时32字节池有内容，也不分配给16字节使用。此时分配16字节失败，但分配32字节可成功。
 */
size_t CFMalloc::compute_alloc_size(size_t sz0)
{
	enum {div_factor=8, min_align=8};
	size_t sz = sz0;
	if (sz == 0) sz = 1;
	if (sz<32*1024)
	{
		size_t y = sz;
		while (sz)
		{
			y = sz;
			sz &= sz - 1;
		}
		size_t align = y/div_factor;
		if (align < min_align) align = min_align;
		MYASSERT(align <= PAGE_SIZE);
		sz = (sz0 + align - 1) & ~(align - 1);
	}
	else
	{
		size_t align = PAGE_SIZE;
		sz = (sz0 + align - 1) & ~(align - 1);
	}
	return sz;
}

size_t CFMalloc::compute_alloc_tail(size_t sz)
{
	//按sz排列完若干页，后面剩下多少？
	size_t np = (sz + PAGE_SIZE - 1) & ~(size_t)(PAGE_SIZE-1);
	return np % sz;
}

int CFMalloc::alloc_size_to_index(size_t from)
{
	MYASSERT((from % PAGE_SIZE) != 0);
	MYASSERT(compute_alloc_size(from) == from);
	static const signed char otbl[257] = {
		-1,-1,-1,-1,-1,-1,-1,-1, 0,-1,-1,-1,-1,-1,-1,-1,
		1 ,-1,-1,-1,-1,-1,-1,-1, 2,-1,-1,-1,-1,-1,-1,24,
		3 ,-1,-1,-1,-1,-1,-1,-1, 4,-1,-1,-1,-1,-1,-1,-1,
		5 ,-1,-1,-1,-1,-1,-1,-1, 6,-1,-1,-1,-1,36,32,25,
		7 ,-1,-1,-1,-1,-1,-1,-1, 8,-1,-1,-1,-1,-1,-1,-1,
		9 ,-1,-1,-1,-1,-1,-1,-1,10,-1,-1,-1,-1,-1,-1,26,
		11,-1,-1,-1,-1,-1,-1,-1,12,-1,-1,-1,-1,-1,-1,-1,
		13,-1,-1,-1,-1,-1,-1,-1,14,46,44,42,40,37,33,27,
		15,-1,-1,-1,-1,-1,-1,-1,-1,71,-1,-1,-1,-1,-1,-1,
		16,-1,-1,-1,-1,-1,-1,-1,-1,70,-1,-1,-1,-1,-1,28,
		17,-1,-1,-1,-1,-1,-1,-1,-1,69,-1,-1,-1,-1,-1,-1,
		18,-1,-1,-1,-1,-1,-1,-1,-1,68,-1,-1,-1,38,34,29,
		19,-1,-1,-1,-1,67,-1,-1,-1,66,-1,-1,-1,65,-1,-1,
		20,-1,-1,-1,-1,64,-1,-1,-1,63,-1,-1,-1,62,-1,30,
		21,-1,-1,61,-1,60,-1,59,-1,58,-1,57,-1,56,-1,55,
		22,-1,54,53,52,51,50,49,48,47,45,43,41,39,35,31,
		23
	};
	int rv = otbl[from % 257];
	MYASSERT(rv>=0);
	return rv;
}
