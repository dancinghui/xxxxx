#include "stdafx.h"
#include "base/lock.h"
#include "xptr.h"
#include "xptrrb.h"

namespace xptr {
	class CRBTempHack : public CRBTreeTemp < RBItemPtrImpl >
	{
	public:
		RBItemX * FindLB(const RBItemX * itm, compare_func cmp, void * env)
		{
			return CRBTreeTemp < RBItemPtrImpl >::FindLB(itm, cmp, env);
		}
		RBItemX * next_item(RBItemX * p, void * env)
		{
			return CRBTreeTemp < RBItemPtrImpl >::next_item(p, env);
		}
	};

	void CBasicRB::clear_all(free_func ff, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&m_rwlock));
		return this_->clear((CRBTempHack::unalloc_func)ff, (void*)ba);
	}

	RBItem * CBasicRB::Delete(const RBItem * itm, compare_func cmp, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&m_rwlock));
		return (RBItem*)this_->Delete((CRBTempHack::RBItemX*)itm, (CRBTempHack::compare_func)cmp, (void*)ba);
	}

	bool CBasicRB::Find(RBItem * inout, size_t size, compare_func cmp, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		CSimpRWLock::AutoRLock _(*CSimpRWLock::from(&m_rwlock));
		CRBTempHack::RBItemX * p = this_->Find((CRBTempHack::RBItemX*)inout, (CRBTempHack::compare_func)cmp, (void*)ba);
		if (!p) return false;
		memcpy(inout, p, size);
		return true;
	}

	RBItem * CBasicRB::Find(const RBItem * itm, compare_func cmp, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		CSimpRWLock::AutoRLock _(*CSimpRWLock::from(&m_rwlock));
		CRBTempHack::RBItemX * p = this_->Find((CRBTempHack::RBItemX*)itm, (CRBTempHack::compare_func)cmp, (void*)ba);
		return (RBItem*)p;
	}

	RBItem * CBasicRB::FindLB(const RBItem * itm, compare_func cmp, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		return (RBItem*)this_->FindLB((CRBTempHack::RBItemX*)itm, (CRBTempHack::compare_func)cmp, (void*)ba);
	}

	RBItem * CBasicRB::next_item(RBItem * itm, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		return (RBItem*)this_->next_item((CRBTempHack::RBItemX*)itm, (void*)ba);
	}

	bool CBasicRB::Insert(RBItem * newitm, compare_func cmp, baseaddr_t ba)
	{
		CRBTempHack * this_ = (CRBTempHack*)this;
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&m_rwlock));
		return this_->Insert((CRBTempHack::RBItemX*)newitm, (CRBTempHack::compare_func)cmp, (void*)ba);
	}
}
