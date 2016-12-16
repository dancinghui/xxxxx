#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0] + "/../")
print sys.path
from spider.httpreq import SpeedControlRequests


class DetectIds(SpeedControlRequests):
    def __init__(self, url_template, low_id):
        SpeedControlRequests.__init__(self)
        self._url_template = url_template
        self._low_id = low_id
        self.latest_id = None
        # self.load_proxy("proxy", True)

    def run(self):
        for _id in xrange(self._low_id, 31226195):

            url = self._url_template.format(_id)
            res = self.with_sleep_requests(url, 0.05)
            if res.code == 200:
                self.latest_id = _id
            else:
                print "job not exists: {}".format(url)


if __name__ == '__main__':
    dt = DetectIds("http://www.wealink.com/zhiwei/view/{}/", 30926521)
    try:
        dt.run()
    except KeyboardInterrupt as e:
        print "latest id: {}".format(dt.latest_id)
    except Exception as e:
         print "latest id: {}".format(dt.latest_id)


##latest_id: 30926881
## set high id: 31000000