#pragma once

/************************************************************************************************
	对称加密底层函数
************************************************************************************************/
//pOutBuffer、pInBuffer均为8byte, pKey为16byte
void TeaEncryptECB(const BYTE *pInBuf, const BYTE *pKey, BYTE *pOutBuf);
void TeaDecryptECB(const BYTE *pInBuf, const BYTE *pKey, BYTE *pOutBuf);
inline void TeaEncryptECB3(const BYTE *pInBuf, const BYTE *pKey, BYTE *pOutBuf);

/// QQ对称加密第一代函数. (TEA加密算法,CBC模式). 密文格式:PadLen(1byte)+Padding(var,0-7byte)+Salt(2byte)+Body(var byte)+Zero(7byte)
/** @param pInBuf in,		需加密的明文部分(Body)
	@param nInBufLen in,	pInBuf长度
	@param pKey in,			加密Key, 长度固定为16Byte.
	@param pOutBuf out,		输出的密文
	@param pOutBufLen in out,	pOutBuf的长度. 长度是8byte的倍数,至少应预留nInBufLen+17;
*/
void oi_symmetry_encrypt(const BYTE* pInBuf, int nInBufLen, const BYTE* pKey, BYTE* pOutBuf, int *pOutBufLen);


/// QQ对称解密第一代函数. (TEA加密算法,CBC模式). 密文格式:PadLen(1byte)+Padding(var,0-7byte)+Salt(2byte)+Body(var byte)+Zero(7byte)
/** @param pInBuf in,		需解密的密文.
	@param nInBufLen in,	pInBuf长度. 8byte的倍数
	@param pKey in,			解密Key, 长度固定为16Byte.
	@param pOutBuf out,		输出的明文
	@param pOutBufLen in out,	pOutBuf的长度. 至少应预留nInBufLen-10
	@return BOOL,			如果格式正确返回TRUE
*/
BOOL oi_symmetry_decrypt(const BYTE* pInBuf, int nInBufLen, const BYTE* pKey, BYTE* pOutBuf, int *pOutBufLen);

/// QQ对称计算加密长度第二代函数. (TEA加密算法,CBC模式). 密文格式:PadLen(1byte)+Padding(var,0-7byte)+Salt(2byte)+Body(var byte)+Zero(7byte)
/** @param nInBufLen in,	nInBufLen为需加密的明文部分(Body)长度
	@return int,			返回为加密后的长度(是8byte的倍数)
*/
int oi_symmetry_encrypt2_len(int nInBufLen);


/// QQ对称加密第二代函数. (TEA加密算法,CBC模式). 密文格式:PadLen(1byte)+Padding(var,0-7byte)+Salt(2byte)+Body(var byte)+Zero(7byte)
/** @param pInBuf in,		需加密的明文部分(Body)
	@param nInBufLen in,	pInBuf长度
	@param pKey in,			加密Key, 长度固定为16Byte.
	@param pOutBuf out,		输出的密文
	@param pOutBufLen in out,	pOutBuf的长度. 长度是8byte的倍数,至少应预留nInBufLen+17;
*/
void oi_symmetry_encrypt2(const BYTE* pInBuf, int nInBufLen, const BYTE* pKey, BYTE* pOutBuf, int *pOutBufLen);

/// QQ对称解密第二代函数. (TEA加密算法,CBC模式). 密文格式:PadLen(1byte)+Padding(var,0-7byte)+Salt(2byte)+Body(var byte)+Zero(7byte)
/** @param pInBuf in,		需解密的密文.
	@param nInBufLen in,	pInBuf长度. 8byte的倍数
	@param pKey in,			解密Key, 长度固定为16Byte.
	@param pOutBuf out,		输出的明文
	@param pOutBufLen in out,	pOutBuf的长度. 至少应预留nInBufLen-10
	@return BOOL,			如果格式正确返回TRUE
*/
BOOL oi_symmetry_decrypt2(const BYTE* pInBuf, int nInBufLen, const BYTE* pKey, BYTE* pOutBuf, int *pOutBufLen);

#ifdef _MSC_VER
#define htonl _byteswap_ulong
#define ntohl _byteswap_ulong
#endif
