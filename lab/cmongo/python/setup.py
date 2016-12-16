from distutils.core import setup, Extension
import os

sources = ['cpagestore.cpp', '../pagestorebase.cpp', '../pagestore.cpp', '../rbtdb.cpp']
include_dirs=["../../utillib/include", "../../utillib", "../../shared", '../../shared/jansson']

if os.name == 'nt':
    include_dirs.extend(["E:/work/util/inc_win", "E:\work\down\mongo-c-driver-1.3.0\src\mongoc",
        'E:/work/down/mongo-c-driver-1.3.0/src/libbson/src/bson'])
    module1 = Extension('cpagestore', sources=sources,
        library_dirs = ["E:/work/util/lib64", "../../shared", "E:/work/down/mongo-c-driver-1.3.0/src/x64/Release"],
        libraries=['libeay32', 'shared', 'gdi32', 'user32', 'advapi32', 'mongoc'],
        define_macros=[('_CRT_SECURE_NO_WARNINGS',1)],
        include_dirs=include_dirs,
        extra_compile_args=['-EHsc'] )
else:
    include_dirs.extend(["/usr/local/include/libbson-1.0", "/usr/local/include/libmongoc-1.0",
        "/usr/local/include", "/opt/local/include"])

    libraries = ['shared','crypto', 'bson-1.0', 'mongoc-1.0']
    module1 = Extension('cpagestore', libraries=libraries, sources=sources, include_dirs=include_dirs,
        library_dirs=['../../shared'],
        extra_compile_args=[ '-std=c++11', '-fvisibility=hidden', '-Wno-unused-local-typedefs'],
        extra_link_args=['-g'])

setup(name = 'cpagestore',
       version = '1.0',
       description = 'Do pagestore in C++',
       ext_modules = [module1])
