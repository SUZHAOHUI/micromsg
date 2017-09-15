import logging
from flask import request,jsonify,make_response
import json
from common import DesEncrypt,verify_auth_token,generate_auth_token,pay_sign
from flask import session
from database import  rd,sb,rd_sms,rd_pay
from send_sms import vcode,csms
import datetime
from protocal import protocal
from get_prepay_id import trans_xml_to_dict


def user_login():
    dd={}
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_user= request.get_json()
        else:
            js_user=request.json
    else:
        if request.method=='GET':
            js_user = request.args.to_dict()
        else:
            js_user = json.loads(request.data.decode('gbk'))
    msisdn=js_user['prtms']
    password=js_user['apwd']
    loginpassword=DesEncrypt(password)
    sloginpassword=loginpassword.decode()
    logging.info("SELECT name,idcard,userid FROM user where tel='{}' and password='{}'".\
                 format(msisdn,sloginpassword))
    try:
        userinfo=sb.session.execute("SELECT name,idcard,user_id FROM user where tel='{}' and password='{}'".format(msisdn,sloginpassword)).fetchone()
        if userinfo:
            result=0
            username=userinfo[0]
            idcard=userinfo[1]
            if not idcard:
                idcard='0'
            userid = userinfo[2]
            if session.get('msisdn')==msisdn:
                logging.info(msisdn)
            # session['username']=username
            # session['msisdn']=msisdn
            # session['userid']=userid
            # session['idcard']=idcard
            # session['id'] = uuid.uuid4().hex
            dd['username']=username
            dd['msisdn']=msisdn
            dd['userid']=userid
            dd['idcard']=idcard
        else:
            rs = json.dumps({"result": 1})
            return make_response(rs)
        appkey=sb.session.execute("SELECT VALUE FROM parameter where parameter_id=900").fetchone()
        mode = sb.session.execute("SELECT VALUE FROM parameter where parameter_id=0").fetchone()
        appkey=appkey[0]
        mode=mode[0]
        appid=rd.hget('ac_auth:{}'.format(appkey),'appid')
        # session['appkey']=appkey
        # session['mode']=mode
        # session['appid']=appid
        dd['appkey']=appkey
        dd['mode']=mode
        dd['appid']=appid

        logging.info('appkey={}, username={}, idcard={},appid={},mode={}'.format(appkey, username, idcard,appid,mode))
        if appkey=='wywawj':
            ifpay=0
        else:
            ifpay=1
        r={}
        r['result']=result
        r['appkey']=appkey
        r['appkid']=appid
        r['aname']=username
        r['cardno']=idcard
        r['subs_model']=mode
        r['ifpay']=ifpay
        token=generate_auth_token(json.dumps(dd))
        r['token']=token.decode()
        logging.info('login return response info:{}'.format(r))
        rs = json.dumps(r)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1})
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)

def changePwd():

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_cpwd= request.get_json()
        else:
            js_cpwd=request.json
    else:
        if request.method=='GET':
            js_cpwd = request.args.to_dict()
        else:
            js_cpwd = json.loads(request.data.decode('gbk'))
    newpwd=js_cpwd.get('newpwd')
    msisdn=js_cpwd.get('phone')
    if not msisdn:
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

    if not newpwd:
        rs = json.dumps({"result": 1})
        return  make_response(rs)

    newpwd=DesEncrypt(newpwd).decode()
    logging.info("update user set password='{}' where tel={}".format(newpwd,msisdn))
    try:
        sb.session.execute("update user set password='{}' where tel={}".format(newpwd,msisdn))
        sb.session.commit()
        rs = json.dumps({"result":0})
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)


