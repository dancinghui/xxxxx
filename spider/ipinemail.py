#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
import re
import poplib
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header

class BaseEmail(object):
    def __init__(self, smtphost='smtp.exmail.qq.com', smtpport=465, pophost='pop.exmail.qq.com'):
        self._smtphost = smtphost
        self._smtpport = int(smtpport)
        self._pophost = pophost

    def sendmail(self, email, title, message, accfrom={'username':'notify@ipin.com', 'password':'4c4b5e4dfF'}):
        username = accfrom['username']
        password = accfrom['password']
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        if isinstance(title, unicode):
            title = message.encode('utf-8')
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['Subject'] = Header(title, 'utf-8')
        msg['From'] = username
        if isinstance(email, list):
            msg['To'] = '; '.join(email)
            tolist = email
        else:
            msg['To'] = email
            tolist = [email]
        for i in range(0, len(tolist)):
            m = re.search('<([a-z0-9_@\-.]*)>\s*$', tolist[i], re.I)
            if m:
                tolist[i] = m.group(1)
        print "sending mail to", tolist
        print msg.as_string()
        s = smtplib.SMTP_SSL(self._smtphost, self._smtpport)
        s.login(username, password)
        s.sendmail(username, tolist, msg.as_string())
        s.quit()

    def send_mail_with_img(self, email, title, message, img_path="", accfrom={'username':'notify@ipin.com', 'password':'4c4b5e4dfF'}):
        if img_path is "":
            return self.sendmail(email, title, message)
        username = accfrom["username"]
        password = accfrom["password"]
        img_data = open(img_path, 'rb').read()
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = username
        msg['To'] = email

        text = MIMEText(message)
        msg.attach(text)
        image = MIMEImage(img_data, name=os.path.basename(img_path))
        msg.attach(image)

        if isinstance(email, list):
            msg['To'] = '; '.join(email)
            tolist = email
        else:
            msg['To'] = email
            tolist = [email]

        s = smtplib.SMTP_SSL(self._smtphost, self._smtpport)
        s.login(username, password)
        s.sendmail(username, tolist, msg.as_string())
        s.quit()

    def retr_email(self, username, password, which=""):
        pop_conn = poplib.POP3_SSL(self._pophost)
        pop_conn.user(username)
        pop_conn.pass_(password)
        # message= pop_conn.retr(1)
        res = pop_conn.stat()
        msgcnt = res[0]
        if which is "" or int(which) is 0:
            msgs = pop_conn.retr(msgcnt)
            return msgs
        if int(which)>msgcnt or (int(msgcnt) + int(which)) < 0:
            print "No such message!"
            return None
        elif int(which) < 0 and int(msgcnt)+int(which) > 0:
            msg = pop_conn.retr(int(msgcnt)+int(which)+1)
            return msg
        else:
            return pop_conn.retr(int(which))

    def retr_latest_email(self, username, password):
        return self.retr_email(username, password, -1)