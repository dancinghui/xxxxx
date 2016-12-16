#include "stdafx.h"
#include <openssl/md5.h>
#include "base/HelperFuncs.h"
#include "base/sutil.h"
#include "qqptlogin.h"
#include "crypt/tea.h"
#include "crypt/base64.h"
#include "crypt/cryptmisc.h"

bool getEncryption(const char * password, crefstr salt, crefstr vcode1, string & res)
{
	CRSA rsa;
	const char * mod = "F20CE00BAE5361F8FA3AE9CEFA495362FF7DA1BA628F64A347F0A8C012BF0B254A30CD92ABFFE7A6EE0DC424CB6166F8819EFA5BCCB20EDFB4AD02E412CCF579B1CA711D55B8B0B3AEB60153D5E0693A2A86F3167D7847A0CB8B00004716A9095D9BADC977CBB804DBDCBA6029A9710869A453F27DFDDF83C016D928B3CBF4C7";
	const char * eee = "03";
	rsa.init(mod, eee, 0);

	string vcode(vcode1);
	MD5_CTX ctx;
	unsigned char h1[16], s2[16];
	MD5_Init(&ctx);
	MD5_Update(&ctx, password, strlen(password));
	MD5_Final(h1, &ctx);
	//md5Pwd = encode16(h1, sizeof(h1));
	MD5_Init(&ctx);
	MD5_Update(&ctx, h1, sizeof(h1));
	MD5_Update(&ctx, salt.data(), salt.length());
	MD5_Final(s2, &ctx);

	string rsaH1 = rsa.public_encrypt((char*)h1, sizeof(h1));
	unsigned int rsaH1Len = (unsigned int) rsaH1.length();
	sutil::s_make_upper(vcode);
	string hexVcode = Helper::encode16(vcode.data(), vcode.length());
	unsigned int vcodeLen = (unsigned int) vcode.length();

	//TEA.initkey(s2);
	//rsaH1Len + rsaH1 + TEA.strToBytes(salt) + vcodeLen + hexVcode
	char ttsrc[4096];
	string rsaH1_x = Helper::encode16(rsaH1.data(), rsaH1.length());
	sprintf(ttsrc, "%04x%s%s%04x%s", rsaH1Len, rsaH1_x.c_str(), Helper::encode16(salt.data(), salt.length()).c_str(), vcodeLen, hexVcode.c_str());
	string ttsrc_d;
	Helper::decode16(ttsrc, ttsrc_d);

	string ob;
	ob.resize(ttsrc_d.length() + 32);
	int oblen = (int)ob.size();
	oi_symmetry_encrypt2((unsigned char*)ttsrc_d.data(), (int)ttsrc_d.length(), s2, (unsigned char*)&ob[0], &oblen);
	ob.resize(oblen);

	string oob = base64_encode(ob.data(), (unsigned int) ob.size());
	std::transform(oob.begin(), oob.end(), &oob[0], [](char ch)->char{
		switch (ch)
		{
		case '/': return '-';
		case '+': return '*';
		case '=': return '_';
		default: return ch;
		}
	});
	res.swap(oob);
	return true;
}
