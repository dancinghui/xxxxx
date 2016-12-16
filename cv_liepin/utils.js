var utils = {
	adjust:function(obj){
	    var keys = []
		var klen = 0;
		for (k in obj.children){++klen; keys.push(k); }
		if (klen == 0) {obj.children = undefined; return;}
		if (klen == 1)
		{
			if (obj.children[keys[0]] == undefined)
				obj.children = undefined;
			else
				obj.children = obj.children[keys[0]].children;
			if (obj.children)
			    this.adjust(obj.children);
		}
		else
		{
			for (k in obj.children)
			{
				this.adjust(obj.children[k]);
			}
		}
	},
	count: function(obj){
		var c = 0;
		for (k  in obj)
		{
			if (obj[k].children)
				c += this.count(obj[k].children);
			else
				c += 1;
		}
		return c;
	},
}

module.exports = utils;
