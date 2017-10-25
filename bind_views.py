import logging
from flask import request,jsonify,make_response
import json
import base64
from database import app,rd,sb,rd_pay
from common import f_bind,f_unbind,verify_auth_token,pay_sign,generate_auth_token,f_vcallreq
import datetime,os,uuid,time
from datetime import timedelta
from get_xml import gen_xml
from get_prepay_id import parse
import requests
namespace = "bind_micro_msg"
headers = {'Content-Type': 'application/json','charset':'gbk'}
def hello():
    logging.info(request.cookies)
    return 'Welcome to my mricro msg app!'

def get_city_number():
    token = request.headers.get('token')
    try:
        checkinfo = eval(verify_auth_token(token))
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_get_code= request.get_json()
        else:
            js_get_code=request.json
    else:
        if request.method=='GET':
            js_get_code = request.args.to_dict()
        else:
            js_get_code = json.loads(request.data.decode('utf8'))
    city=js_get_code.get('city')
    if not city:
        rs = json.dumps({"result": 1})
        return  make_response(rs)
    try:
        city_numbers=sb.session.execute("""  select c.city,a.acms from acms a
                               left join city c on a.code=c.code
                               where a.state in ('N','U') and a.status='I' and use_location='A' and c.city like '%{}%'
                            """.format(city))
        j=0
        acmss = None
        d_number={}
        for i in city_numbers:
            if j==10:
                break
            city=i[0]
            acms=i[1]
            d_number['city']=city
            if  acmss:
                acmss='{},{}'.format(acmss,acms)
            else:
                acmss=acms
            d_number['number']=acmss
            logging.info('city={},acms={}'.format(city,acmss))
            j+=1
        d_number.update({'result':0})
        rs=json.dumps(d_number)
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)


def get_city_list():
    token = request.headers.get('token')
    try:
        checkinfo = eval(verify_auth_token(token))
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)
    try:
        city_numbers=sb.session.execute("""  select DISTINCT c.city,a.code from acms a
                               left join city c on a.code=c.code
                               where a.state='U' and a.status='I'
                            """)

        l_city=[]
        for i in city_numbers:
            d_city = {}
            city=i[0]
            code=i[1]
            d_city['city']=city
            d_city['code']=code
            logging.info('city={},code={}'.format(city,code))
            l_city.append(d_city)
        rs=json.dumps(l_city)
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)


def ax_bind():
    token=request.headers.get('token')
    try:
        checkinfo=eval(verify_auth_token(token))
        logging.info(checkinfo)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1,'msg':'token verify error'})
        return  make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    appkey=checkinfo['appkey']
    prtms=checkinfo['msisdn']
    useid=checkinfo['userid']
    cardno=checkinfo['idcard']
    appid=checkinfo['appid']

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_ax_bind= request.get_json()
        else:
            js_ax_bind=request.json
    else:
        if request.method=='GET':
            js_ax_bind = request.args.to_dict()
        else:
            js_ax_bind = json.loads(request.data.decode('gbk'))
    acms=js_ax_bind.get('acms')
    if not acms:
        rs = json.dumps({"result": 1})
        return  make_response(rs)
    logging.info('{},{},{},{},{}'.format(appkey,prtms,cardno,appid,useid))
    r=f_bind(appkey, prtms, acms, cardno, appid)
    logging.info(r)
    if r['result']=='200':
        try:
            state_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # logging.info("""
            #                     update acms set state='U',status='V',state_date='{}',status_date='{}' where acms='{}';\
            #                     insert into user_acms_rela (user_id,acms_id,state,state_date,operator_id,purpose)\
            #                     values({},(SELECT acms_id from acms where acms='{}'),'V','{}',{},'O');\
            #                     insert into subs_rela (anum,xnum,user_id,state,state_date,operator)\
            #                     values('{}','{}',{},'B','{}',{})\
            #                """.format(state_date,state_date,acms,useid,acms,state_date,useid,prtms,acms,useid,state_date,useid))
            sb.session.execute("""
                                update acms set state='U',status='V',state_date='{}',status_date='{}' where acms='{}';
                                insert into user_acms_rela (user_id,acms_id,state,state_date,operator_id,purpose)
                                values({},(SELECT acms_id from acms where acms='{}'),'V','{}',{},'O');
                                insert into subs_rela (anum,xnum,user_id,state,state_date,operator)
                                values('{}','{}',{},'B','{}',{})
                           """.format(state_date,state_date,acms,useid,acms,state_date,useid,prtms,acms,useid,state_date,useid))
            rs = json.dumps({'result': 0})
        except Exception as ex:
            rs = json.dumps({"result":1})
            logging.error(ex)
            sb.session.rollback()
            return make_response(rs)
        finally:
            sb.session.commit()
            sb.session.close()
    else:
        rs = json.dumps({'result': 1})
    return make_response(rs)



