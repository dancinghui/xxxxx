#include "stdafx.h"
#include "base64.h"

static const char encoding_tbl[64] = {
		'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
		'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
		'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
		'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '/' };

static const char decoding_tbl[] = {62,-1,-1,-1,63,52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-2,-1,-1,-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,-1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51};

static int decode_look(char ch)
{
    if (ch < '+' || ch > 'z') return -1;
    return decoding_tbl[ch - '+'];
}

string base64_encode(const void *pbSrcData0, unsigned int nSrcLen)
{
	string rv;
	const unsigned char * pbSrcData = (const unsigned char *)pbSrcData0;

	if (!pbSrcData || nSrcLen == 0) return rv;
	rv.reserve((nSrcLen + 2) / 3 * 4 + 4);

	unsigned int i = 0;
	for (i = 0; i + 3 <= nSrcLen; i += 3)
	{
		unsigned int blk = (pbSrcData[i + 0] << 16) + (pbSrcData[i + 1] << 8) + pbSrcData[i + 2];
		rv += encoding_tbl[(blk >> 18) & 0x3f];
		rv += encoding_tbl[(blk >> 12) & 0x3f];
		rv += encoding_tbl[(blk >> 6) & 0x3f];
		rv += encoding_tbl[(blk >> 0) & 0x3f];
	}
	if (i + 1 == nSrcLen || i + 2 == nSrcLen)
	{
		unsigned char cha = pbSrcData[i + 0], chb = (i + 1 == nSrcLen) ? 0 : pbSrcData[i + 1];
		unsigned int blk = (cha << 16) + (chb << 8);
		rv += encoding_tbl[(blk >> 18) & 0x3f];
		rv += encoding_tbl[(blk >> 12) & 0x3f];
		rv += (i + 1 == nSrcLen) ? '=' : encoding_tbl[(blk >> 6) & 0x3f];
		rv += '=';
	}
	return rv;
}

struct b64_bitop
{
    string vout;
    unsigned int tmp, bits;
    b64_bitop(size_t elen){tmp=0; bits=0; vout.reserve((elen*3+3)/4); }
    void add6bits(unsigned int v)
    {
        tmp = (tmp<<6) + v;
        bits += 6;
        if (bits>=8)
        {
            addch(tmp >> (bits-8));
            bits -= 8;
        }
    }
    void addch(unsigned int v)
    {
        vout += (char)v;
    }
};

string base64_decode(const char *bs, size_t bslen, unsigned int * err)
{
#if defined(_DEBUG) || defined(DEBUG)
    for (int i=0; i<64; ++i)
    {
        int ii = decode_look(encoding_tbl[i]);
        if (ii != i)
        {
            abort();
        }
    }
#endif
    unsigned int xtmp = 0;
    unsigned int & errv = err ? *err : xtmp;
    errv = 0;
    
    b64_bitop bb(bslen);
    if (bslen == (size_t)-1) bslen = strlen(bs);
    unsigned int usedlen = 0;
    for (size_t i=0; i<bslen; ++i)
    {
        unsigned char ch = bs[i];
        if (isspace(ch)) continue;
        int chv = decode_look(ch);
        if (chv<0)
        {
            int eqcnt = 0, eqcntreq = ((usedlen+3)&~3) - usedlen;
            if (ch == '=')
            {
                ++ eqcnt;
				for (; i<bslen; ++i)
				{
					unsigned char ch1 = bs[i];
					if (isspace(ch1)) continue;
					if (ch1 == '=') { ++ eqcnt; continue; }
					errv |= BASE64_ERROR_EXTRACH;
					break;
				}
				if (eqcnt != eqcntreq) errv |= BASE64_ERROR_EXTRACH;
				return bb.vout;
            }
			errv |= BASE64_ERROR_INVALIDCH;
			break;
        }
        else
        {
            ++ usedlen;
            bb.add6bits(chv);
        }
    }
	return bb.vout;
}
