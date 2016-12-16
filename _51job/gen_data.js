var HTTP = require("q-io/http");
var fs = require("q-io/fs");
var iconvlite = require('iconv-lite');
var utils = require("../_liepin.cv/utils");


var areaurl = 'http://js.51jobcdn.com/in/js/2009/jobarea_array_c.js?20151118';
var infourl = 'http://js.51jobcdn.com/in/js/2009/merge_search_data_c.js?20140825';
var indturl = 'http://js.51jobcdn.com/in/js/2009/indtype_array_c.js?20140825';

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
    rs = iconvlite.decode(resp, 'GBK');
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
	        area[pkey].children = area[pkey].children || {};
	        area[pkey].children[ni] = {desc:ja[i], value:i};
	    }
	}

	outs += "jobarea=" + JSON.stringify(area) + "\n";
    return HTTP.read(indturl);
}).then(function (resp){
    var rs = iconvlite.decode(resp, 'GBK');
    eval(rs);
    idts = []
    for (i in it)
    {
        idts.push([i, it[i]]);
    }
    outs += "industrytype = " + JSON.stringify(idts) + "\n";
    return HTTP.read(infourl);
}).then(function (resp){
    rs = iconvlite.decode(resp, 'GBK');
    eval(rs);

    var appendo = function(name, v){
        outs += name + " = " + JSON.stringify(trans(v, "--请选择--")) + "\n";
    }

    outs += "\n";
    appendo("cotype", d_search_cotype);
    appendo("degreefrom", d_search_degreefrom);
    appendo("companysize", d_search_companysize);
    appendo("workyear", d_search_workyear);
    appendo("issuedate", d_search_issuedate);
    return fs.write('qdata.py', outs);
}).then(function (f){
    //console.log(outs);
	console.log("OK");
}, function(err){
	console.log("error: "+err);
});
