from xml.etree import ElementTree as etree
from xml.etree.ElementTree import  Element, SubElement, ElementTree
import uuid
import os
from common import pay_sign
import base64
import xml.etree.ElementTree as ET

def gen_xml(input_dict,root_tag='xml'):
    root_name = ET.Element(root_tag)
    for key, val in input_dict.items():
        key = ET.SubElement(root_name, key)
        key.text = val
    rough_string = ET.tostring(root_name, 'utf-8')
    return rough_string.decode()

if __name__ == '__main__':
    d_unifiedorder={}
    key='08e6e433ac44fe1967467d7bb2589746'
    d_unifiedorder['appid']='wx2421b1c4370ec43b'  #小程序ID
    d_unifiedorder['mch_id']='gh_b90f61edf97e'    #商户号
    d_unifiedorder['nonce_str']=base64.b64encode(os.urandom(24)).upper().decode()
    d_unifiedorder['body']='号外号-虚拟号码'
    d_unifiedorder['out_trade_no']=uuid.uuid3(uuid.NAMESPACE_DNS,'haowaihaoweixinxiaochengxu').hex.upper()
    d_unifiedorder['total_fee']='1'
    d_unifiedorder['spbill_create_ip']='127.0.0.1'
    d_unifiedorder['notify_url']='https://www.haowaihao.com.cn/api/notify'
    d_unifiedorder['trade_type']='JSAPI'
    sign=pay_sign(d_unifiedorder,key)
    d_unifiedorder['sign']=sign
    xmltext=gen_xml(d_unifiedorder)
    print(xmltext)







