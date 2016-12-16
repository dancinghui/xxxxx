var HTTP = require("q-io/http");
var fs = require("q-io/fs");
var iconvlite = require('iconv-lite');
var utils = require("../cv_liepin/utils");

var url = 'http://img01.zhaopin.cn/2012/js/arrdata.js';
var outs = "#!/usr/bin/env python\n# -*- coding:utf8 -*-\n\n";

HTTP.read(url).then(function (resp){
    rs = iconvlite.decode(resp, 'utf-8');
	eval(rs);

	provs=[]
	for (i in arrCity)
	{
		if (parseInt(arrCity[i][1]) == 489)
		{
			provs.push(arrCity[i]);
		}
	}
	provs.push(['480','0','国外'])
	provs = JSON.stringify(provs)
	console.log(provs);
	outs += "provs=" + provs + "\n";
    return fs.write('qdata.py', outs);
}).then(function (f){
	console.log("OK");
}, function(err){
	console.log("error: "+err);
});

