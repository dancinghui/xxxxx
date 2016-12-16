#pragma once
#include "base/lock.h"
#include "xptr.h"

#define PAGE_SIZE 4096

class CSharedFilemap
{
public:
	struct Config
	{
		virtual uint64_t maxfilesz();
		virtual uint32_t initsz();

		static Config * get_sample_config();
	};
	//basic constraint of the file header info.
	struct SFHeader
	{
		uint64_t magic;
		uint32_t version;
		volatile int rwlock_file;

		xptr::space_span lastspace;
	};
public:
	CRWLock lock; //wlock表示要进程级remap文件 此后m_fileptr会变化使内存访问失效..
protected:
	char m_fn[512];
	intptr_t m_handler;
	intptr_t m_mmhandler;
	size_t m_mapsz;
	SFHeader * m_fileptr;
	Config * m_cfg;
public:
	void RLock();
	void RUnlock();

protected:
	bool init(const char * fn);
	bool do_resize_file(size_t incsz);

protected:
	CSharedFilemap(Config * cfg);
	~CSharedFilemap();
};

#define AUTO_WLOCK(var) CSimpRWLock::AutoWLock _##__COUNTER__(*CSimpRWLock::from(&(var)))
#define AUTO_RLOCK(var) CSimpRWLock::AutoRLock _##__COUNTER__(*CSimpRWLock::from(&(var)))
#define SFM_JOIN1(a,b) a##b
#define SFM_JOIN(a,b) SFM_JOIN1(a,b)
#define ENTER_FUNC() CRWLock::AutoRLock SFM_JOIN(_lk_ , __COUNTER__)(this->lock); AUTO_RLOCK(m_fileptr->rwlock_file)
#define ENTER_FUNCO(o) LockUtil::CAutoRLock<CSharedFilemap> _##__COUNTER__(*(o))

class CRBFileBase : public CSharedFilemap
{
public:
	struct VComp
	{
		virtual int compare_node(const void * a, const void * b) = 0;
	};
	struct VRecv
	{
		virtual bool recv(void * a) = 0;
	};

	struct file_st
	{
		uint64_t magic;
		uint32_t version;
		volatile int rwlock_file;

		xptr::space_span lastspace;
		xptr::single_list rbitems;

		xptr::packed_ptr m_root;
		volatile int m_rwlock;

		char reserved[128 - 32 - 8];
	};
	static_assert(sizeof(file_st)==128, "");

protected:
	//Ret C(Key * key, Node * node)
	template <class C, class Key, class Node>
	struct call_c1 : VComp {
		call_c1(const C& cmp) : cmp(cmp){}
		int compare_node(const void * a, const void * b)
		{
			return cmp((Key*)a, (Node*)b);
		}
	private:
		const C & cmp;
	};

	template <class CLS, class Key, class Node, class FUNC>
	struct call_c2 : VComp {
		call_c2(CLS* c, FUNC f) : c(c), f(f){}
		int compare_node(const void * a, const void * b)
		{
			return (c->*f)((Key*)a, (Node*)b);
		}
	private:
		CLS * c;
		FUNC f;
	};

	template <class R, class Node>
	struct call_recv : VRecv
	{
		call_recv(const R & rcv):rcv(rcv){}
		bool recv(void * a)
		{
			return rcv((Node*)a);
		}
	private:
		const R & rcv;
	};

protected:
	xptr::packed_ptr alloc_item(size_t sz);
	void add_items(size_t sz);

	bool _insert(const void * r, size_t sz, VComp * cmp);
	bool _find(void * r, size_t sz, VComp * cmp);
	bool _delete(void * r, size_t sz, VComp * cmp);
	int _find_eq_range(void * r, VComp* cmp, VRecv * rcv);
	bool _find_do(const void * r, VComp* cmp, VRecv * rcv);

	CRBFileBase();
	~CRBFileBase();
};

template <class Node, class Settings>
class CRBFile : public CRBFileBase
{
protected:
	virtual int compare_node(const Node * a, const Node * b) = 0;

public:
	bool init(const char * fn)
	{
		CRWLock::AutoWLock _(this->lock);
		if (!CSharedFilemap::init(fn)) return false;

		if (m_fileptr->magic != Settings::magic || m_fileptr->version != Settings::version)
		{
			memset(m_fileptr, 0, sizeof(file_st));
			m_fileptr->lastspace.startptr.value_ = (unsigned int)(sizeof(file_st) >> xptr::packed_ptr::SHIFTV);
			m_fileptr->lastspace.endptr.value_ = (unsigned int)(m_mapsz >> xptr::packed_ptr::SHIFTV);
			m_fileptr->magic = Settings::magic;
			m_fileptr->version = Settings::version;
			add_items(sizeof(Node));
		}
		return true;
	}

	bool Insert(const Node * kn)
	{
		typedef CRBFile<Node, Settings> this_class;
		call_c2<this_class, Node, Node, int (this_class::*)(const Node *a, const Node *b)> _(this, &this_class::compare_node);
		return _insert(kn, sizeof(Node), &_);
	}
	bool Find(Node * kn)
	{
		typedef CRBFile<Node, Settings> this_class;
		call_c2<this_class, Node, Node, int (this_class::*)(const Node *a, const Node *b)> _(this, &this_class::compare_node);
		return _find(kn, sizeof(Node), &_);
	}
	bool Delete(const Node * kn)
	{
		typedef CRBFile<Node, Settings> this_class;
		call_c2<this_class, Node, Node, int (this_class::*)(const Node *a, const Node *b)> _(this, &this_class::compare_node);
		return _delete(kn, sizeof(Node), &_);
	}

	template <class R, class C, class Key>//rcv((Node*)findnode)
	int find_eq_range(const Key * kn, const R & rcv, const C & cmp)
	{
		call_c1<C, Key, Node> cmp_(cmp);
		call_recv<R, Node> rcv_(rcv);
		return _find_eq_range((void*)kn, &cmp_, &rcv_);
	}

	template <class R, class C>//rcv((Node*)findnode)
	bool find_do(const Node * kn, const R & rcv, const C & cmp)
	{
		call_c1<C, Node, Node> cmp_(cmp);
		call_recv<R, Node> rcv_(rcv);
		return _find_do(kn, &cmp_, &rcv_);
	}

	template <class R, class C, class Key>//rcv((Node*)findnode)
	bool find_key_do(const Key * kn, const R & rcv, const C & cmp)
	{
		call_c1<C, Key, Node> cmp_(cmp);
		call_recv<R, Node> rcv_(rcv);
		return _find_do(kn, &cmp_, &rcv_);
	}

	template <class R>//rcv((Node*)findnode)
	bool find_do(const Node * kn, const R & rcv)
	{
		typedef CRBFile<Node, Settings> this_class;
		call_c2<this_class, Node, Node, int (this_class::*)(const Node *a, const Node *b)> _(this, &this_class::compare_node);
		call_recv<R, Node> rcv_(rcv);
		return _find_do(kn, &_, &rcv_);
	}
};
