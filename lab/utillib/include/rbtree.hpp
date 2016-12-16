#pragma once
#define _INC_RBTREE_HPP_

template <class RBItemPtr>
class CRBTreeBase{
public:
	enum COLOR
	{
		COLOR_RED,
		COLOR_BLACK,
	};
	struct RBItemX
	{
		RBItemPtr parent_, left_, right_;
		unsigned int one : 1;
		unsigned int zero : 1;
		unsigned int color : 1;
		unsigned int flags_avail : 29;

		unsigned char getColor()
		{
			//clang bugly gives compare this a warning.
			void * this_ = this;
			return this_ ? color : COLOR_BLACK;
		}
		void set_left(RBItemX * l, void * env)
		{
			left_.set(l, env);
			if (l) l->parent_.set(this, env);
		}
		void set_right(RBItemX * r, void * env)
		{
			right_.set(r, env);
			if (r) r->parent_.set(this, env);
		}
	};
};

struct RBItemXPtr
{
	uint32_t value_;

	CRBTreeBase<RBItemXPtr>::RBItemX * v(void * env)
	{
		if (value_ == 0) return 0;
		return (CRBTreeBase<RBItemXPtr>::RBItemX*) ((char*)env + ((intptr_t)value_ << 3));
	}
	void set(CRBTreeBase<RBItemXPtr>::RBItemX * p, void *env)
	{
		if (p == 0)
			value_ = 0;
		else
			value_ = (uint32_t) (((char*)p - (char*)env) >> 3);
	}
};

#define left left_.v(env)
#define right right_.v(env)
#define parent parent_.v(env)

template <class RBItemPtr>
class CRBTreeTemp
{
protected:
	RBItemPtr m_root_;
public:
	typedef typename CRBTreeBase<RBItemPtr>::COLOR COLOR;
	typedef typename CRBTreeBase<RBItemPtr>::RBItemX RBItemX;
	typedef int(*compare_func)(const RBItemX *a, const RBItemX *b);
	typedef void (*unalloc_func)(void *itemptr);

	CRBTreeTemp()
	{
		static_assert(sizeof(*this) == sizeof(RBItemPtr), "this class should be a simple bridge.");
		m_root_.set(0, 0);
	}
	void clear(unalloc_func unalloc, void * env)
	{
		del_x(m_root_.v(env), unalloc, env);
		m_root_.set(0, 0);
	}

protected:
	RBItemX * TREE_MINIMUM(RBItemX * x, void * env)
	{
		RBItemX * y;
		while ((y = x->left) != NULL) x = y;
		return x;
	}

	template <class C>
	RBItemX * FindLB(const RBItemX * itm, const C& cmp, void * env)
	{
		RBItemX * x = m_root_.v(env);
		RBItemX * y = 0;
		while (x != NULL)
		{
			y = x;
			int k = cmp(itm, x);
			x = (k <= 0) ? x->left : x->right;
		}
		return y;
	}

	RBItemX * next_item(RBItemX * p, void * env)
	{
		if (p == 0) return 0;
		if (p->parent == 0)
		{
			if (p->right != 0)
				return TREE_MINIMUM(p->right, env);
			else
				return 0;
		}
		if (p->parent->left == p)
		{
			if (p->right)
				return TREE_MINIMUM(p->right, env);
			else
				return p->parent;
		}
		MYASSERT(p->parent->right == p);
		for (RBItemX * p1 = p->parent; p1->parent;)
		{
			if (p1 == p1->parent->right)
				p1 = p1->parent;
			else
				return p1->parent;
		}
		return 0;
	}

private:
	void del_x(RBItemX * p, unalloc_func unalloc, void * env)
	{
		if (!p) return;
		del_x(p->left, unalloc, env);
		del_x(p->right, unalloc, env);
		unalloc(p);
	}

	RBItemX * sibling(RBItemX * x, void * env)
	{
		MYASSERT(x->parent);
		return sibling(x, x->parent, env);
	}

