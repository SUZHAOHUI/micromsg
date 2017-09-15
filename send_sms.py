import random
import requests
import base64
import hashlib
import datetime
import os



def attach_header(msg):
    '''附加校验信息到msg消息中'''
    msg.pop('sign', None)
    app_key = msg['appkey']
    # app_id = find_appid(app_key)
    app_id = 'L9HASRNCM0IQ'  # XXX FOR TEST
    nonce_len = 16
    try:
        with open('/dev/urandom', 'rb') as fd:
            nonce = fd.read(nonce_len)
    except:
        # 没找到硬件随机数发生器, 使用系统自带的随机数函数
        try:
            nonce = os.urandom(nonce_len)
        except:
        # 没找到系统随机数发生器, 使用伪随机数函数
            nonce = bytes(random.randint(0, 255) for i in range(nonce_len))
    # nonce = nonce.hex()
    nonce = base64.b85encode(nonce).decode('utf8')
    created = datetime.datetime.now(datetime.timezone.utc)
    created = created.isoformat()
    result = {
        'nonce': nonce,
        'ts': created,
        }
    msg.update(result)
    data = sorted(msg.items(), key=lambda x:x[0])
    data = ["{}={}".format(*i) for i in data]
    data = ','.join(data)
    # print('data:', data)
    data = hashlib.sha256(data.encode('utf8'))
    data.update(app_id.encode('utf8'))
    sign = base64.b64encode(data.digest()).decode('utf8')
    msg.update({'sign': sign})
    return msg


def vcode(phone):
    msg = {'ms': phone,
           'appkey': 'hwh',
           'ts': '20160715114223039684',
           'tid':'10073599',
           'vp': '900',
           }
    msg = attach_header(msg)
    r = requests.post('http://101.200.221.216:8888/gsms', json=msg)
    return r.json()


def csms(phone,content):
    msg = {'ms': phone,
            'tid':'10073500',
           'appkey': 'wywawj',
           'ts': datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
           'ct': content
           }
    msg = attach_header(msg)
    r = requests.post('http://101.200.221.216:8888/csms', json=msg)
    return r.json()

if __name__=='__main__':
    vcode('13810326774')
