#!/usr/bin/env python
# encoding:utf-8
import time
import os
import BaseHTTPServer
import cgi
import re
import random
from spider.runtime import Log


class ImageCodeServer(BaseHTTPServer.HTTPServer):
    def __init__(self, a, b, geimg):
        BaseHTTPServer.HTTPServer.__init__(self, a,b)
        self.geimg = geimg
        self.code = ''


class ImageCodeRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, a, b, c):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self,a,b,c)

    def log_message(self, format, *args):
        return

    def get_path(self):
        a = re.sub(r'\?.*', '', self.path)
        return a

    def do_GET(self):
        p = self.get_path()
        if p == '/':
            return self.load_page()
        if p == '/img':
            return self.load_image()
        self.do_HEAD()
        self.wfile.write('not found\n')

    def do_HEAD(self):
        self.send_response(404)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def do_POST(self):
        p = self.get_path()
        if p == '/setcode':
            return self.set_code()
        self.do_HEAD()
        self.wfile.write('not found\n')

    def load_image(self):
        rimg = self.server.geimg()
        self.send_response(200)
        self.send_header("Content-type", "image/jpg")
        self.send_header("Content-Length", str(len(rimg)))
        self.end_headers()
        self.wfile.write(rimg)

    def set_code(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type']} )
        self.server.code = form.getvalue('code', '')
        rmsg = "<h3>code %s recieved.</h3>" % self.server.code
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(rmsg)))
        self.end_headers()
        self.wfile.write(rmsg)

    def load_page(self):
        rhtml = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>get image</title>
<script type="text/javascript" src="http://mat1.gtimg.com/www/asset/lib/jquery/jquery/jquery-1.11.1.min.js"></script>
<script type="text/javascript">
function change_img()
{
	document.getElementById("img").src = "/img?a=" + Math.random();
	document.getElementById("code").focus();
	return false;
}
function cancel_code()
{
	$.post("/setcode", {code:'',type:'json'}, function(){});
	return false;
}
</script>
</head>
<body>
<form method="POST" action="/setcode">
	<img src="/img?a=$RND" border="0" id="img" />
	<a href="###" onclick="return change_img()">another image</a> <br />
	<input id="code" name="code" type="text" length="8" />
	<input type="submit" value="submit"/> <a href="###" onclick="return cancel_code()">cancel</a>
</form>
<script type="text/javascript">
$(document).ready(function(){
	$("#code").focus();
});
</script>
</body>
</html>
        """
        rhtml = re.sub(r"\$RND", str(random.random()), rhtml)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(rhtml)))
        self.end_headers()
        self.wfile.write(rhtml)


class GetImageCode(object):
    def __init__(self, port=8100):
        self.port = port
        self.code = ''

    def resolve(self, refresher):
        httpd = ImageCodeServer(('', self.port), ImageCodeRequestHandler, refresher)
        self._print_banner(httpd.server_port)
        while httpd.code == '':
            httpd.handle_request()
        httpd.server_close()
        return httpd.code

    def _print_banner(self, port):
        hostname = 'localhost'
        conn_info = os.getenv('SSH_CONNECTION') or ''
        m = re.search(r'[0-9.]+ \d+ ([0-9.]+) ', conn_info)
        if m:
            hostname = m.group(1)
        Log.error("[pid:%d]Enter image code at http://%s:%d/ " % (os.getpid(), hostname, port))


if __name__ == '__main__':
    from spider.spider import SessionRequests
    rf = SessionRequests()
    gi = GetImageCode()
    print time.asctime(), "Server Starts"
    print gi.resolve(lambda : rf.request_url('https://passport.zhaopin.com/checkcode/imgrd').content )
    print time.asctime(), "Server Stops"
