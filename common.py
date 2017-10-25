from Crypto.Cipher import DES3
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,SignatureExpired,BadSignature

import hashlib

from database import app
# from cloghandler import ConcurrentRotatingFileHandler
import logging
import logging.handlers
import os
import base64
import datetime,time
import requests,json
LOGLEVEL='DEBUG'
headers = {'Content-Type': 'application/json','charset':'gbk'}
url='http://101.201.101.70:5000'

def f_log_concurrent(log_file):
    LEVELS = { 'debug':logging.DEBUG,'info':logging.INFO,'error':logging.ERROR}
    log = logging.getLogger()
    level=LEVELS.get(LOGLEVEL,logging.NOTSET)

    # Use an absolute path to prevent file rotation trouble.
    logfile = os.path.abspath(log_file)
    # Rotate log after reaching 1G, keep 60 old copies.
    rotateHandler = ConcurrentRotatingFileHandler(logfile, "a", 1024*1024*1024, 60,encoding="utf-8")
    fm=logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s","%Y-%m-%d %H:%M:%S",)
    rotateHandler.setFormatter(fm)
    log.addHandler(rotateHandler)
    log.setLevel(level)
    return log

def f_log(log_file):
    LEVELS = { 'debug':logging.DEBUG,'info':logging.INFO,'error':logging.ERROR}
    logger = logging.getLogger()
    level=LEVELS.get(LOGLEVEL,logging.NOTSET)
    logging.basicConfig(level=level,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')

    current_dir = os.path.dirname(os.path.abspath(__file__))

    logpath=os.path.join(current_dir,'log')

    if os.path.exists(logpath) is False:
        os.makedirs(logpath)
    handler=logging.handlers.TimedRotatingFileHandler(os.path.join(logpath,log_file),when='D',interval=1,backupCount=365)
    fm=logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s","%Y-%m-%d %H:%M:%S")
    handler.setFormatter(fm)
    logger.addHandler(handler)


def init_str(s):
    l=len(s) % 8
    if l!=0:
        c=8-l
        s+=chr(c)*c
    return s

def DesEncrypt(passwd):
    key = bytes("8h 2v4s7u%8y8n7b&gy2/,72","utf-8")
    passwd1=init_str(passwd)
    des3=DES3.new(key,DES3.MODE_ECB)
    res2=des3.encrypt(passwd1)
    b2bencryptkey=  base64.standard_b64encode(res2)
    return b2bencryptkey


def CheckSID(dict1, secret):
    if isinstance(dict1, dict):
        list1 = sorted(dict1.items(),key=lambda x:x[0])
        str=[]

        for list_item in iter(list1):
            if list_item[0]!='sid'and list_item[0]!='sign':                    # and list_item[0]!='rsvd':
                if list_item[1] is None:
                    continue
                str.append(list_item[0])
                str.append(list_item[1])

        str=(''.join(str))
    else:
        str=dict1
    str=(''.join((secret,str)))
    # print(str)
    a2md5 = hashlib.md5()
    a2md5.update(str.encode('utf-8'))
    a2md5_Digest = a2md5.hexdigest()
    a2md5value=a2md5_Digest.upper()
    return a2md5value

def f_bind(appkey,prtms,acms,cardno,appid):
    values = {"ver": "1.0",
              "msgid": "",
              "ts": "",
              "service": "acbss",
              "msgtype": "subreq",
              "appkey": appkey,
              "rsvd": "0",
              "prtms": prtms,
              "acms": acms,
              "subts": "",
              "producttype": "4",
              "name": "李新会",
              # "anucodecalled": "218",
              "cardtype": "1",
              "callrecording": "1",
              "smsmtchannel": "3",
              "cardno": cardno,
              "sid": "505CCE48B7A20E319C1169CCE7D4A075"}
    sid = CheckSID(values, appid)
    values['sid'] = sid
    r = requests.post(url, json.dumps(values), headers=headers)
    return r.json()

def f_unbind(appkey,prtms,acms,appid):
    values = {"ver": "1.0",
              "msgid": "5742461579df5400606dce74sub",
              "ts": "20160815112221231",
              "service": "acbss",
              "msgtype": "unsubreq",
              "appkey": appkey,
              "rsvd": "0",
              "prtms": prtms,
              "acms": acms,
              "unsubts": "20160815142221231"}
    sid = CheckSID(values, appid)
    values['sid'] = sid
    r = requests.post(url, json.dumps(values), headers=headers)
    return r.json()


def f_vcallreq(appkey,acms,calledms,appid):
    values={
     "ver":"1.0",
     "msgid":"5f053ec9-11d5-4580-bfb7-f82194989923",
     "ts":"20160816095014091",
     "service":"acsa",
     "msgtype":"vcallreq",
     "sid":"002B85761915447E0821803ABD7F0415",
     "appkey":appkey,
     "acms":acms,
     "calledms":calledms
     }
    sid = CheckSID(values, appid)
    values['sid'] = sid
    r = requests.post(url, json.dumps(values), headers=headers)
    return r.json()




def generate_auth_token(dict,expiration = 18000):
    s = Serializer('haowaihao2016lxhlq', expires_in = expiration)
    return s.dumps(dict)

def verify_auth_token(token):
    s = Serializer('haowaihao2016lxhlq')
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None # valid token, but expired
    except BadSignature:
        return None # invalid token
    except Exception as ex:
        logging.info(ex)
        return None
    return data

def pay_sign(dict1, secret='6XlblatoOeCriipz7lkAgiSH2RI0rk8k'):
    if isinstance(dict1, dict):
        list1 = sorted(dict1.items(),key=lambda x:x[0])
        str1=[]
        for list_item in iter(list1):
            if list_item[0]!='sign':
                if list_item[1] is None:
                    continue
                str1.append(list_item[0])
                str1.append('=')
                str1.append(list_item[1])
                str1.append('&')

    str_value=''.join(str1)
    str_value= "{}key={}".format(str_value, secret)

    logging.info(str_value)
    a2md5 = hashlib.md5()
    a2md5.update(str_value.encode('GBK'))
    a2md5_Digest = a2md5.hexdigest()
    a2md5value=a2md5_Digest.upper()
    return a2md5value

if __name__ == '__main__':
    # DesEncrypt("123456")
    token=generate_auth_token({'id': 'foobar'})
    aaa=verify_auth_token(token)
    print(aaa)