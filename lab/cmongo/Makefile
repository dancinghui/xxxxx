UTILLIB=$(shell ls -d1 ~/work/dev/utillib )
LDFLAGS=-L/usr/local/lib
CFLAGS=-I/usr/local/include/libmongoc-1.0/ -I/usr/local/include/libbson-1.0/ -I$(UTILLIB) -I$(UTILLIB)/include -I ../shared
CXXFLAGS=-std=c++11 $(CFLAGS)
LIBS=-lmongoc-1.0 -lbson-1.0 -lstdc++ -L ../shared -lshared

HOST=$(shell uname -s)
ifeq ($(HOST), Linux)
	CFLAGS+=-ffunction-sections -fdata-sections -g
	CXXFLAGS+=-ffunction-sections -fdata-sections -g
	LDFLAGS+=-Wl,-gc-sections
	LIBS+=-lpthread
endif

vpath %.cpp $(UTILLIB)/base
vpath %.c $(UTILLIB)/include

all:cmongo
	
cmongo:main.o pagestore.o cptfuncs.o HelperFuncs.o
	$(CC) -o $@ $^  $(LIBS)

clean:
	-@rm -f *.o cmongo
