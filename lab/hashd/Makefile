ULIBDIR=$(HOME)/work/dev/utillib
CFLAGS=-I$(ULIBDIR) -I$(ULIBDIR)/include
CXXFLAGS= -std=c++0x  -I$(ULIBDIR) -I$(ULIBDIR)/include
LIBS=-lstdc++ -lcrypto -lpthread

HOST=$(shell uname -s)
ifeq ($(HOST), Linux)
	LDFLAGS+=-Wl,-gc-sections
	STRIP=-s
endif
ifeq ($(HOST), Darwin)
	CXXFLAGS+=-I/opt/local/include
	CFLAGS+=-I/opt/local/include
	LDFLAGS+=-L /opt/local/lib
endif

hashd:hashd.o nethelper.o cptfuncs.o
	gcc -o $@ $^ $(LDFLAGS) $(LIBS)

cptfuncs.o:$(ULIBDIR)/include/cptfuncs.c
	gcc $(CFLAGS) -c $<

nethelper.o: $(ULIBDIR)/net/nethelper.cpp
	gcc $(CXXFLAGS) -c $<

hashd.o:hashd.cpp
	gcc $(CXXFLAGS) -c $<
