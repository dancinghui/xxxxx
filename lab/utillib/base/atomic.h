#pragma once

namespace atomops{
	template <int N>
	struct ops;

	template <>
	struct ops < 4 >
	{
#ifdef _WIN32
		typedef LONG sztype;
		static sztype lock_inc(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 4, "");
			return InterlockedIncrement(v);
		}
		static sztype lock_dec(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 4, "");
			return InterlockedDecrement(v);
		}
		static bool lock_cmp_swap(volatile sztype * v, sztype old, sztype new_)
		{
			return InterlockedCompareExchange(v, new_, old) == old;
		}
#else
		typedef int sztype;
		static sztype lock_inc(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 4, "");
			return __sync_fetch_and_add(v, (sztype)1) + 1;
		}
		static sztype lock_dec(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 4, "");
			return __sync_fetch_and_add(v, (sztype)-1) - 1;
		}
		static bool lock_cmp_swap(volatile sztype * v, sztype old, sztype new_)
		{
			return __sync_bool_compare_and_swap(v, old, new_);
		}
#endif
	};

	template <>
	struct ops < 8 >
	{
#ifdef _WIN32
		typedef ULONGLONG sztype;
		static sztype lock_inc(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 8, "");
			return InterlockedIncrement(v);
		}
		static sztype lock_dec(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 8, "");
			return InterlockedDecrement(v);
		}
		static bool lock_cmp_swap(volatile sztype * v, sztype old, sztype new_)
		{
			return InterlockedCompareExchange(v, new_, old) == old;
		}
#else
		typedef long long sztype;
		static sztype lock_inc(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 8, "");
			return __sync_fetch_and_add(v, (sztype)1) + 1;
		}
		static sztype lock_dec(volatile sztype * v)
		{
			static_assert(sizeof(sztype) == 8, "");
			return __sync_fetch_and_add(v, (sztype)-1) - 1;
		}
		static bool lock_cmp_swap(volatile sztype * v, sztype old, sztype new_)
		{
			return __sync_bool_compare_and_swap(v, old, new_);
		}
#endif
	};


	template <class T>
	T lock_inc(volatile T * v)
	{
		typedef typename ops<sizeof(T)>::sztype sztype;
		return (T)ops<sizeof(T)>::lock_inc((volatile sztype*)v);
	}
	template <class T>
	T lock_dec(volatile T * v)
	{
		typedef typename ops<sizeof(T)>::sztype sztype;
		return (T)ops<sizeof(T)>::lock_dec((volatile sztype*)v);
	}
	template <class T>
	bool lock_comp_swap(volatile T * ptr, volatile T old, volatile T new_)
	{
		typedef typename ops<sizeof(T)>::sztype sztype;
		return ops<sizeof(T)>::lock_cmp_swap((volatile sztype*)ptr, (sztype)old, (sztype)new_);
	}
}
