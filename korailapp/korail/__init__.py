# -*- coding: utf-8 -*-
from __future__ import print_function
from django.utils import timezone
from korailapp.models import ReserveQueue
from .korail import Korail
from pushbullet import PushBullet
import threading, time

def reserveThread():
    korail_list = {}

    while True:
        reserves = ReserveQueue.objects.filter(reserv_code=None)
        for r in reserves:
            korail = korail_list.get(r.username)
            if not korail:
                korail = Korail(r.username, r.password)
                try:
                    korail.login()
                except Exception as e:
                    print (e)
                    continue
                korail_list[r.username] = korail

            try:
                trains = korail.search_train(r.dep, r.arr, r.date, r.time, r.train_type)
            except Exception as e:
                print (e)
                continue

            for train in trains:
                if train.예약가능 == "Y" and train.열차그룹코드 == r.train_type:
                    if (train.열차그룹 == "KTX" and train.요금 > 50000):
                        continue

                    # reserve
                    reserve_code = korail.reserve(train)
                    if not reserve_code:
                        continue
                    r.reserve_code = reserve_code
                    r.save()

                    # send push
                    pb = PushBullet("o.F9hgFDT4awcXH2XHZ390ECvXj1JmGj0F")
                    title = "{} {}행 ({}-{})".format(
                        train.열차그룹, train.도착역, train.출발일[-4:], train.출발시간[:4]
                    )
                    note = "{} {}->{} ({} {}~{}) 요금: {}".format(
                        train.열차종류,
                        train.출발역, train.도착역,
                        train.출발일[-4:], train.출발시간[:4], train.도착시간[:4],
                        train.요금
                    )
                    pb.push_note(title, note)
                    break

        time.sleep(10)

th = threading.Thread(target=reserveThread)
# th.start()
#th.join()