	RBItemX * sibling(RBItemX * x, RBItemX * xp, void * env)
	{
		RBItemX * r;
		if (xp->left == x)
			r = xp->right;
		else
			r = xp->left;
		MYASSERT(r != x);
		return r;
	}
	RBItemX * one_child(RBItemX * x, void * env)
	{
		MYASSERT(x->left == NULL || x->right == NULL);
		if (x->left)
			return x->left;
		else
			return x->right;
	}
	void set_root(RBItemX * x, void * env)
	{
		m_root_.set(x, env);
		if (x) x->parent_.set(0, env);
	}
	void replace_item(RBItemX * xp, RBItemX * x, RBItemX * nx, void * env)
	{
		//repalce node x to nx.
		MYASSERT((xp == NULL && m_root_.v(env) == x) || xp->left == x || xp->right == x);
		if (xp == NULL)
		{
			if (m_root_.v(env) == x)
				set_root(nx, env);
			else
				abort();
		}
		else if (xp->left == x)
			xp->set_left(nx, env);
		else if (xp->right == x)
			xp->set_right(nx, env);
		else
			abort();
	}

	void rotate(RBItemX * x, void * env, bool isdanger = false)
	{
		MYASSERT(x != 0);
		MYASSERT(x->parent != NULL);
		MYASSERT(isdanger || x->color == COLOR::COLOR_RED);
		// left or right rotate in one function.
		//     xp            --left-->           Xp
		//  a     x                           X   c
		//       b c        <-right--        a b
		RBItemX * xp = x->parent;
		RBItemX * xpp = xp->parent;
		if (x == xp->right)
		{
			RBItemX * b = x->left;
			xp->set_right(b, env);
			x->set_left(xp, env);
		}
		else
		{
			RBItemX * b = x->right;
			xp->set_left(b, env);
			x->set_right(xp, env);
		}
		replace_item(xpp, xp, x, env);
		int a = xp->color;
		xp->color = x->color;
		x->color = a;
	}

	//insert-fixup
	void InsertFixup(RBItemX * z, void * env)
	{
		RBItemX * zp = z->parent;
		if (zp == NULL)
		{
			z->color = COLOR::COLOR_BLACK;
			return;
		}
		if (zp->getColor() == COLOR::COLOR_BLACK)
			return;

		RBItemX * zpp = zp->parent;
		RBItemX * s = sibling(zp, env);
		if (s->getColor() == COLOR::COLOR_RED)
		{
			//case 1
			zp->color = COLOR::COLOR_BLACK;
			s->color = COLOR::COLOR_BLACK;
			zpp->color = COLOR::COLOR_RED;
			return InsertFixup(zpp, env);
		}

		if ((zp->right == z && zpp->right == s) || (zp->left == z && zpp->left == s))
		{
			//case 2
			rotate(z, env, true);
			z = zp;
			zp = z->parent;
			MYASSERT(zp->parent == zpp);
		}

		if ((zp->right == z && zpp->left == s) || (zp->left == z && zpp->right == s))
		{
			//case 3
			rotate(zp, env, false);
		}
		else
		{
			MYASSERT("unknown case");
			abort();
		}
	}

	void RBDeleteFixup(RBItemX * x, RBItemX * xp, void * env)
	{
		if (xp == NULL)
		{
			set_root(x, env);
			if (x) x->color = COLOR::COLOR_BLACK;
			return;
		}

		//x may be null, xp is x->parent.
		RBItemX * s = sibling(x, xp, env);
		//now s is x's sibling.
		if (s->color == COLOR::COLOR_RED)
		{
			//case 1
			rotate(s, env, false);
			//xp is still xp.
			MYASSERT(xp->left == x || xp->right == x);
			s = sibling(x, xp, env);
			MYASSERT(s->color == COLOR::COLOR_BLACK);
		}

		if (s->left->getColor() == COLOR::COLOR_BLACK && s->right->getColor() == COLOR::COLOR_BLACK)
		{
			//case 2.
			s->color = COLOR::COLOR_RED;
			x = xp;
			xp = x->parent;
			if (x->color == COLOR::COLOR_RED)
				x->color = COLOR::COLOR_BLACK;
			else
			{
				//x->color is COLOR_BLACK
				if (xp)
					return RBDeleteFixup(x, xp, env);
				//otherwise x is root, nothing to do.
				MYASSERT(m_root_.v(env) == x);
			}
			//case 2 won't fall back to 3 or 4. case 1 does.
			return;
		}

		if (s->left->getColor() == COLOR::COLOR_RED && x == xp->left)
		{
			//case 3
			rotate(s->left, env, false);
			s = sibling(x, xp, env);
		}
		else if (s->right->getColor() == COLOR::COLOR_RED && x == xp->right)
		{
			//case 3
			rotate(s->right, env, false);
			s = sibling(x, xp, env);
		}

		//the final case.
		if (s->left->getColor() == COLOR::COLOR_RED && x == xp->right)
		{
			rotate(s, env, true);
			s->left->color = COLOR::COLOR_BLACK;
		}
		else if (s->right->getColor() == COLOR::COLOR_RED && x == xp->left)
		{
			rotate(s, env, true);
			s->right->color = COLOR::COLOR_BLACK;
		}
		else
		{
			MYASSERT("bug");
			abort();
		}
	}

