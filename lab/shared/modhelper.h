#pragma once
#ifdef __APPLE__
#include <Python/Python.h>
#else
#include <Python.h>
#endif

#ifdef _WIN32
# define PYM_VISIBLE //__declspec(dllexport)
#else
# define PYM_VISIBLE __attribute__ ((visibility ("default")))
#endif

namespace pycall_util
{
	typedef intptr_t (*anycfunc_t)(intptr_t ,...);
	template <class FUNC, int N>
	struct get_c_func_helper;

	template <class FUNC>
	struct get_c_func_helper < FUNC, sizeof(void*) >
	{
		static anycfunc_t get(FUNC funcptr)
		{
			return ((anycfunc_t*)(&funcptr))[0];
		}
	};

#if defined(__amd64__) || defined(_M_AMD64)
	//on x64, windows, mac, linux all support this hack. Currently I don't care other OSes.
	template <class FUNC>
	struct get_c_func_helper < FUNC, 2*sizeof(void*) >
	{
		static anycfunc_t get(FUNC funcptr)
		{
			anycfunc_t f_ = ((anycfunc_t*)(&funcptr))[0];
			anycfunc_t f1_ = ((anycfunc_t*)(&funcptr))[1];
			if (f1_ != NULL)
			{
				return NULL;
			}
			return f_;
		}
	};

#elif defined(__APPLE__) && defined(__i386__)
    template <class FUNC>
    struct get_c_func_helper < FUNC, 2*sizeof(void*) >
    {
        static anycfunc_t get(FUNC funcptr)
        {
            anycfunc_t f_ = ((anycfunc_t*)(&funcptr))[0];
            anycfunc_t f1_ = ((anycfunc_t*)(&funcptr))[1];
            if (f1_ != NULL)
            {
                return NULL;
            }
            return f_;
        }
    };

#endif

	template <class FUNC>
	anycfunc_t get_c_func(FUNC funcptr)
	{
		return get_c_func_helper<FUNC, sizeof(FUNC)>::get(funcptr);
	}
}

struct PyTypeObjectExt : PyTypeObject
{
	intptr_t this_;
};

class PythonMethodDefs
{
public:
	typedef pycall_util::anycfunc_t anycfunc_t;

	enum IR_FLAGS{
		IRFLAG_EMPTY=0,
		IRFLAG_THIS=1,
		IRFLAG_THAT=2,
		IRFLAG_TAHT_NEW = 3,
	};
	struct info_reg{
		PyCFunction pyf;
		anycfunc_t funcptr;
		const char * argsdesc;
		unsigned int flags;
		void * that;
		void* (*that_new)();
		void (*that_del)(void * that);
	};

protected:
	vector<PyMethodDef> m_methods;
private:
	map<int, info_reg> m_methods_info;

private:
	static PythonMethodDefs * find_and_check(PyObject * self, int index);
	PyObject * callit(info_reg * r, PyObject * self, PyObject * args) const;
	bool add_method_internal(int N, const char * name, const char * doc, int argtype, info_reg & ir);

	template <int N>
	static PyObject * callit(PyObject * self, PyObject * args)
	{
		PythonMethodDefs * this_ = find_and_check(self, N);
		if (!this_) return NULL;
		auto it = this_->m_methods_info.find(N);
		return this_->callit(&it->second, self, args);
	}
public:
	PythonMethodDefs()
	{
		PyMethodDef md = {0};
		m_methods.push_back(md);
	}

	bool add_method_raw(const char * name, const char * doc, PyCFunction pyf, int argtype=METH_VARARGS)
	{
		int c = __COUNTER__;
		(void)c;
		info_reg ir = { 0 };
		ir.pyf = pyf;
		return add_method_internal(0, name, doc, argtype, ir);
	}
	/*//////////////////////////////////////////////////////
	// argsdesc 是返回值及参数列表，如vi，表示返回void，参数为int
	// 详见 https://docs.python.org/2/c-api/arg.html
	// 反回值调用buildvar，参数是调parsevar.
	// 注意：为处理返回值方便，加入了几个参数：
	// F: 表示返回值是动态分配的，需要调用free释放。
	// v: 表示返回值是void，python返回None
	// !: 表示返回值是bool，python返回True或False
	///////////////////////////////////////////////////*////
	template <int N, class FUNC>
	bool add_method(const char * name, const char * doc, FUNC funcptr, const char * argsdesc)
	{
		static_assert(N>0, "N must greater than 0");
		PyCFunction f = &PythonMethodDefs::callit<N>;
		anycfunc_t f_ = reinterpret_cast<anycfunc_t>(funcptr);
		info_reg ir = { 0 };
		ir.pyf = f;
		ir.funcptr = f_;
		ir.argsdesc = argsdesc;
		return add_method_internal(N, name, doc, METH_VARARGS, ir);
	}

