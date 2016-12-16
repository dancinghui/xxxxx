#!/usr/bin/env python
# -*- coding:utf8 -*-
from accounts import CardManager, AccountManager, pay_account

if __name__ == '__main__':
    cm = CardManager()
    ac = AccountManager()
    name = '福建'
    cm.save()
    # for card in cm.getall():
    #     if pay_account(ac, card, name):
    #         print card
    #         break
    #     else:
    #         print 'card is used', card
