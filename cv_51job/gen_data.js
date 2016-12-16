var HTTP = require("q-io/http");
var fs = require("q-io/fs");
var iconvlite = require('iconv-lite');
var utils = require("../_liepin.cv/utils");

var areaurl = 'http://js.51jobcdn.com/ehire2007/js/20151117/ResumeArea_Layer.js';
var infourl = 'http://js.51jobcdn.com/ehire2007/js/20151117/DictTable.js';

var outs = "#!/usr/bin/env python\n# -*- coding:utf8 -*-\n\n";

var trans = function(obj, skipv){
    var xx = []
    for (i in obj)
    {
        if (obj[i].v && obj[i].v != skipv)
            xx.push([obj[i].k, obj[i].v])
    }
    return xx;
}

HTTP.read(areaurl).then(function (resp){
    rs = iconvlite.decode(resp, 'utf-8');
	rs = rs.replace(/}\s*\/\/主要城市数据字典[\s\S]*/, "");
	rs = rs.replace(/[\s\S]*else\s*{/, "");
	eval(rs);
	area = {}
	for (i in ja)
	{
	    ni = parseInt(i);
	    if (ni % 10000 == 0)
	    {
	        area[ni] = {desc:ja[i], value:i};
	    }
	    else
	    {
	        pkey = ni - ni%10000;
			//area[pkey].children = area[pkey].children || {};
	        //area[pkey].children[ni] = {desc:ja[i], value:i};
	    }
	}

	outs += "jobarea=" + JSON.stringify(area) + "\n";
    return HTTP.read(infourl);
}).then(function (resp){
	rs = iconvlite.decode(resp, 'utf-8');
	rs = rs.replace(/\/\/基层岗位关键字[\s\S]*/, "");
	eval(rs);

	mj = []
	for (i in ctMajorAss)
	{
		c = parseInt(ctMajorAss[i].code);
		v = ctMajorAss[i].value;
		if (c % 100 == 0)
		{
			//	$法学类|0900$
			s = '$' + v + '|' + ctMajorAss[i].code + '$';
			mj.push([s]);
		}
	}
	outs += "mj=" + JSON.stringify(mj) + "\n";
    return fs.write('qdata.py', outs);
}).then(function (f){
	console.log("OK");
}, function(err){
	console.log("error: "+err);
});