def ax_unbind():
    token=request.headers.get('token')
    try:
        checkinfo=eval(verify_auth_token(token))
        logging.info(checkinfo)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    appkey=checkinfo['appkey']
    prtms=checkinfo['msisdn']
    useid=checkinfo['userid']
    appid=checkinfo['appid']
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_ax_unbind= request.get_json()
        else:
            js_ax_unbind=request.json
    else:
        if request.method=='GET':
            js_ax_unbind = request.args.to_dict()
        else:
            js_ax_unbind = json.loads(request.data.decode('gbk'))
    acms=js_ax_unbind.get('acms')
    if not acms:
        rs = json.dumps({"result": 1})
        return  make_response(rs)
    logging.info('{},{},{},{}'.format(appkey,prtms,appid,useid))
    r=f_unbind(appkey, prtms, acms,appid)
    logging.info(r)
    if r['result']=='200':
        state_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            sb.session.execute("""
                                update acms set state='D',status='I',state_date='{}',status_date='{}' where acms='{}';
                                update user_acms_rela set state='I',state_date='{}'
                                where state='V' and user_id={} and acms_id=(SELECT acms_id from acms where acms='{}');
                                update subs_rela set state='U',state_date='{}' where anum='{}' and xnum='{}' and state='B';)
                           """.format(state_date, state_date, acms, state_date,useid, acms, state_date, prtms, acms))
            rs = json.dumps({'result': 0})
        except Exception as ex:
            rs = json.dumps({"result":1})
            logging.error(ex)
            sb.session.rollback()
            return make_response(rs)
        finally:
            sb.session.commit()
            sb.session.close()
    else:
        rs = json.dumps({'result': 1})
    return make_response(rs)


def vcall_req():
    token = request.headers.get('token')
    try:
        checkinfo = eval(verify_auth_token(token))
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return make_response(rs)
    appid=checkinfo['appid']
    appkey=checkinfo['appkey']
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_vcall_req= request.get_json()
        else:
            js_vcall_req=request.json
    else:
        if request.method=='GET':
            js_vcall_req= request.args.to_dict()
        else:
            js_vcall_req= json.loads(request.data.decode('utf8'))
    acms=js_vcall_req.get('acms')
    calledms=js_vcall_req.get('calledms')
    if len(calledms) > 12 and calledms.find('-'):
        calledms=calledms.replace('-','')

    if (not acms) or (not calledms):
        rs = json.dumps({"result": 1,'msg':'parameters losing!'})
        return  make_response(rs)
    r=f_vcallreq(appkey, acms, calledms, appid)
    logging.info(r)
    logging.info(r['result'])
    if r['result'] == '200':
        rs = json.dumps({"result": 0})
        return make_response(rs)
    else:
        rs = json.dumps({"result": 1,'msg':'acms platform return err'})
        return make_response(rs)



