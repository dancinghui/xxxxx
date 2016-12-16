#pragma once

enum base64_error_enums
{
    BASE64_ERROR_INVALIDCH=1,
    BASE64_ERROR_EXTRACH = 2,
};
string base64_encode(const void *pbSrcData0, unsigned int nSrcLen);
string base64_decode(const char *bs, size_t bslen, unsigned int * err=0);

inline string base64_encode(crefstr d){return base64_encode(d.data(), (unsigned int)d.length());}
inline string base64_decode(crefstr d){return base64_decode(d.data(), (unsigned int)d.length());}
