#pragma once

class KillCheck
{
public:
	KillCheck();
	~KillCheck();

	static void Register(void (*func)(void *), void * arg);
	static void Unregister(void (*func)(void*), void * arg);
};
