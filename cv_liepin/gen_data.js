var HTTP = require("q-io/http");
var fs = require("q-io/fs");
var objurl = 'http://core.pc.lietou-static.com/revs/js/common/plugins/jquery.localdata_6f102631.js';
var utils = require("./utils")

HTTP.read(objurl).then(function (resp){
	s = resp.toString('utf-8');
	s = s.replace(/};![\s\S]*/, '};');
	eval(s);

	cl = LocalData.citys.list;
	robj = {}
	for (i in cl)
	{
		type = cl[i][0];
		robj[cl[i][1][0]] = {desc:cl[i][1][1], value:cl[i][1][0]}
		if (type==2)
		{
			sl = cl[i][2];
			t = robj[cl[i][1][0]];
			t.children = {}
			for (j=1; j<sl.length; ++j)
			{
				t.children[sl[j][0]] = {desc:sl[j][1], value:sl[j][0]}
			}
		}
	}
	utils.adjust(robj);
	ind_obj = []
	for(i in LocalData.industry)
	{
		v = LocalData.industry[i][1];
		for (k in v)
		{
			ind_obj.push([v[k][0], v[k][1]]);
		}
	}
	content = "#!/usr/bin/env python\n# -*- coding:utf8 -*-\n\n";
	content += "cities="+JSON.stringify(robj)+"\n";
	content += "industries="+JSON.stringify(ind_obj)+"\n";
	return fs.write('qdata.py', content);
}).then(function (f){
	console.log("OK:"+f);
}, function(err){
	console.log("error: "+err);
});
