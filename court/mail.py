#!/usr/bin/env python
# -*- coding:utf8 -*-
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart

import time
from email.mime.text import MIMEText


def send_attach(users, title, message, attach, tag):
    username = 'notify@ipin.com'
    password = '4c4b5e4dfF'
    smtphost = 'smtp.exmail.qq.com'
    smtpport = 465
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    if isinstance(title, unicode):
        title = message.encode('utf-8')
    mail_body = message
    mail_to = users
    msg = MIMEMultipart()
    msg['Subject'] = Header(title, 'utf-8')
    msg['From'] = username
    msg['To'] = ';'.join(mail_to)
    msg['date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')
    body = MIMEText(mail_body, _charset='utf-8')
    msg.attach(body)

    att = MIMEText(open(attach, 'rb').read(), 'base64', 'utf-8')
    att["Content-Type"] = 'application/octet-stream'
    att["Content-Disposition"] = 'attachment;filename="%s"' % tag
    msg.attach(att)

    smtp = smtplib.SMTP_SSL(smtphost, smtpport)
    smtp.login(username, password)
    smtp.sendmail(username, mail_to, msg.as_string())
    smtp.quit()
