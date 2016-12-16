#pragma once


namespace xptr{
	typedef const struct base__ * baseaddr_t;

	struct shift_type_t
	{
		int dummy;
		shift_type_t(int v):dummy(v){}
		friend unsigned long long operator << (unsigned long long a, const shift_type_t& v)
		{
			return a << v.dummy;
		}
		friend unsigned long long operator >> (unsigned long long a, const shift_type_t& v)
		{
			return a >> v.dummy;
		}
#ifdef _WIN64
	private:
#endif
		friend  unsigned long operator << (unsigned long a, const shift_type_t& v)
		{
			return a << v.dummy;
		}
		friend  unsigned long operator >> (unsigned long a, const shift_type_t& v)
		{
			return a >> v.dummy;
		}
	private:
		friend size_t operator << (unsigned int a, const shift_type_t& v);
		friend size_t operator >> (unsigned int a, const shift_type_t& v);
	private:
		friend size_t operator << (int a, const shift_type_t& v);
		friend size_t operator >> ( int a, const shift_type_t& v);
	};

	struct packed_ptr{
#if (defined(_DEBUG) || defined (DEBUG)) && (defined(_M_AMD64) || defined(__amd64__))
		static shift_type_t SHIFTV;
#else
		enum { SHIFTV = 3 /*align at 8 bytes.*/};
#endif
		unsigned int value_;

		void * rawptr(baseaddr_t baseaddr){
			if (!value_) return 0;
			return (char*)baseaddr + ((size_t)value_ << SHIFTV);
		}
		void setptr(void * x, baseaddr_t baseaddr)
		{
			value_ = ptr2v(x, baseaddr);
		}
		static unsigned int ptr2v(void *x, baseaddr_t ba)
		{
			if (!x) { return 0; }
			MYASSERT( ((uintptr_t)x & (((size_t)1 << SHIFTV)-1)) == 0);
			MYASSERT(x > ba);
			size_t v1 = (char*)x - (char*)ba;
			v1 = v1 >> SHIFTV;
			MYASSERT(v1 < 0x100000000llu);
			return (unsigned int)v1;
		}
		bool notnull() const { return value_ != 0; }
		void clear() { value_ = 0; }
	private:
		int operator - (const packed_ptr & ano) const;
		int operator - (const packed_ptr & ano);
		int operator + (const packed_ptr & ano) const;
		int operator + (const packed_ptr & ano);
	};



	template <class T>
	struct packed_ptr_t : packed_ptr {
		T * rawptr(baseaddr_t baseaddr){return (T*)packed_ptr::rawptr(baseaddr);}
		void setptr(T* x, baseaddr_t baseaddr){packed_ptr::setptr((void*)x, baseaddr);}
	};

	struct single_list
	{
		packed_ptr_t<single_list> next;
		int serialno;

		void push(single_list * a, baseaddr_t ba);
		single_list* pop(baseaddr_t ba);
	};

	struct double_list
	{
		packed_ptr prev;
		packed_ptr next;

		void first_init(baseaddr_t);
		bool popnext(double_list * &x, baseaddr_t);
		bool popprev(double_list * &x, baseaddr_t);
		void addnext(double_list * x, baseaddr_t);
		void addprev(double_list * x, baseaddr_t);
		void remove_self(baseaddr_t);
	};

	struct double_list_lk {
		double_list base;
		int rwlock;
		int reseved;
		bool lk_popnext(double_list * &x, baseaddr_t baseaddr);
		bool lk_popprev(double_list * &x, baseaddr_t baseaddr);
		void lk_addnext(double_list * x, baseaddr_t baseaddr);
		void lk_addprev(double_list * x, baseaddr_t baseaddr);
	};

	struct space_span{
		packed_ptr startptr;
		packed_ptr endptr;
	};
}