	template <int N, class FUNC>
	bool add_this_method(const char * name, const char * doc, FUNC funcptr, const char * argsdesc)
	{
		static_assert(N>0, "N must greater than 0");
		PyCFunction f = &PythonMethodDefs::callit<N>;
		anycfunc_t f_ = pycall_util::get_c_func(funcptr);
		if (!f_) fprintf(stderr, "add class member %s failed: must be simple class!\n", name);
		info_reg ir = { 0 };
		ir.pyf = f;
		ir.funcptr = f_;
		ir.argsdesc = argsdesc;
		ir.flags = IRFLAG_THIS;
		return add_method_internal(N, name, doc, METH_VARARGS, ir);
	}

	template <int N, class T, class FUNC>
	bool add_alt_this_method(const char * name, const char * doc, FUNC funcptr, const char * argsdesc, T * that)
	{
		static_assert(N>0, "N must greater than 0");
		PyCFunction f = &PythonMethodDefs::callit<N>;
		anycfunc_t f_ = pycall_util::get_c_func(funcptr);
		if (!f_) fprintf(stderr, "add class member %s failed: must be simple class!\n", name);
		info_reg ir = { 0 };
		ir.pyf = f;
		ir.funcptr = f_;
		ir.argsdesc = argsdesc;
		ir.flags = IRFLAG_THAT;
		ir.that = that;
		return add_method_internal(N, name, doc, METH_VARARGS, ir);
	}

	template <int N, class T, class FUNC>
	bool add_newobj_method(const char * name, const char * doc, FUNC funcptr, const char * argsdesc)
	{
		static_assert(N>0, "N must greater than 0");
		PyCFunction f = &PythonMethodDefs::callit<N>;
		anycfunc_t f_ = pycall_util::get_c_func(funcptr);
		if (!f_) fprintf(stderr, "add class member %s failed: must be simple class!\n", name);
		info_reg ir = { 0 };
		ir.pyf = f;
		ir.funcptr = f_;
		ir.argsdesc = argsdesc;
		ir.flags = IRFLAG_TAHT_NEW;
		ir.that_new = &that_new_helper_t<T>::tt_new;
		ir.that_del = &that_new_helper_t<T>::tt_del;
		return add_method_internal(N, name, doc, METH_VARARGS, ir);
	}

protected:
	template <class TT>
	struct that_new_helper_t{
		static void * tt_new(){ return new TT; }
		static void tt_del(void * _) { delete (TT*)_; }
	};
};

class CPyModuleHelper : public PythonMethodDefs
{
private:
	CPyModuleHelper(){}
	CPyModuleHelper(const CPyModuleHelper & ano);

private:
	const char * m_name;
	PyObject * m_thismodule;
public:
	PyObject * m_moderr;

public:
	const char * getname()const{return m_name;}
	bool AddObject(const char * name, PyObject * type)
	{
		return PyModule_AddObject(m_thismodule, name, type) == 0;
	}
	void SetErrStr(const char * str)
	{
		return PyErr_SetString(m_moderr, str);
	}
	void SetErrStr(int code, const char * str)
	{
		PyObject * obj = Py_BuildValue("(is)", code, str);
		PyErr_SetObject(m_moderr, obj);
		Py_DECREF(obj);
	}
	bool init(const char * name, const char * doc);
	static CPyModuleHelper & GetInstance();
};

class PythonObjectFactoryBase : public PythonMethodDefs
{
protected:
	PyTypeObjectExt m_type;
	string m_fullname;
	const char * m_name;
protected:
	static void * get_this(PyObject * self);
public:
	PythonObjectFactoryBase(const char * name, const char * doc);
	bool apply();
};

template <class T>
class PythonObjectFactory : public PythonObjectFactoryBase
{
public:
	struct ObjectType{
		PyObject_HEAD
		T * realobj;
	};

private:
	static void dealloc(PyObject * self)
	{
		ObjectType* obj_ = (ObjectType*)self;
		if (obj_->realobj){
			delete obj_->realobj;
			obj_->realobj = 0;
		}
		self->ob_type->tp_free(self);
	}
	static PyObject* _new(PyTypeObject * type, PyObject* args, PyObject* kwds)
	{
		ObjectType * self = (ObjectType*) type->tp_alloc(type, 0);
		if (!self) return NULL;

		self->realobj = new T;
		if (! self->realobj->init(args, kwds))
		{
			dealloc( (PyObject*) self);
			return NULL;
		}
		return (PyObject*)self;
	}
public:
	static T * get_this(PyObject *self) { return (T*)PythonObjectFactoryBase::get_this(self); }
	PythonObjectFactory(const char * name, const char * doc) : PythonObjectFactoryBase(name,doc)
	{
		m_type.tp_basicsize = sizeof(ObjectType);
		m_type.tp_dealloc = dealloc;
		m_type.tp_new = _new;
	}
};

template <class T>
class CPyFuncs : public T
{
protected:
	void * build_s(const char * s, size_t len)
	{
		if (len == (size_t)-1) len = strlen(s);
		return Py_BuildValue("s#", s, len);
	}
	void on_error(int code, const char * errstr)
	{
		CPyModuleHelper::GetInstance().SetErrStr(code, errstr);
	}
};
