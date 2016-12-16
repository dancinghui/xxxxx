CXXFLAGS=-std=c++11 -I ../utillib -I ../utillib/include -g -O2
CFLAGS=-g -O2
OBJS=bintest.o cptfuncs.o HelperFuncs.o
EXE=bintest
LIBS=-lpthread
LDFLAGS=-g

all:$(EXE)

$(EXE):$(OBJS)
	g++ -o $@ $(OBJS) $(LDFLAGS) $(LIBS)

clean:
	-@ rm -f *.o $(EXE)

vpath %.cpp ../utillib/base
vpath %.c ../utillib/include
