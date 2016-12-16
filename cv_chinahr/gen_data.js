var HTTP = require("q-io/http");
var fs = require("q-io/fs");
var cityurl = 'http://static.chinahr.com/themes/chinahr/js/selector/city.js';
var industryurl = 'http://static.chinahr.com/themes/chinahr/js/selector/industry.js';
var joburl = 'http://static.chinahr.com/themes/chinahr/js/selector/job.js';


var Utils = {
	translate_cc:function(catelogsCity){
		rootobj = {};
		for (var depth=1; depth<3; ++depth)
		{
			dcount = 0;
			for (i in catelogsCity)
			{
				c = catelogsCity[i];
				oo = c[5].split(/,/);
				if (oo.length == depth)
				{
					++ dcount;
					o = rootobj;
					pathlist = oo;
					ep = pathlist.pop();
					for (ip in pathlist)
					{
						o = o[pathlist[ip]].children;
						o.length;
					}
					o[ep] = {desc:c[0], value:c[5], children:{}};
				}
			}
			if (dcount==0) break;
		}
		for (k in rootobj)
			this.adjust(rootobj[k]);
		return rootobj;
	},
	adjust:function(obj){
		var klen = 0;
		for (k in obj.children){++klen;}
		if (klen == 0) {obj.children = undefined; return;}
		if (klen == 1)
		{
			if (obj.children[0] == undefined)
				obj.children = undefined;
			else
				obj.children = obj.children[0].children;
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
			c += 1;
		}
		return c;
	},
	firstlevel : function(obj){
	    newcd = []
	    for (k in rootobj)
	    {
	        newcd.push( [ obj[k].value, obj[k].desc ] );
    	}
    	return newcd;
	}
}

outs = "#!/usr/bin/env python\n# -*- coding:utf8 -*-\n\n"

HTTP.read(cityurl).then(function (resp){
	s = resp.toString('utf-8');
	eval(s);
	catelogsCity.pop();
	catelogsCity.pop();
	catelogsCity.pop();
	rootobj = Utils.translate_cc(catelogsCity);
	newcd = Utils.firstlevel(rootobj)
	outs += "city_data = " + JSON.stringify(newcd, undefined, 0) + "\n";
	return HTTP.read(industryurl);
}).then(function (r){
	s = r.toString('utf-8');
	eval(s);
	ro = Utils.translate_cc(catelogsIndustry);
	ro = Utils.firstlevel(ro);
	outs += "industry_data = " +JSON.stringify(ro)+ "\n";
	return HTTP.read(joburl);
}).then(function (r){
	s = r.toString('utf-8');
	eval(s);
	ro = Utils.translate_cc(catelogsJob);
	ro = Utils.firstlevel(ro);
	outs += "job_data = " + JSON.stringify(ro) + "\n";
	return fs.write("qdata.py", outs);
}).then(function (f){
	console.log("OK:"+f);
}, function(err){
	console.log("error: "+err);
});
