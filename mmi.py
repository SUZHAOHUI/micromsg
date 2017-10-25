from common import f_log
from database import app
from views import  *
from bind_views import *

#logfile='/data/log/micromsg/mmi.log'
logfile='mmi.log'

# f_log_concurrent(logfile)
f_log(logfile)
from views import user_login

app.secret_key = '6NQO4D1O5RNEPL31IO5PN+2TZQS4BV/A'
app.add_url_rule('/',view_func=hello,methods=['GET','POST'])
app.add_url_rule('/api/login.do',view_func=user_login,methods=['GET','POST'])
app.add_url_rule('/api/changePwd.do',view_func=changePwd,methods=['GET','POST'])
app.add_url_rule('/api/addLinkman.do',view_func=add_customer,methods=['GET','POST'])
app.add_url_rule('/api/delLinkman.do',view_func=del_customer,methods=['GET','POST'])
app.add_url_rule('/api/updateLinkman.do',view_func=mod_customer,methods=['GET','POST'])
app.add_url_rule('/api/getContacts.do',view_func=get_customer,methods=['GET','POST'])
app.add_url_rule('/api/findCdr.do',view_func=find_cdr,methods=['GET','POST'])
app.add_url_rule('/api/userInfo.do',view_func=get_userinfo,methods=['GET','POST'])
app.add_url_rule('/api/getSmsVcode.do',view_func=sms_vcode,methods=['GET','POST'])
app.add_url_rule('/api/VerSmsVcode.do',view_func=verify_smscode,methods=['GET','POST'])
app.add_url_rule('/api/sendSms.do',view_func=send_x_sms,methods=['GET','POST'])
app.add_url_rule('/api/getProtocol.do',view_func=get_protocl,methods=['GET','POST'])
app.add_url_rule('/api/getCityNumber.do',view_func=get_city_number,methods=['GET','POST'])
app.add_url_rule('/api/getCityInfo.do',view_func=get_city_list,methods=['GET','POST'])
app.add_url_rule('/api/setAxBind.do',view_func=ax_bind,methods=['GET','POST'])
app.add_url_rule('/api/unAxBind.do',view_func=ax_unbind,methods=['GET','POST'])
app.add_url_rule('/api/getWeiXinPublic.do',view_func=get_wx_p,methods=['GET','POST'])
app.add_url_rule('/api/notifyHWH',view_func=weixin_notify,methods=['GET','POST'])
app.add_url_rule('/api/vCallReq.do',view_func=vcall_req,methods=['GET','POST'])
app.add_url_rule('/api/getOwerAcms.do',view_func=get_owner_acms,methods=['GET','POST'])
app.add_url_rule('/api/queryTopup.do',view_func=query_topup,methods=['GET','POST'])
app.add_url_rule('/api/getPrice.do',view_func=get_price,methods=['GET','POST'])
app.add_url_rule('/api/querySms.do',view_func=query_sms,methods=['GET','POST'])
app.add_url_rule('/api/userRegister.do',view_func=user_register,methods=['GET','POST'])
app.add_url_rule('/api/companyRegister.do',view_func=company_register,methods=['GET','POST'])

if __name__ == '__main__':
    app.run(debug=True)
    sb.session.close()

