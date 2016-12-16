#!/usr/bin/env python
# -*- coding:utf8 -*-

from service.cv_contact_get.cv_51job.downloader import CV51jobDownloader
from service.cv_contact_get.cv_zhilian.downloader import CVZLDownloader
from service.cv_contact_get.common import config, read_bitArray
from flask import Flask, request, make_response, jsonify
from spider.runtime import Log

app = Flask(__name__)

CHANNEL_DOWNLOADER_MAP = {
    'cv_51job': CV51jobDownloader(),
    'cv_zhilian': CVZLDownloader(),
}


@app.route('/cvDownload', methods=['GET',])
def CVDownloadHandler():

    channel = request.args.get('channel', '')
    cvId = request.args.get('cvId','')

    if not (channel and cvId):
        return make_response(jsonify({"status": 404,'content': '', 'msg': 'need channel and cvid', 'flag': 0}))

    if channel not in CHANNEL_DOWNLOADER_MAP:
        Log.warning('channel %s has no downloader' % channel)
        return make_response(jsonify({'status':405,'content':'', 'msg':'channel %s has no downloader' % channel, 'flag': 0}))

    status, cvinfo = CHANNEL_DOWNLOADER_MAP.get(channel).download(cvId, True)

    rs = {}
    rs['status'] = status
    rs['content'] = cvinfo
    rs['msg'] = config.StatusCode.code_msg_map.get(status)
    if rs['status'] == config.StatusCode.ALREADY_IN_DB:
        flag = 1
    elif rs['status'] == config.StatusCode.CV_CLOSED:
        flag = 2
    elif rs['status'] == config.StatusCode.DOWNLOAD_RETRY_FAIL:
        flag = 3
    else:
        flag = 0

    rs['flag'] = flag
    return make_response(jsonify(rs))


@app.route('/bitconvert', methods=['GET',])
def bitconvert():
    result = {

        "flag": 0,
        "content":"",

    }
    bitstream = request.args.get('bitstream', '')
    flag, content = read_bitArray.convert_bitarray(bitstream)
    result.update({'flag': flag, 'content':content})
    return make_response(jsonify(result))

if __name__ == '__main__':
    app.run('127.0.0.1', 9527, debug=True)