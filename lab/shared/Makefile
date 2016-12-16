OBJS=modhelper.o fmalloc.o xptr.o lock.o killcheck.o xptrrb.o sharedfm.o xptrdbg.o rbfilebase.o \
HelperFuncs.o sutil.o base64.o cryptmisc.o tea.o basichtml.o cptfuncs.o process_single.o fmtstr.o\
dump.o error.o hashtable.o hashtable_seed.o load.o memory.o pack_unpack.o strbuffer.o strconv.o utf.o value.o cmongo.o
CFLAGS=-Wall -fPIC -O2 -g -I ../utillib -I ../utillib/include -I jansson -I /usr/local/include/libmongoc-1.0 -I /usr/local/include/libbson-1.0
LDFLAGS=
LIBS=-lcrypto

vpath %.cpp ../utillib/base ../utillib/misc ../utillib/fileformat ../utillib/crypt
vpath %.c ../utillib/include jansson

HOST=$(shell uname -s)
ifeq ($(HOST), Linux)
	LDFLAGS+=-Wl,-gc-sections
	CFLAGS+= -I /usr/include/python2.7
endif
ifeq ($(HOST), Darwin)
	CFLAGS+=-I/opt/local/include
	LDFLAGS+=-L /opt/local/lib
endif

.cpp.o:
	g++ -c -o $@ -std=c++11 $(CFLAGS) $<

all:libshared.a

libshared.a:$(OBJS)
	ar rcs $@  $(OBJS)

clean:
	-@ rm -f *.o
