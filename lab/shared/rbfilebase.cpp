#include "stdafx.h"
#include "sharedfm.h"
#include "rbtree.hpp"
#include "xptr.h"
#include "xptrrb.h"

using namespace xptr;

#define file() ((file_st*)m_fileptr)
#define rbtree() ((CRBTempHack*)(&file()->m_root))

class CRBTempHack : public CRBTreeTemp < RBItemPtrImpl >
{
public:
	template <class C>
	RBItemX * FindLB(const RBItemX * itm, const C& cmp, void * env)
	{
		return CRBTreeTemp < RBItemPtrImpl >::FindLB(itm, cmp, env);
	}
	RBItemX * next_item(RBItemX * p, void * env)
	{
		return CRBTreeTemp < RBItemPtrImpl >::next_item(p, env);
	}
};

struct vcomp_cmp_t
{
	CRBFileBase::VComp * vf;

	int operator () (const void * a, const void * b) const
	{
		return vf->compare_node((void*)a, (void*)b);
	}
	vcomp_cmp_t(CRBFileBase::VComp* vf) :vf(vf){}
};

CRBFileBase::CRBFileBase() : CSharedFilemap(CSharedFilemap::Config::get_sample_config())
{
}

CRBFileBase::~CRBFileBase()
{
}

bool CRBFileBase::_insert(const void * r, size_t sz, VComp * cmp)
{
	packed_ptr ptr = alloc_item(sz);

	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	CRBTempHack::RBItemX * itm = (CRBTempHack::RBItemX *)ptr.rawptr(ba);
	memcpy(itm, r, sz);
	if (!rbtree()->Insert(itm, vcomp_cmp_t(cmp), (void*)ba))
	{
		file()->rbitems.push((single_list*)itm, ba);
		return false;
	}
	return true;
}

bool CRBFileBase::_find(void * r, size_t sz, VComp * cmp)
{
	packed_ptr ptr = alloc_item(sz);

	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	CRBTempHack::RBItemX * itm = (CRBTempHack::RBItemX *)ptr.rawptr(ba);
	memcpy(itm, r, sz);
	CRBTempHack::RBItemX * f = rbtree()->Find(itm, vcomp_cmp_t(cmp), (void*)ba);
	if (f) memcpy(r, f, sz);
	return !!f;
}

bool CRBFileBase::_delete(void * r, size_t sz, VComp * cmp)
{
	packed_ptr ptr = alloc_item(sz);

	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	CRBTempHack::RBItemX * itm = (CRBTempHack::RBItemX *)ptr.rawptr(ba);
	memcpy(itm, r, sz);
	CRBTempHack::RBItemX * f = rbtree()->Delete(itm, vcomp_cmp_t(cmp), m_fileptr);
	if (f)
	{
		file()->rbitems.push( (single_list*) f, ba);
	}
	return !!f;
}

int CRBFileBase::_find_eq_range(void * r, VComp* cmp, VRecv * rcv)
{
	ENTER_FUNC();
	CRBTempHack::RBItemX * f = rbtree()->FindLB((CRBTempHack::RBItemX*)r, vcomp_cmp_t(cmp), m_fileptr);
	int n = 0;
	for (; f; f = rbtree()->next_item(f, m_fileptr))
	{
		int c = cmp->compare_node(r, f);
		if (c > 0) continue;
		if (c < 0) break;
		++n;
		if (! rcv->recv(f)) break;
	}
	return n;
}

bool CRBFileBase::_find_do(const void * r, VComp* cmp, VRecv * rcv)
{
	ENTER_FUNC();
	baseaddr_t ba = (baseaddr_t)m_fileptr;
	CRBTempHack::RBItemX * f = rbtree()->Find((CRBTempHack::RBItemX *)r, vcomp_cmp_t(cmp), (void*)ba);
	if (f)
	{
		rcv->recv(f);
	}
	return !!f;
}

////////////////////////////////////////////////////

packed_ptr CRBFileBase::alloc_item(size_t sz)
{
	{
		ENTER_FUNC();
		baseaddr_t ba = (baseaddr_t)m_fileptr;
		xptr::single_list * s = file()->rbitems.pop(ba);
		if (s)
		{
			packed_ptr pp;
			pp.setptr(s, ba);
			return pp;
		}
	}

	if (CSharedFilemap::do_resize_file(1024 * 1024))
	{
		{
			CRWLock::AutoWLock file_expand(this->lock);
			add_items(sz);
		}
		return alloc_item(sz);
	}
	packed_ptr pp;
	pp.value_ = 0;
	return pp;
}

void CRBFileBase::add_items(size_t sz) //this->lock must have been w-locked.
{
	MYASSERT(sz >= 24);
	MYASSERT(sz % 8 == 0);

	AUTO_WLOCK(m_fileptr->rwlock_file);

	baseaddr_t ba = (baseaddr_t)m_fileptr;
	char * p1 = (char*)m_fileptr->lastspace.startptr.rawptr(ba);
	char * pe = (char*)m_fileptr->lastspace.endptr.rawptr(ba);
	char * pi = 0;
	for (pi = pe - sz; pi >= p1; pi-=sz)
	{
		file()->rbitems.push((single_list*)pi, ba);
	}
	m_fileptr->lastspace.startptr.setptr(pe, ba);
}
