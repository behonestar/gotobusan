# -*- coding: utf-8 -*-
from __future__ import print_function
import requests
import json

SCHEME = "https"
KORAIL_HOST = "smart.letskorail.com"
KORAIL_PORT = "9443"

KORAIL_DOMAIN = "%s://%s:%s" % (SCHEME, KORAIL_HOST, KORAIL_PORT)
KORAIL_MOBILE = "%s/classes/com.korail.mobile" % KORAIL_DOMAIN

KORAIL_LOGIN = "%s.login.Login" % KORAIL_MOBILE
KORAIL_LOGOUT = "%s.common.logout" % KORAIL_MOBILE
KORAIL_SEARCH_SCHEDULE = "%s.seatMovie.ScheduleView" % KORAIL_MOBILE
KORAIL_TICKETRESERVATION = "%s.certification.TicketReservation" % KORAIL_MOBILE

def parse_value(dict, keys):
    for key in keys:
        if key in dict:
            dict = dict[key]
        else:
            return None
    return dict

class SeatType:
    SPECAIL = '2'
    GENERAL = '1'

class TrainType:
    KTX = "100"  # "KTX, KTX-산천",
    SAEMAEUL = "101"  # "새마을호",
    MUGUNGHWA = "102"  # "무궁화호",
    TONGGUEN = "103"  # "통근열차",
    NURIRO = "102"  # "누리로",
    ALL = "109"  # "전체",
    AIRPORT = "105"  # "공항직통",
    KTX_SANCHEON = "100"  # "KTX-산천",
    ITX_SAEMAEUL = "101"  # "ITX-새마을",
    ITX_CHEONGCHUN = "104"  # "ITX-청춘",

    def __init__(self):
        raise NotImplementedError("Do not make instance.")

class Train():
    def __init__(self, train_info):
        self.no = int(train_info.get('h_trn_no'))  #"161"
        self.type = train_info.get('h_trn_clsf_nm')  #"KTX-산천"
        self.type_code= train_info.get('h_trn_clsf_cd')
        self.group = train_info.get('h_trn_gp_nm')  #"KTX"
        self.group_code = train_info.get('h_trn_gp_cd')  #"100"
        self.stopby = train_info.get('h_dtour_txt')  #"-", "구포정차", "수원정차"

        self.rundate = train_info.get('h_run_dt')
        self.dep = train_info.get('h_dpt_rs_stn_nm')
        self.dep_code = train_info.get('h_dpt_rs_stn_cd')
        self.dep_date = train_info.get('h_dpt_dt')
        self.dep_time = train_info.get('h_dpt_tm')  #"073000"

        self.arr = train_info.get('h_arv_rs_stn_nm')
        self.arr_code = train_info.get('h_arv_rs_stn_cd')
        self.arr_date = train_info.get('h_arv_dt')
        self.arr_time = train_info.get('h_arv_tm')  #"204400"

        self.reservable = train_info.get('h_rsv_psb_flg')  #"Y", "N"
        self.rsv_special = train_info.get('h_gen_rsv_nm')  #"매진", "예약하기"
        self.rsv_general = train_info.get('h_gen_rsv_nm')
        self.rsv_stand = train_info.get('h_stnd_rsv_nm')  #"역발매중"

        self.fee = int(train_info.get('h_rcvd_amt')) #"00000000048800": 48,800원
        self.mile_rate = float(train_info.get('h_train_disc_gen_rt')) * -1 #"-005.00": 5%

        #print("{}\t{}({})\t\t{}\t{}\t{}\t{}".format(self.열차번호, self.열차그룹, self.열차종류, self.예약가능,
        #                                            self.요금, self.마일리지적립률, self.경유))

