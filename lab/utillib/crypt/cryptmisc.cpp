#include "stdafx.h"
#include "cryptmisc.h"

#include <openssl/ssl.h>

size_t c_unescape(const char* s, size_t len, string & sb)
{
	size_t i;
	for (i = 0; i<len; ++i)
	{
		if (s[i] == '\\')
		{
#define EITEM(x, y) case x: sb+=y, ++i; break;
			switch (s[i + 1])
			{
				EITEM('a', '\a');
				EITEM('t', '\t');
				EITEM('v', '\v');
				EITEM('n', '\n');
				EITEM('b', '\b');
				EITEM('r', '\r');
				EITEM('f', '\f');
				EITEM('\'', '\'');
				EITEM('\"', '\"');
				EITEM('\\', '\\');
			default:
			case 0:
				return false;
			case 'X':
			case 'x':
			{
				i++;
				BYTE ch = 0;
				int ic = 0;
				while (s[i + 1] < 0x7f && isxdigit(s[i + 1]) && ic++<2)
				{
					BYTE v = s[i + 1] <= '9' ? s[i + 1] - '0' : (s[i + 1] | 0x20) - 'a' + 10;
					ch = ch * 16 + v;
					i++;
				}
				sb += ch;
			}
			break;
			case '0': case '1': case '2': case '3':
			case '4': case '5': case '6': case '7':
			{
				BYTE ch = 0;
				int ic = 0;
				while (s[i + 1] >= '0' && s[i + 1] <= '7' && ic++<3)
				{
					ch = ch * 8 + s[i + 1] - '0';
					i++;
				}
				sb += ch;
			}
			break;
			}
		}
		else if (s[i] == '"')
		{
			return i;
		}
		else
		{
			sb += s[i];
		}
	}
	return i;
}

void CRSA::init(const char * mod, const char * eee, const char * ddd)
{
	if (rsa1) RSA_free(rsa1);

	rsa1 = RSA_new();
	RSA_blinding_off(rsa1);
	BIGNUM *e = 0, *n = 0, *d = 0;
	BN_hex2bn(&n, mod);
	BN_hex2bn(&e, eee);
	if (ddd) BN_hex2bn(&d, ddd);
	rsa1->e = e;
	rsa1->d = d;
	rsa1->n = n;
}

CRSA::CRSA()
{
	m_padding = RSA_PKCS1_PADDING;
	rsa1 = 0;
}

CRSA::~CRSA()
{
	RSA_free(rsa1);
}

string CRSA::public_encrypt(const char * txt, unsigned int txtlen)
{
	char to[2048] = { 0 };
	int nerr = RSA_public_encrypt(txtlen, (unsigned char*)txt, (unsigned char*)to, rsa1, m_padding);
	string rv;
	if (nerr >= 0) rv.assign(to, nerr);
	return rv;
}

string CRSA::private_decrypt(const char * enc, unsigned int enclen)
{
	string rv;
	if (!rsa1->d) return rv;
	char to[2048] = { 0 };
	int nerr = RSA_private_decrypt(enclen, (unsigned char*)enc, (unsigned char*)to, rsa1, m_padding);
	if (nerr >= 0) rv.assign(to, nerr);
	return rv;
}

