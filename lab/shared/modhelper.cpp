#include "stdafx.h"
#include "modhelper.h"


namespace
{
	struct DummyObject
	{
		bool init(PyObject* args, PyObject* kwds){return false;}
	};
	intptr_t find_real_object(PyObject * self)
	{
		PythonObjectFactory<DummyObject>::ObjectType * p;
		p = (PythonObjectFactory<DummyObject>::ObjectType*)self;
		return p ? (intptr_t) p->realobj : (intptr_t)0;
	}
}

PyObject * PythonMethodDefs::callit(info_reg *r, PyObject * self, PyObject * args) const
{
	const char * tr = r->argsdesc;
	intptr_t nargs[12] = {0};
	bool freeit = false;
	intptr_t this_ = 0;

	if (*tr=='F'){freeit = true ; ++tr;}
	int n = PyArg_ParseTuple(args, (const char*)tr+1,
							 &nargs[0], &nargs[1], &nargs[2], &nargs[3], &nargs[4], &nargs[5],
							 &nargs[6], &nargs[7], &nargs[8], &nargs[9], &nargs[10], &nargs[11]);
	if (!n) return NULL;
	intptr_t rv = 0;
	if (r->flags == IRFLAG_THIS)
	{
		this_ = find_real_object(self);
		rv = (r->funcptr)(this_, nargs[0], nargs[1], nargs[2], nargs[3], nargs[4], nargs[5],
						  nargs[6], nargs[7], nargs[8], nargs[9], nargs[10], nargs[11]);
	}
	else if (r->flags == IRFLAG_THAT)
	{
		this_ = (intptr_t) r->that;
		rv = (r->funcptr)(this_, nargs[0], nargs[1], nargs[2], nargs[3], nargs[4], nargs[5],
			nargs[6], nargs[7], nargs[8], nargs[9], nargs[10], nargs[11]);
	}
	else if (r->flags == IRFLAG_TAHT_NEW)
	{
		this_ = (intptr_t) (*r->that_new)();
		rv = (r->funcptr)(this_, nargs[0], nargs[1], nargs[2], nargs[3], nargs[4], nargs[5],
			nargs[6], nargs[7], nargs[8], nargs[9], nargs[10], nargs[11]);
		//delete it later.
	}
	else
		rv = (r->funcptr)(nargs[0], nargs[1], nargs[2], nargs[3], nargs[4], nargs[5],
						  nargs[6], nargs[7], nargs[8], nargs[9], nargs[10], nargs[11]);

	PyObject * ro = NULL;
	char kv[] = {((char*)tr)[0], 0};

	if (! PyErr_Occurred())
	{
		switch (kv[0])
		{
		case 'v':
			ro = Py_None;
			Py_INCREF(ro);
			break;
		case '!':
			ro = (!!(unsigned char)rv) ? Py_True : Py_False;
			Py_INCREF(ro);
			break;
		default:
			ro = Py_BuildValue(kv, rv);
			break;
		}
	}

	if (r->flags == IRFLAG_TAHT_NEW)
		(*r->that_del)((void*)this_);
	if (freeit) free((void*)rv);
	return ro;
}

bool PythonMethodDefs::add_method_internal(int N, const char * name, const char * doc, int argtype, info_reg & ir)
{
	PyMethodDef md = {name, ir.pyf, argtype, doc};
	if (N > 0)
	{
		if (m_methods_info.find(N) != m_methods_info.end())
		{
			fprintf(stderr, "failed to register method, duplicate arg:N=%d\n", N);
			return false;
		}
		m_methods_info[N] = ir;
	}
	m_methods.insert(m_methods.begin()+m_methods.size()-1, md);
	return true;
}

PythonMethodDefs * PythonMethodDefs::find_and_check(PyObject * self, int index)
{
	PythonMethodDefs * r = 0;
	if (!self)
	{
		//assume global methods.
		r = &CPyModuleHelper::GetInstance();
	}
	else
	{
		PyTypeObjectExt * tp_ = (PyTypeObjectExt*)(self->ob_type);
		r = (PythonMethodDefs*) tp_->this_;
	}

	if (!r || r->m_methods_info.find(index) == r->m_methods_info.end())
	{
		char bm[100];
		sprintf(bm, "bad method %p:%d", self, index);
		CPyModuleHelper::GetInstance().SetErrStr(bm);
		return NULL;
	}

	return r;
}

/////////////////////////////////////////////////////////////////////
///             Module Helper Funcs.                         ////////
/////////////////////////////////////////////////////////////////////

bool CPyModuleHelper::init(const char * name, const char * doc)
{
	m_name = name;
	m_thismodule = Py_InitModule3(name, &m_methods[0], doc);
	if (!m_thismodule || !PyModule_Check(m_thismodule))
		return false;
	string merr = name;
	merr += ".error";

	m_moderr = PyErr_NewException((char*)merr.c_str(), NULL, NULL);
	Py_INCREF(m_moderr);
	PyModule_AddObject(m_thismodule, "error", m_moderr);
	return true;
}

CPyModuleHelper & CPyModuleHelper::GetInstance()
{
	static CPyModuleHelper themh;
	return themh;
}


/////////////////////////////////////////////////////////////////////
///             Object Helper Funcs.                         ////////
/////////////////////////////////////////////////////////////////////
PythonObjectFactoryBase::PythonObjectFactoryBase(const char * name, const char * doc)
{
	PyTypeObject nontype = {
		PyObject_HEAD_INIT(NULL)
	};
	memcpy(&m_type, &nontype, sizeof(m_type));
	CPyModuleHelper & mh = CPyModuleHelper::GetInstance();
	m_fullname = mh.getname();
	m_fullname += ".";
	m_fullname += name;
	m_name = name;
	m_type.tp_name = m_fullname.c_str();

	m_type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
	m_type.tp_doc = doc;
	m_type.this_ = (intptr_t) this;
}

bool PythonObjectFactoryBase::apply()
{
	CPyModuleHelper & mh = CPyModuleHelper::GetInstance();
	m_type.tp_methods = &m_methods[0];

	if (PyType_Ready(&m_type) < 0)
		return false;
	Py_INCREF(&m_type);
	return mh.AddObject(m_name, (PyObject*) &m_type);
}

void * PythonObjectFactoryBase::get_this(PyObject * self)
{
	return (void*) find_real_object(self);
}
