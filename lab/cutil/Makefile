test:
	find . -name '*.so' | xargs rm -f
	python setup.py build
	find . -name '*.so' | xargs -I {} cp {} .
	./test.py

all:
	rm -fr build/
	python setup.py install
	./test.py
