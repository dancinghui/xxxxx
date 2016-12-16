#pragma once

size_t c_unescape(const char* s, size_t len, string & sb);
struct rsa_st;

class CRSA
{
	rsa_st * rsa1;
	int m_padding;
	
public:
	CRSA();
	~CRSA();
	void init(const char * mod, const char * eee, const char * ddd);
	string public_encrypt(const char * txt, unsigned int txtlen);
	string private_decrypt(const char * enc, unsigned int enclen);
	
	string public_encrypt(crefstr txt)
	{
		return public_encrypt(txt.data(), (unsigned int) txt.length());
	}
	string private_decrypt(crefstr enc)
	{
		return private_decrypt(enc.data(), (unsigned int) enc.length());
	}
	void set_padding(int padding)
	{
		m_padding = padding;
	}
	int get_padding()const{return m_padding;}
};
