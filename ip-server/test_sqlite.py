#!/usr/bin/env python
# -*- coding:utf8 -*-
import unittest

import sqlite3

IP_TABLE = 't_ip'
IP_TABLE_SERVER_COLUMN = 'c_server'
IP_TABLE_IP_COLUMN = 'c_ip'


class SQLite3:
    def __init__(self):
        self.database = 'ip.db'
        self.table = 'table_ip'

    def get_db(self):
        return sqlite3.connect(self.database)

    def create_table(self):
        db = self.get_db()
        db.execute('DROP TABLE IF EXISTS %s' % IP_TABLE)
        db.commit()
        sql = '''CREATE TABLE %s(
    %s TEXT PRIMARY KEY NOT NULL,
    %s TEXT NOT NULL);
    ''' % (IP_TABLE, IP_TABLE_SERVER_COLUMN, IP_TABLE_IP_COLUMN)
        print sql
        db.execute(sql)
        db.commit()
        sql = 'INSERT OR REPLACE INTO %s(%s,%s) VALUES ("%s","%s")' % (
            IP_TABLE, IP_TABLE_IP_COLUMN, IP_TABLE_SERVER_COLUMN, 'server',
            'mumas')
        print sql
        db.execute(sql)
        db.commit()
        db.close()
        print 'database create successfully'

    def insert(self, key, value):
        db = self.get_db()
        db.execute('INSERT OR REPLACE INTO %s(%s,%s) VALUES ("%s","%s")' %
                   (IP_TABLE, IP_TABLE_IP_COLUMN, IP_TABLE_SERVER_COLUMN, value,
                    key))
        db.commit()

    def check_table(self):
        db = self.get_db()
        c = db.execute('SELECT * FROM %s' % IP_TABLE)
        for r in c:
            print r[0], '==>', r[1]

    def find(self, key):
        db = self.get_db()
        sql = 'SELECT %s FROM %s WHERE %s="%s"' % (IP_TABLE_IP_COLUMN, IP_TABLE, IP_TABLE_SERVER_COLUMN, key)
        print sql
        c = db.execute(sql)
        res = c.fetchall()
        if len(res) > 0:
            return res[0]
        else:
            return ''


class SQLiteTestCase():
    db = SQLite3()

    def test_create_table(self):
        self.db.create_table()
        self.db.check_table()

    def test_insert(self):
        self.db.insert('hello', 'ok')
        self.db.check_table()

    def test_check(self):
        self.db.check_table()

    def test_find(self):
        print self.db.find('hello')


if __name__ == '__main__':
    s = SQLiteTestCase()
    s.test_create_table()
    s.test_insert()
    s.test_check()
    s.test_find()
