#!/usr/bin/env python
# -*- coding:utf8 -*-
# all the imports
import re
import sqlite3
from flask import Flask, request, session, jsonify

# configuration
DATABASE = 'flaskr.db'
DEBUG = True
USERNAME = 'ipin'
PASSWORD = 'ipin1234'
PORT = 9000
IP_TABLE = 't_ip'
IP_TABLE_SERVER_COLUMN = 'c_server'
IP_TABLE_IP_COLUMN = 'c_ip'
HOST = '192.168.1.251'
SECRET_KEY = 'LuJAxGaUMqnDOARGzY9zIe0Rd41opkL7'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


def get_db():
    return sqlite3.connect(app.config['DATABASE'])


def valid_login(username, password):
    return username == USERNAME and password == PASSWORD


def log_the_user_in(username, password):
    app.logger.info('user %s login', username)
    session[username] = username
    return 'Hello %s' % username


def init_db():
    db = get_db()
    db.execute('''CREATE TABLE %s(
    %s TEXT PRIMARY KEY NOT NULL,
    %s TEXT NOT NULL);
    ''' % (IP_TABLE, IP_TABLE_SERVER_COLUMN, IP_TABLE_IP_COLUMN))
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()


def update_key(key, value):
    app.logger.info('update %s to %s', key, value)
    db = get_db()
    db.execute('INSERT OR REPLACE INTO %s(%s,%s) VALUES("%s","%s")' %
               (IP_TABLE, IP_TABLE_IP_COLUMN, IP_TABLE_SERVER_COLUMN, value,
                key))
    db.commit()


def get_value(key):
    db = get_db()
    c = db.execute('SELECT * FROM %s WHERE %s="%s"' % (IP_TABLE, IP_TABLE_SERVER_COLUMN, key))
    if c:
        ips = {}
        for row in c:
            ips[row[0]] = row[1]
        return ips
    return None


def get_all():
    db = get_db()
    c = db.execute('SELECT * FROM %s ' % IP_TABLE)
    ips = {}
    for row in c:
        ips[row[0]] = row[1]
    return ips


#
#
# #@app.route('/login', methods=['POST', 'GET'])
# def login():
#     if request.method == 'POST':
#         if valid_login(request.form['username'], request.form['password']):
#             return log_the_user_in(request.form['username'], request.form['password'])
#         else:
#             return 'error: invalid username/password'
#     else:
#         return '''
#         <html>
#             <form action method=POST>
#                 <p><input type=text maxlength=50 name=username>
#                 <p><input type=password maxlength=50 name=password>
#                 <p><input type=submit value=Login>
#             </form>
#         </html>
#         '''
#
#
# #@app.route('/logout')
# def logout():
#     session.pop(request.args.get('username'))
#     return 'ok'


@app.route('/')
def find():
    key = request.args.get('key')
    if not key or key == '':
        ips = get_all()
    else:
        ips = get_value(key)
    if ips is not None and ips != {}:
        return jsonify({'result': ips, 'code': 1})
    return jsonify({'code': 0, 'result': {}})


@app.route('/update', methods=['POST'])
def update():
    encrypt = request.form['encrypt']
    if encrypt != SECRET_KEY:
        return 'error: Permission denied,%s' % encrypt

    key = request.form['key']
    value = request.form['value']
    if not key or not value:
        return 'error: key and value is required'

    if not re.match('\d{1,4}\.\d{1,4}\.\d{1,4}\.\d{1,4}(:\d+)?$', value):
        return 'error: invalid value %s' % value
    else:
        update_key(key, value)
        return 'ok'


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
