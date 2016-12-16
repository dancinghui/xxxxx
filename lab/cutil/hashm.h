#pragma once
#include "basicrt.h"

class CHashTable
{
private:
	CLock m_lock;
	struct hashobj{
		unsigned char md[16];
		bool operator == (const hashobj & ho) const
		{
			return memcmp(md, ho.md, 16) == 0;
		}
	};
	struct Hasher{
		size_t operator () (const hashobj & ho) const
		{
			size_t * ps = (size_t*)ho.md;
			size_t rv = 0;
			for (int i=0; i*sizeof(size_t) < sizeof(ho.md); ++i)
			{
				rv = rv ^ ps[i];
			}
			return rv;
		}
	};
	std::unordered_map<hashobj, int, Hasher> m_hashmap;
public:
	int Lookup(unsigned char (&md)[16])
	{
		int rv = -1;
		hashobj obj;
		memcpy(obj.md, md, 16);

		m_lock.Lock();
		rv = m_hashmap[obj];
		m_lock.Unlock();
		return rv;
	}
	int Inc(unsigned char (&md)[16])
	{
		int rv = -1;
		hashobj obj;
		memcpy(obj.md, md, 16);
		m_lock.Lock();
		rv = ++ m_hashmap[obj];
		m_lock.Unlock();
		return rv;
	}
};