def get_wx_p():
    token=request.headers.get('token')
    try:
        checkinfo=eval(verify_auth_token(token))
        logging.info(checkinfo)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1,"msg":"token error"})
        return  make_response(rs)
    msisdn=checkinfo.get('msisdn')

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_wxpublic_info= request.get_json()
        else:
            js_wxpublic_info=request.json
    else:
        if request.method=='GET':
            js_wxpublic_info = request.args.to_dict()
        else:
            js_wxpublic_info = json.loads(request.data.decode('gbk'))
    logging.info(js_wxpublic_info)
    appid=js_wxpublic_info.get('appid')
    secret=js_wxpublic_info.get('secret')
    js_code=js_wxpublic_info.get('js_code','9e6bb39cf18dc3f2b94e5c29ca9c8dcf')
    amt=js_wxpublic_info.get('amt')
    acms=js_wxpublic_info.get('acms')
    days=js_wxpublic_info.get('days')

    def get_expire_date(acms):
        try:
            expire_date=None
            unsubts = sb.session.execute("""
                  select unsubts from acms where use_location='A' and state='U' and acms='{}'
                   """.format(acms))
            for i in unsubts:
                expire_date = i[0]
        except Exception as ex:
            logging.info(ex)
            return 0
        finally:
            sb.session.close()
        return expire_date

    if not appid or not secret or not js_code or not amt:
        rs = json.dumps({"result": 1,'msg':'parameters losing!'})
        return  make_response(rs)
    grant_type = 'authorization_code'
    values={'appid':appid,'secret':secret,'js_code':js_code,'grant_type':grant_type}
    logging.info(values)
    rg=requests.get('https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'\
    .format(values['appid'],values['secret'],values['js_code']))

    logging.debug(rg.text)
    openid=rg.json().get('openid')
    spbill_create_ip='101.201.101.70'

    # spbill_create_ip=js_wxpublic_info.get('spbill_create_ip')

    d_unifiedorder={}
    key='6XlblatoOeCriipz7lkAgiSH2RI0rk8k'
    # key='a8b0248258c0110fd8895d7466b8c579'
    d_unifiedorder['appid']=appid  #小程序ID
    d_unifiedorder['mch_id']='1485541442'    #商户号
    # d_unifiedorder['mch_id'] = '1265774901'
    d_unifiedorder['nonce_str']=base64.b64encode(os.urandom(24)).upper().decode()
    d_unifiedorder['body']='haowaihao'
    d_unifiedorder['out_trade_no']=uuid.uuid4().hex.upper()
    d_unifiedorder['total_fee']=str(amt)
    d_unifiedorder['spbill_create_ip']=spbill_create_ip
    d_unifiedorder['notify_url']='https://weixin1.haowaihao.com.cn/api/notifyHWH'
    d_unifiedorder['trade_type']='JSAPI'
    d_unifiedorder['openid']=openid
    sign=pay_sign(d_unifiedorder,key)
    d_unifiedorder['sign']=sign
    logging.info(d_unifiedorder)
    xmltext=gen_xml(d_unifiedorder)
    logging.info(xmltext)
    pray_pay=requests.post('https://api.mch.weixin.qq.com/pay/unifiedorder',data=xmltext,headers = {'Content-type': 'text/xml'})
    logging.info(pray_pay.text.encode('ISO-8859-1').decode())
    r_p=parse(pray_pay.text,key)
    logging.info(r_p)
    if r_p.get('result'):
        return r_p
    elif r_p.get('result_code')=='SUCCESS' and r_p.get('return_code')=='SUCCESS':
        rtwx={}
        rtwx['appId']=r_p['appid']
        rtwx['timeStamp']=str(int(time.time()))
        rtwx['nonceStr']=base64.b64encode(os.urandom(24)).upper().decode()
        rtwx['package']='prepay_id={}'.format(r_p['prepay_id'])
        rtwx['signType']='MD5'
        sign=pay_sign(rtwx,key)
        rtwx['paySign']=sign
        expire_date = get_expire_date(acms)
        current_date=datetime.datetime.now()
        if not expire_date:
            expire_date = current_date
        expire_date = expire_date + timedelta(days=int(days))
        expire_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        pay_flag=0
        z=0
        while (not pay_flag) and z<10:
            pay_flag = rd_pay.hget('payment:report:{}'.format(d_unifiedorder['out_trade_no']), 'result_code')
            if pay_flag=='SUCCESS':
                state='SUCCESS'
                rtwx['data']={'amcs':acms,'amt':amt,'state':'SUCCESS','expire_date':expire_date}
            z+=1
            time.sleep(1)
        if z>=10:
            rtwx['data']={'amcs':acms,'amt':amt,'state':'time out','expire_date':expire_date}
            state='timeout'
        try:
            sb.session.execute("insert into payment(msisdn,acms,amt,topup_date,state,out_trade_no,days)\
                               VALUES('{}','{}',{},'{}','{}','{}',{})".\
                               format(msisdn,acms,amt,current_date,state,d_unifiedorder['out_trade_no'],days))
            sb.session.commit()
        except Exception as ex:
            logging.error(ex)
            logging.info({"result": 1, 'msg': 'insert data error!'})
        finally:
            sb.session.close()

        logging.info(rtwx)
        return json.dumps(rtwx)
    else:
        return json.dumps({'result':1})

def get_price():
    token=request.headers.get('token')
    try:
        checkinfo=eval(verify_auth_token(token))
        logging.info(checkinfo)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1,"msg":"token error"})
        return  make_response(rs)
    try:
        priceinfo=sb.session.execute("SELECT price,period,period_unit FROM price where state='V'").fetchall()
        l_p=[]
        for i in priceinfo:
            d_p = {}
            price=i[0]
            logging.info(price)
            period=i[1]
            period_unit=i[2]
            d_p['price']=price
            d_p['period']=period
            d_p['period_unit']=period_unit
            l_p.append(d_p)
    except Exception as ex:
        rs = json.dumps({"result": 1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    rs = json.dumps(l_p)
    logging.info(rs)
    return rs


def query_topup():
    token=request.headers.get('token')
    try:
        checkinfo=eval(verify_auth_token(token))
        logging.info(checkinfo)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'token verify error'})
        return  make_response(rs)
    if not checkinfo:
        rs = json.dumps({"result": 1,"msg":"token error"})
        return  make_response(rs)
    msisdn=checkinfo['msisdn']
    try:
        topup_info=sb.session.execute("select acms,amt,topup_date,state from payment where msisdn={} order by topup_date desc".format(msisdn))
        sb.session.commit()
        ti=[]
        for ic in topup_info:
            t_c = {}
            t_c['acms']=ic[0]
            t_c['amt']=ic[1]
            t_c['topup_date']=str(ic[2])
            t_c['state']=ic[3]
            ti.append(t_c)
    except Exception as ex:
        logging.error(ex)
        return json.dumps({"result": 1, 'msg': 'Query data error!'})
    finally:
        sb.session.close()
    rs=json.dumps(ti)
    logging.info(rs)
    return json.dumps(rs)





