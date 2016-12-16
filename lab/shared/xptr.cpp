#include "stdafx.h"
#include "xptr.h"
#include "base/lock.h"
#include "base/atomic.h"

namespace xptr
{
	void single_list::push(single_list * a, baseaddr_t ba)
	{
		for (;;)
		{
			single_list oldvalue;
			oldvalue.next.value_ = *(volatile unsigned int *)& this->next.value_;
			oldvalue.serialno = *(volatile unsigned int *)& this->serialno;

			single_list newvalue;
			newvalue.next.value_ = packed_ptr::ptr2v(a, ba);
			newvalue.serialno = oldvalue.serialno + 1;

			a->next.value_ = oldvalue.next.value_;

			if (atomops::lock_comp_swap((volatile uint64_t*)this, *(uint64_t*)&oldvalue, *(uint64_t*)&newvalue))
				return;
		}
	}
	single_list* single_list::pop(baseaddr_t ba)
	{
		for (;;)
		{
			single_list oldvalue;
			oldvalue.next.value_ = *(volatile unsigned int *)& this->next.value_;
			oldvalue.serialno = *(volatile unsigned int *)& this->serialno;

			packed_ptr tmp;
			tmp.value_ = oldvalue.next.value_;
			single_list * nn = (single_list*)tmp.rawptr(ba);

			if (!nn) return 0;

			single_list newvalue;
			newvalue.next.value_ = nn->next.value_;
			newvalue.serialno = oldvalue.serialno + 1;

			if (atomops::lock_comp_swap((volatile uint64_t*)this, *(uint64_t*)&oldvalue, *(uint64_t*)&newvalue))
			{
				nn->next.value_ = 0;
				return nn;
			}
		}
	}

	void double_list::first_init(baseaddr_t ba)
	{
		prev.setptr(this, ba);
		next.setptr(this, ba);
	}
	bool double_list::popnext(double_list * &x, baseaddr_t ba)
	{
		double_list * n = (double_list*)next.rawptr(ba);
		double_list * nn = (double_list*) (n->next.rawptr(ba));
		next.setptr(nn, ba);
		nn->prev.setptr(this, ba);
		if (n == this) return false;
		x = n;
		return true;
	}
	bool double_list::popprev(double_list * &x, baseaddr_t ba)
	{
		double_list * n = (double_list*)prev.rawptr(ba);
		double_list * nn = (double_list*) (n->prev.rawptr(ba));
		prev.setptr(nn, ba);
		nn->next.setptr(this, ba);
		if (n == this) return false;
		x = n;
		return true;
	}
	void double_list::addnext(double_list * x, baseaddr_t ba)
	{
		x->next.value_ = next.value_;
		x->prev.setptr(this, ba);
		((double_list*)next.rawptr(ba))->prev.setptr(x, ba);
		next.setptr(x, ba);
	}
	void double_list::addprev(double_list * x, baseaddr_t ba)
	{
		x->next.setptr(this, ba);
		x->prev.value_ = prev.value_;
		((double_list*)prev.rawptr(ba))->next.setptr(x, ba);
		prev.setptr(x, ba);
	}
	void double_list::remove_self(baseaddr_t ba)
	{
		double_list * p = (double_list*)prev.rawptr(ba);
		double_list * n = (double_list*)next.rawptr(ba);
		p->next.value_ = next.value_;
		n->prev.value_ = prev.value_;
		prev.setptr(this, ba);
		next.setptr(this, ba);
	}

	bool double_list_lk::lk_popnext(double_list * &x, baseaddr_t baseaddr)
	{
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return base.popnext(x, baseaddr);
	}
	bool double_list_lk::lk_popprev(double_list * &x, baseaddr_t baseaddr)
	{
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return base.popprev(x, baseaddr);
	}
	void double_list_lk::lk_addnext(double_list * x, baseaddr_t baseaddr)
	{
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return base.addnext(x, baseaddr);
	}
	void double_list_lk::lk_addprev(double_list * x, baseaddr_t baseaddr)
	{
		CSimpRWLock::AutoWLock _(*CSimpRWLock::from(&rwlock));
		return base.addprev(x, baseaddr);
	}
}