class Korail():
    _session = requests.session()
    _device = 'AD'
    _version = '150718001'
    _key = 'korail01234567890'

    username = None
    password = None

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def _is_valid(self, j):
        if j.get('strResult') != 'SUCC':
            return False
        if j.get('h_msg_cd') == 'IRZ000001':  #login
            return True
        if j.get('h_msg_cd') == 'IRG000000':  #search_train
            return True
        if j.get('h_msg_cd') == 'IRR000018':  #reserve success
            return True
        if j.get('h_msg_cd') == 'WRR664260':  #reserve success ('동일 시간대 예약 내역 존재')
            return True
        return False

    def login(self):
        data = {
            'Device': self._device,
            'Version': self._version,
            'txtInputFlg': 2, #2:membership #4:phone #5:email
            'txtMemberNo': self.username,
            'txtPwd': self.password
        }
        r = self._session.post(KORAIL_LOGIN, data=data)
        j = json.loads(r.text)

        if not self._is_valid(j):
            raise Exception("로그인 실패")

        self._key = j['Key']
        self.membership_number = j['strMbCrdNo']
        self.name = j['strCustNm']
        self.email = j['strEmailAdr']
        return True

    def search_train(self, dep, arr, date, time, train_type):
        data = {
            'Device': self._device,
            'radJobId': '1',
            'selGoTrain': train_type,
            'txtCardPsgCnt': '0',
            'txtGdNo': '',
            'txtGoAbrdDt': date,  # '20140803',
            'txtGoEnd': arr,
            'txtGoHour': time,  # '071500',
            'txtGoStart': dep,
            'txtJobDv': '',
            'txtMenuId': '11',
            'txtPsgFlg_1': '1',  # 어른
            'txtPsgFlg_2': '0',  # 어린이
            'txtPsgFlg_3': '0',  # 경로
            'txtPsgFlg_4': '0',  # 장애인1
            'txtPsgFlg_5': '0',  # 장애인2
            'txtSeatAttCd_2': '000',
            'txtSeatAttCd_3': '000',
            'txtSeatAttCd_4': '015',
            'txtTrnGpCd': train_type,

            'Version': self._version,
        }
        r = self._session.get(KORAIL_SEARCH_SCHEDULE, params=data)
        j = json.loads(r.text)
        #print (r.text)

        trains = []
        train_infos = parse_value(j, ['trn_infos', 'trn_info'])
        if not train_infos:
            raise Exception("열차 정보를 얻어올 수 없습니다.")

        for info in train_infos:
            trains.append(Train(info))

        if len(trains) == 0:
            raise Exception("열차 정보가 없습니다.")

        return trains


    def reserve(self, train):
        data = {
            'Device': self._device,
            'Version': self._version,
            'Key': self._key,
            'txtGdNo': '',
            'txtJobId': '1101',
            'txtTotPsgCnt': '1',  # 탑승인원
            'txtSeatAttCd1': '000',
            'txtSeatAttCd2': '000',
            'txtSeatAttCd3': '000',
            'txtSeatAttCd4': '015',
            'txtSeatAttCd5': '000',
            'hidFreeFlg': 'N',
            'txtStndFlg': 'N',
            'txtMenuId': '11',
            'txtSrcarCnt': '0',
            'txtJrnyCnt': '1',

            # 여정 정보1
            'txtJrnySqno1': '001',
            'txtJrnyTpCd1': '11',
            'txtDptDt1': train.출발일,
            'txtDptRsStnCd1': train.출발역코드,
            'txtDptTm1': train.출발시간,
            'txtArvRsStnCd1': train.도착역코드,
            'txtTrnNo1': train.열차번호,
            'txtRunDt1': train.운행일,
            'txtTrnClsfCd1': train.열차종류코드,
            'txtPsrmClCd1': SeatType.GENERAL,
            'txtTrnGpCd1': train.열차그룹코드,
            'txtChgFlg1': '',

            # 탑승 정보1
            'txtPsgTpCd1': "1",  #1:어른 3:어린이
            'txtDiscKndCd1': "000", #할인 타입
            'txtCompaCnt1': "1",  #인원수
            'txtCardCode_1': '',  #할인카드 종류
            'txtCardNo_1': '',  #할인카드 번호
            'txtCardPw_1': '',  #할인카드 비밀번호
        }

        r = self._session.get(KORAIL_TICKETRESERVATION, params=data)
        j = json.loads(r.text)

        if not self._is_valid(j):
            return False

        return j.get('h_pnr_no')







