CFLAGS=-I../utillib -I../utillib/include -I/opt/local/include -I../cutil
CXXFLAGS=$(CFLAGS) -std=c++11
LIBS=-lcrypto -lpthread

vpath %.cpp ../utillib/base ../utillib/crypt ../cutil
vpath %.c ../utillib/include

all:getqqpwd

clean:
	rm -f *.o *~ getqqpwd

getqqpwd:getqqpwd.o qqptlogin.o sutil.o HelperFuncs.o base64.o tea.o cryptmisc.o cptfuncs.o
	g++ -o $@ $^ $(LDFLAGS) $(LIBS)
