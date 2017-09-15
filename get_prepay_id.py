import xml.etree.ElementTree as ET
from common import pay_sign
from bs4 import BeautifulSoup

def parse(sxml,secret):
    notify_data_tree = ET.fromstring(sxml)
    return_code = notify_data_tree.find("return_code").text
    if return_code!='FAIL':
        result_code = notify_data_tree.find("result_code").text
    d_r = {}
    if return_code=='SUCCESS' and result_code=='SUCCESS':
        d_r['return_code']=notify_data_tree.find('return_code').text
        d_r['return_msg']=notify_data_tree.find('return_msg').text
        d_r['appid']=notify_data_tree.find("appid").text
        d_r['mch_id'] = notify_data_tree.find("mch_id").text
        d_r['nonce_str'] = notify_data_tree.find("nonce_str").text
        d_r['result_code']=notify_data_tree.find('result_code').text
        d_r['trade_type']=notify_data_tree.find('trade_type').text
        d_r['prepay_id']=notify_data_tree.find('prepay_id').text
        r_sign=notify_data_tree.find('sign').text
        l_sign=pay_sign(d_r,secret)

        if l_sign!=r_sign:
            return {'result':1}

    elif return_code=='SUCCESS':
        d_r['result_code']=notify_data_tree.find('return_code').text
        d_r['return_msg']=notify_data_tree.find('return_msg').text
        d_r['appid']=notify_data_tree.find("appid").text
        d_r['mch_id'] = notify_data_tree.find("mch_id").text
        d_r['nonce_str'] = notify_data_tree.find("nonce_str").text
        d_r['result_code']=notify_data_tree.find('result_code').text
        r_sign=notify_data_tree.find('sign').text
        l_sign=parse(d_r,secret)
        if l_sign!=r_sign:
            return {'result':1}
    else:
        d_r['result_code']=notify_data_tree.find('return_code').text
        d_r['return_msg']=notify_data_tree.find('return_msg').text

    return d_r




def trans_xml_to_dict(xml):
    """
    将微信支付交互返回的 XML 格式数据转化为 Python Dict 对象

    :param xml: 原始 XML 格式数据
    :return: dict 对象
    """
    soup = BeautifulSoup(xml, 'xml')
    xml = soup.find('xml')
    if not xml:
        return {}
    # 将 XML 数据转化为 Dict
    data = dict([(item.name, item.text) for item in xml.find_all()])
    return data



