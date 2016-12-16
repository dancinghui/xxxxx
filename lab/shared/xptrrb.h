#pragma once
#include "rbtree.hpp"

namespace xptr
{
	struct RBItem{
		packed_ptr parent_, left_, right_;
		union{
			struct {
				unsigned int one : 1;
				unsigned int zero : 1;
				unsigned int color : 1;
				unsigned int flags_avail : 29;
			};
			unsigned int flags;
		};
	};

	static_assert(sizeof(RBItem) == 16, "");

	struct RBItemPtrImpl : packed_ptr {
		typedef CRBTreeBase<RBItemPtrImpl>::RBItemX RBItemX;

		RBItemX * v(void * env)
		{
			return (RBItemX*)rawptr((baseaddr_t)env);
		}
		void set(RBItemX * p, void *env)
		{
			setptr(p, (baseaddr_t)env);
		}
	};

	class CBasicRB
	{
	public:
		typedef int (*compare_func)(const RBItem * a, const RBItem * b);
		typedef void (*free_func)(RBItem * a);
	protected:
		packed_ptr m_root;
		volatile int m_rwlock;
	public:
		void clear_all(free_func ff, baseaddr_t ba);
		RBItem * Delete(const RBItem * itm, compare_func cmp, baseaddr_t ba);
		bool Find(RBItem * inout, size_t size, compare_func cmp, baseaddr_t ba);
		bool Insert(RBItem * newitm, compare_func cmp, baseaddr_t ba);
	private:
		RBItem * Find(const RBItem * itm, compare_func cmp, baseaddr_t ba);
		RBItem * FindLB(const RBItem * itm, compare_func cmp, baseaddr_t ba);
		RBItem * next_item(RBItem * itm, baseaddr_t ba);
	public:
		template <class T>
		bool Find(const RBItem * itm, compare_func cmp, baseaddr_t ba, const T& obj)
		{
			CSimpRWLock::AutoRLock _(*CSimpRWLock::from(&m_rwlock));
			RBItem * fnd = Find(itm, cmp, ba);
			if (fnd)
			{
				obj(fnd);
				return true;
			}
			return false;
		}
		template <class T>
		int FindEqRange(const RBItem * itm, compare_func cmp, baseaddr_t ba, const T & obj)
		{
			int n = 0;
			CSimpRWLock::AutoRLock _(*CSimpRWLock::from(&m_rwlock));
			for (RBItem * fnd = FindLB(itm, cmp, ba);
				fnd;
				fnd = next_item(fnd, ba))
			{
				if (cmp(itm, fnd) != 0)
					break;
				++n;
				if (!obj(fnd))
					break;
			}
			return n;
		}
	};
}