def add_customer():
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

    userid=checkinfo['userid']
    appkey=checkinfo['appkey']
    msisdn=checkinfo['msisdn']
    mode=checkinfo['mode']
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_add_customer= request.get_json()
        else:
            js_add_customer=request.json
    else:
        if request.method=='GET':
            try:
                js_add_customer = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_add_customer = json.loads(request.data.decode('gbk'))

    name=js_add_customer.get('name')
    # name=bytes(name,'ISO-8859-1').decode('GBK')
    tel=js_add_customer.get('tel')
    if len(tel) > 12 and tel.find('-'):
        tel=tel.replace('-','')
    if not tel:
        rs = json.dumps({"result": 1,"msg":"losing lianman tel!"})
        return  make_response(rs)

    acms=js_add_customer.get('acms','')
    if acms:
        if len(acms)<8:
            rs = json.dumps({"result": 1,"msg":"losing lianman tel error!"})
            return  make_response(rs)
        else:
            if mode=='ax':
                axcnt=rd.keys('subs_rela_ax:{}:{}:{}:s'.format(msisdn,acms,appkey))

            if not axcnt:
                rs = json.dumps({"result": 1, "msg": "{} and {} not binding relation!".format(msisdn,acms)})
                return make_response(rs)

    create_date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    code=datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    try:
        sb.session.execute("insert into customer (code,name,source_id,belong_with,tel,user_id,acms,create_date,expire_date,comments)\
                           VALUES('{}','{}',3,'U','{}',{},'{}','{}',(select unsubts from acms where acms='{}' and state='U' and \
                           use_location='A' and  status='V'),'通过小程序增加')".format(code,name,tel,userid,acms,create_date,acms))
        sb.session.commit()
        rs = json.dumps({"result":0})
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result":1,'msg':'insert data error!'})
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)

def del_customer():
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

    userid=checkinfo['userid']
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_delete_customer= request.get_json()
        else:
            js_delete_customer=request.json
    else:
        if request.method=='GET':
            try:
                js_delete_customer = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_delete_customer = json.loads(request.data.decode('gbk'))
    tel=js_delete_customer.get('tel')
    try:
        sb.session.execute("delete from customer where user_id={} and tel='{}'".format(userid,tel))
        sb.session.commit()
        rs = json.dumps({"result":0})
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    return make_response(rs)

def mod_customer():
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

    userid=checkinfo['userid']
    appkey=checkinfo['appkey']
    msisdn=checkinfo['msisdn']

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_mod_customer= request.get_json()
        else:
            js_mod_customer=request.json
    else:
        if request.method=='GET':
            try:
                js_mod_customer = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_mod_customer = json.loads(request.data.decode('utf8'))

    old_tel=js_mod_customer.get('old_tel')
    if not old_tel:
        rs = json.dumps({"result": 1,"msg":"no liankman tel!"})
        return  make_response(rs)

    new_name=js_mod_customer.get('new_name')
    acms=js_mod_customer.get('acms')
    # new_name = bytes(new_name, 'ISO-8859-1').decode('GBK')
    new_tel=js_mod_customer.get('new_tel')
    if len(new_tel) > 12 and new_tel.find('-'):
        new_tel=new_tel.replace('-','')

    try:
        if new_name:
            sb.session.execute("update customer set name='{}' where user_id={} and tel='{}'".format(new_name,userid,old_tel))
        if acms:
            if len(acms) < 8:
                rs = json.dumps({"result": 1, "msg": "losing lianman tel error!"})
                return make_response(rs)
            else:
                axcnt = rd.keys('subs_rela_ax:{}:{}:{}:s'.format(msisdn, acms, appkey))
                if not axcnt:
                    rs = json.dumps({"result": 1, "msg": "{} and {} not binding relation!".format(msisdn, acms)})
                    return make_response(rs)
            sb.session.execute("update customer set acms='{}' where user_id={} and tel='{}'".format(acms,userid,old_tel))

        sb.session.commit()
        if new_tel:
            sb.session.execute("update customer set tel='{}'  where user_id={} and tel='{}'".format(new_tel,userid,old_tel))
        sb.session.commit()
        rs = json.dumps({"result":0})
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    sb.session.close()
    return make_response(rs)

