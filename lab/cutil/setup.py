from distutils.core import setup, Extension
import os

sources=['cutil.cpp', 'fhtml.cpp',  'gfuncs.cpp', 'pyjobq.cpp', 'jobq.cpp', 'qqptlogin.cpp', 'kvstore.cpp']
include_dirs=["../utillib/include", "../utillib", "../shared", '../shared/jansson']

if os.name == 'nt':
    include_dirs.extend(["E:/work/util/inc_win"])
    module1 = Extension('cutil', sources=sources,
        library_dirs = ["E:/work/util/lib64", "../shared"],
        libraries=['libeay32', 'shared', 'gdi32', 'user32', 'advapi32'],
        define_macros=[('_CRT_SECURE_NO_WARNINGS',1)],
        include_dirs=include_dirs,
        extra_compile_args=['-EHsc'] )
else:
    include_dirs.extend(["/opt/local/include"])
    module1 = Extension('cutil', sources=sources, libraries=['crypto', 'shared'],
        include_dirs=include_dirs,
        library_dirs=['../shared'],
        extra_compile_args=['-std=c++11', '-g', '-fvisibility=hidden', '-Wno-unused-local-typedefs'],
        extra_link_args=['-g'] )

setup (name = 'cutil',
       version = '1.0',
       description = 'This is a cutil package',
       ext_modules = [module1])