	RBItemX * RBDelete(RBItemX * z, void * env)
	{
		//     yz          or             z
		//   x                          a    d
		//                                 yb  e
		//                                  cx
		RBItemX *y, *x, *yp;

		if (z->left == NULL || z->right == NULL)
		{
			y = z;
		}
		else
		{
			y = TREE_MINIMUM(z->right, env);
		}
		x = one_child(y, env);
		yp = y->parent;
		replace_item(yp, y, x, env);

		if (y != z)
		{
			//原来放z的地方要换成放y
			y->set_left(z->left, env);
			y->set_right(z->right, env);
			replace_item(z->parent, z, y, env);
			//keep color.
			int color = y->color;
			y->color = z->color;
			z->color = color;

			//    z
			//  a   yb
			if (yp == z) yp = y;
			y = z;
		}

		//fixup x.
		MYASSERT(x == NULL || x->color == COLOR::COLOR_RED);
		if (x == NULL)
		{
			if (y->color == COLOR::COLOR_BLACK)
			{
				//deleted a black item, fixup needed.
				//now yp is parent of this deleted item.
				RBDeleteFixup(x, yp, env);
			}
		}
		else
			x->color = COLOR::COLOR_BLACK;
		return y;
	}

public:
	template <class C>
	bool Insert(RBItemX * z, const C& cmp, void * env)
	{
		RBItemX * y = NULL;
		RBItemX * x = m_root_.v(env);
		while (x != NULL)
		{
			y = x;
			int k = cmp(z, x);
			if (k == 0)
			{
				return false;
			}
			x = (k < 0) ? x->left : x->right;
		}

		z->left_.set(0, env);
		z->right_.set(0, env);
		z->color = COLOR::COLOR_RED;
		z->one = 1;
		z->zero = 0;

		if (y == NULL)
		{
			set_root(z, env);
			z->color = COLOR::COLOR_BLACK;
		}
		else
		{
			int c = cmp(z, y);
			if (c < 0)
				y->set_left(z, env);
			else
				y->set_right(z, env);
			InsertFixup(z, env);
		}
		return true;
	}

	template <class C>
	RBItemX * Delete(const RBItemX * itm, const C& cmp, void * env)
	{
		RBItemX * x = m_root_.v(env);
		while (x != NULL)
		{
			int k = cmp(itm, x);
			if (k == 0)
			{
				RBItemX * p = RBDelete(x, env);
				return p;
			}
			x = (k < 0) ? x->left : x->right;
		}
		return 0;
	}

	template <class C>
	RBItemX * Find(const RBItemX * itm, const C& cmp, void * env)
	{
		RBItemX * x = m_root_.v(env);
		while (x != NULL)
		{
			int k = cmp(itm, x);
			if (k == 0) return x;
			x = (k < 0) ? x->left : x->right;
		}
		return 0;
	}

	bool check(void * env)
	{
		RBItemX  * root = m_root_.v(env);
		if (root == NULL) return true;
		MYASSERT(root->color == COLOR::COLOR_BLACK);
		if (root->color != COLOR::COLOR_BLACK)
			return false;
		int maxbh = 0;
		return check_(root, env, maxbh, 0);
	}
private:
	bool check_(RBItemX *a, void * env, int & maxd, int level)
	{
		if (a == 0)
		{
			if (maxd == 0)
			{
				maxd = level;
				return true;
			}
			else
			{
				MYASSERT(maxd == level);
				return maxd == level;
			}
		}
		if ( (a->left == 0 || a->left->parent == a) && (a->right==0 || a->right->parent == a));
		else return false;

		if (a->color == COLOR::COLOR_RED)
		{
			if (a->left->getColor() == COLOR::COLOR_BLACK && a->right->getColor() == COLOR::COLOR_BLACK)
				;
			else
			{
				MYASSERT(!"red->red");
				return false;
			}
		}

		if (a->color == COLOR::COLOR_BLACK) ++level;
		return check_(a->left, env, maxd, level) &&
			check_(a->right, env, maxd, level);
	}
};

#undef parent
#undef left
#undef right
