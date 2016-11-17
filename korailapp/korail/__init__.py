# -*- coding: utf-8 -*-
from __future__ import print_function
from korailapp.models import ReserveQueue
from .korail import Korail
from pushbullet import PushBullet
from datetime import datetime, timedelta
import threading, time


def get_signed_in_korail(korail_list, username, password):
    obj = korail_list.get(username)
    if obj and obj.get('expired') > datetime.now():
        return obj.get('korail')

    korail = Korail(username, password)
    korail.login()
    korail_list[username] = {'korail': korail, 'expired': datetime.now() + timedelta(minutes=15)}
    return korail

def reserveThread():
    korail_list = {}

    while True:
        reserves = ReserveQueue.objects.filter(reserve_code=None)
        for r in reserves:
            r.save()
            try:
                korail = get_signed_in_korail(korail_list, r.username, r.password)
                trains = korail.search_train(r.dep, r.arr, r.date, r.time, r.train_type)
            except Exception as e:
                print (e)
                continue

            for train in trains:
                if train.reservable == "Y" and train.group_code == r.train_type:
                    if (train.group_code == "KTX" and train.fee > 50000):
                        continue

                    # reserve
                    reserve_code = korail.reserve(train)
                    if not reserve_code:
                        continue
                    r.reserve_code = reserve_code
                    r.save()

                    # send push
                    pb = PushBullet("o.F9hgFDT4awcXH2XHZ390ECvXj1JmGj0F")
                    title = "%s %s (%s-%s)" % (train.group, train.arr, train.dep_date[-4:], train.dep_time[:4])
                    note = "%s %s->%s (%s %s-%s) %s" % (train.type, train.dep, train.arr, train.dep_date[-4:], train.dep_time[:4], train.arr_time[:4], train.fee)
                    pb.push_note(title, note)
                    break

        time.sleep(10)

th = threading.Thread(target=reserveThread)
th.start()
#th.join()
