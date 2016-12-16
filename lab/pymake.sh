#!/bin/bash -e

pushd shared
if [ "$REMAKE" = "1" ] ; then
	make clean
fi
make
popd

pushd cutil
if [ "$REMAKE" = "1" ] ; then
	rm -fr build
fi
python setup.py build
$SUDO python setup.py install
popd

pushd cmongo/python
if [ "$REMAKE" = "1" ] ; then
	rm -fr build
fi
python setup.py build
$SUDO python setup.py install
popd