def get_customer():
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

    userid=checkinfo['userid']
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_get_customer= request.get_json()
        else:
            js_get_customer=request.json
    else:
        if request.method=='GET':
            try:
                js_get_customer = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_get_customer = json.loads(request.data.decode('gbk'))
    phone=js_get_customer.get('phone')
    letter=js_get_customer.get('letter')
    logging.info('phone={},letter={}'.format(phone,letter))
    try:
        if phone:
            custinfo=sb.session.execute('''select c.name,c.tel,c.acms,a.unsubts
                                           from customer c
                                           left join acms a on a.acms=c.acms
                                           where c.user_id={} and c.tel like '%{}%' and c.source_id=3'''
                                        .format(userid,phone))
        if letter:
            custinfo=sb.session.execute('''
                                        select g.name,g.tel,g.acms,a.unsubts from
                                        (SELECT  c.name,c.tel,c.acms
                                        FROM customer c, t_coslers t2
                                        WHERE  CONV(HEX(LEFT(CONVERT(c.name USING gbk ), 1)), 16, 10) BETWEEN t2.cBegin AND t2.cEnd
                                               and t2.f_PY=upper('{}') and c.user_id={} and c.source_id=3
                                        ORDER BY convert(c.name using gbk) ASC) g
                                        left acms a on g.acms=a.acms
                                        '''.format(letter,userid))
        if (not phone) and (not letter):
            custinfo=sb.session.execute('''select c.name,c.tel,c.acms,a.unsubts
                                           from customer c
                                           left join acms a on a.acms=c.acms
                                           where c.user_id={} and source_id=3
                                        '''.format(userid))
        ci=[]
        for ic in custinfo:
            d_c = {}
            d_c['name']=ic[0]
            d_c['tel']=ic[1]
            d_c['acms']=ic[2]
            d_c['expire_date']=str(ic[3])
            ci.append(d_c)
    except Exception as ex:
        rs = json.dumps({"result":1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    rs=json.dumps(ci)
    logging.info(rs)
    return rs

def find_cdr():
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

    userid=checkinfo['userid']
    msisdn=checkinfo['msisdn']
    try:
        logging.info(('''
                                        select  case when c.name is  null then cc.otherms else c.name end as 'name',
                                        cc.otherms,date(cc.call_time),cc.call_time,cc.release_time,
                                        (UNIX_TIMESTAMP(`cc`.`release_time`) - UNIX_TIMESTAMP(`cc`.`call_time`)) AS `duration`,
                                        cc.call_type, a.city from
                                        cdr_call cc left join
                                        (select name,tel from customer where source_id=3 and user_id={}) c
                                        on cc.otherms=c.tel  and
                                        date(cc.call_time)>=DATE_SUB(CURDATE(), INTERVAL 1 week) and cc.prtms='{}'
                                        left join area a on a.number=left(cc.otherms,7)
                                        where cc.call_type in ('0','1','128') and (length(cc.otherms)>6 and  length(cc.otherms)<12)
                                        order by cc.call_time desc

                           '''.format(userid,msisdn)))
        call_record=sb.session.execute('''
                                        select  case when c.name is  null then cc.otherms else c.name end as 'name',
                                        cc.otherms,date(cc.call_time),cc.call_time,cc.release_time,
                                        (UNIX_TIMESTAMP(`cc`.`release_time`) - UNIX_TIMESTAMP(`cc`.`call_time`)) AS `duration`,
                                        cc.call_type, a.city from
                                        cdr_call cc left join
                                        (select name,tel from customer where source_id=3 and user_id={}) c
                                        on cc.otherms=c.tel  and
                                        date(cc.call_time)>=DATE_SUB(CURDATE(), INTERVAL 1 week) and cc.prtms='{}'
                                        left join area a on a.number=left(cc.otherms,7)
                                        where cc.call_type in ('0','1','128') and (length(cc.otherms)>6 and  length(cc.otherms)<12)
                                        order by cc.call_time desc
                           '''.format(userid,msisdn))

        d_calls=[]
        j=0
        for i in call_record:
            d_record = {}
            logging.info(i)
            name=i[0]
            tel=i[1]
            date=i[2]
            call_time=i[3]
            release_time=i[4]
            logging.info(release_time)
            duration=i[5]
            call_type=i[6]
            city=i[7]
            d_record['name']=name
            d_record['tel']=tel
            d_record['date']=str(date)
            d_record['call_time']=str(call_time)
            d_record['release_time']=str(release_time)
            d_record['duration']=duration
            d_record['call_type']=call_type
            d_record['city']=city
            d_calls.insert(j,d_record)
            logging.info(d_record)
            j+=1
    except Exception as ex:
        rs = json.dumps({"result": 1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    if d_calls==[]:
        return json.dumps({'msg':'no cdr'})
    logging.info(d_calls)
    rs = json.dumps(d_calls)
    logging.info(rs)
    return rs

def get_userinfo():
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

    userid=checkinfo['userid']
    msisdn=checkinfo['msisdn']
    username=checkinfo['username']
    logging.info(userid)
    try:
        company=sb.session.execute("select value from parameter where parameter_id=901").fetchone()
        company=company[0]
        user_info=sb.session.execute('''select a.acms from user u,acms a,user_acms_rela uar
                               where uar.user_id=u.user_id and uar.acms_id=a.acms_id and uar.state='V' and u.user_id={};
                          '''.format(userid))
        d_u={}
        j=0
        acms_t=None
        for i in user_info:
            acms=i[0]
            if j>0:
                acms_t='{},{}'.format(acms_t,acms)
            else:
                acms_t=acms
            j+=1
        d_u['result']=0
        d_u['name']=username
        d_u['company']=company
        d_u['ms']=msisdn
        d_u['acms']=acms_t
    except Exception as ex:
        rs = json.dumps({"result": 1})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    rs = json.dumps(d_u)
    logging.info(rs)
    return wrap_resp(rs)

def sms_vcode():
    # token=request.headers.get('token')
    # try:
    #     checkinfo=eval(verify_auth_token(token))
    #     logging.info(checkinfo)
    # except Exception as ex:
    #     logging.error(ex)
    #     rs = json.dumps({"result": 1, 'msg': 'token verify error'})
    #     return  make_response(rs)
    # if not checkinfo:
    #     rs = json.dumps({"result": 1,"msg":"token error"})
    #     return  make_response(rs)

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_vcode= request.get_json()
        else:
            js_vcode=request.json
    else:
        if request.method=='GET':
            try:
                js_vcode = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_vcode = json.loads(request.data.decode('gbk'))
    phone=js_vcode['phone']
    r=vcode(phone)
    if r.get('msg')=='success':
        result=0
        msgid=r.get('vid')
        ver_code= rd_sms.get("sms:vcode:{}".format(msgid))
        exptime=(datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        d_u={'vcode':ver_code,'vid':msgid,'exptime':exptime}
    else:
        result=1
    d_u.update({'result':result})
    rs = json.dumps(d_u)
    logging.info(rs)
    return wrap_resp(rs)

def verify_smscode():
    # token=request.headers.get('token')
    # try:
    #     checkinfo=eval(verify_auth_token(token))
    #     logging.info(checkinfo)
    # except Exception as ex:
    #     logging.error(ex)
    #     rs = json.dumps({"result": 1, 'msg': 'token verify error'})
    #     return  make_response(rs)
    # if not checkinfo:
    #     rs = json.dumps({"result": 1,"msg":"token error"})
    #     return  make_response(rs)

    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_verify_sms= request.get_json()
        else:
            js_verify_sms=request.json
    else:
        if request.method=='GET':
            try:
                js_verify_sms = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
        else:
            js_verify_sms = json.loads(request.data.decode('gbk'))
    vid=js_verify_sms.get('vid')
    r_code=js_verify_sms.get('vcode')
    ver_code = rd_sms.get("sms:vcode:{}".format(vid))
    logging.info('ver_code={},rcode={},vid={}'.format(ver_code,r_code,vid))
    if ver_code==r_code:
        rs={'result':0}
    else:
        rs = {'result':1}
    rs = json.dumps(rs)
    logging.info(rs)
    return wrap_resp(rs)

def send_x_sms():
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
    logging.info(msisdn)
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_send_x_sms= request.get_json()
        else:
            js_send_x_sms=request.json
    else:
        if request.method=='GET':
            try:
                js_send_x_sms = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
                rs = {'result': 1, 'msg': 'data is not json'}
        else:
            js_send_x_sms = json.loads(request.data.decode('utf8'))
    acms=js_send_x_sms['acms']
    starttime=js_send_x_sms['starttime']
    content=js_send_x_sms['content']
    peer_no=js_send_x_sms['peer_no']
    content1='{} {} {}'.format(content,msisdn,peer_no)
    logging.info('acms={},starttime={},content={},peer_no={}'.format(acms,starttime,content1,peer_no))
    r=csms(acms,content1)
    if r.get('msg') == 'success':
        rs={'result':0}
        msgid=r.get('msgid')
        try:
            sb.session.execute("insert into micro_sms(msgid,content,peer_no,prtms,acms,send_time)\
                               VALUES('{}','{}',{},'{}','{}','{}')". \
                               format(msgid,content,peer_no,msisdn,acms,starttime))
            sb.session.commit()
        except Exception as ex:
            logging.error(ex)
            rs = json.dumps({"result": 1, 'msg': 'insert micro sms error'})
        finally:
            sb.session.close()
    else:
        if r.get('message'):
            rs = {'result': 1, 'msg': r.get('message')}
        else:
            rs = {'result': 1, 'msg': r.get('msg')}

    rs = json.dumps(rs)
    return wrap_resp(rs)
def query_sms():
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
    userid=checkinfo['userid']
    logging.info(msisdn)
    if request.headers.get('Content-Type') == 'application/json':
        if request.method=='GET':
            js_query_sms= request.get_json()
        else:
            js_query_sms=request.json
    else:
        if request.method=='GET':
            try:
                js_query_sms = request.args.to_dict()
            except Exception as ex:
                logging.warning(ex)
                rs = {'result': 1}
        else:
            js_query_sms = json.loads(request.data.decode('utf8'))
    peer_no=js_query_sms['peer_no']


    try:
        if not peer_no:
            sms_info=sb.session.execute('''select ms.acms,ms.content,ms1.send_time,ms.peer_no,c.name
                                            from micro_sms ms inner join
                                            (select peer_no,prtms,max(send_time) send_time from micro_sms group by peer_no,prtms) ms1
                                            on ms.peer_no=ms1.peer_no and ms.prtms=ms1.prtms and ms.send_time=ms1.send_time
                                            left join customer c on c.tel=ms.peer_no and c.user_id={}
                                            where ms.prtms="{}"'''.format(userid,msisdn))
        else:
            sms_info=sb.session.execute('''select ms.acms,content,send_time,peer_no,name
                              from micro_sms ms
                              left join customer c on c.tel=ms.peer_no and c.user_id={}
                              where ms.prtms="{}" and peer_no="{}"
                              order by  ms.send_time desc'''.format(userid,msisdn,peer_no))
        l_sms=[]
        j=0

        for i in sms_info:
            d_sms = {}
            acms=i[0]
            content=i[1]
            send_time=i[2]
            peer_no=i[3]
            name=i[4]
            d_sms['acms']=acms
            d_sms['content']=content
            d_sms['send_time']=str(send_time)
            d_sms['peer_no']=peer_no
            d_sms['name']=name
            l_sms.append(d_sms)
        rs=json.dumps(l_sms)
    except Exception as ex:
        logging.error(ex)
        rs = json.dumps({"result": 1, 'msg': 'insert micro sms error'})
    finally:
        sb.session.close()
    rs = json.dumps(rs)
    return wrap_resp(rs)

def get_protocl():
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

    rs = json.dumps({"result":0,'protocol':protocal})
    return wrap_resp(rs)

def get_owner_acms():
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
    userid=checkinfo['userid']
    try:
        acmsinfo=sb.session.execute('''select a.acms,c.name,c.tel,a.unsubts
                                    from user_acms_rela uar inner join acms a
                                    on a.acms_id=uar.acms_id
                                    left join customer c
                                    on c.user_id=uar.user_id and c.acms=a.acms
                                    where   uar.user_id={} and a.state='U' and uar.state='V'
                                    '''
                                    .format(userid))
        ci=[]
        for ic in acmsinfo:
            d_c = {}
            d_c['acms']=ic[0]
            d_c['name']=ic[1]
            d_c['tel']=ic[2]
            d_c['unsubts']=str(ic[3])
            ci.append(d_c)
    except Exception as ex:
        rs = json.dumps({"result":1,'msg':'Query db error!'})
        logging.error(ex)
        return make_response(rs)
    finally:
        sb.session.close()
    rs=json.dumps(ci)
    logging.info(rs)
    return rs


def weixin_notify():
    if request.method=='GET':
        try:
            js_notify = request.data.decode('gbk')
        except Exception as ex:
            logging.warning(ex)
    else:
        js_notify = request.data.decode('gbk')
    logging.info(js_notify)
    data=trans_xml_to_dict(js_notify)
    sign_r=data['sign']
    sign_l= pay_sign(data)
    logging.info('sign_r={},sign_l={}'.format(sign_l,sign_r))
    if sign_l==sign_r:
        if data['result_code']=='SUCCESS' and data['return_code']=='SUCCESS':
            rp='''<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'''
            rd_pay.hmset('payment:report:{}'.format(data['out_trade_no']),data)
            try:
                sb.session.execute('''update payment set state='SUCCESS' \
                                      where out_trade_no='{}'
                                   '''.format(data['out_trade_no']))
                sb.session.execute('''
                           update acms
                           set unsubts=(select date_add(ifnull(unsubts,now()), \
                           interval (select days from payment where acms.acms=payment.acms and payment.out_trade_no='{}') day));
                            '''.format(data['out_trade_no']))
                sb.session.commit()
            except Exception as ex:
                logging.error(ex)
                logging.info({"result": 1, 'msg': 'update data error!'})
            finally:
                sb.session.close()
            return rp
    else:
        return '''<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[SIGN ERROR]]></return_msg></xml>'''

def wrap_resp(mmi_resp=None, d={}):
    if mmi_resp is None:
        mmi_resp = d
    resp = make_response(jsonify(mmi_resp), 200)
    return resp
