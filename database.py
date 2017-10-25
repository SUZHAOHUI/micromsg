import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
redis_connstr='redis://:acsystem@101.201.101.70:6379/0'
redis_pool = redis.ConnectionPool.from_url(redis_connstr, decode_responses=True)
rd = redis.StrictRedis(connection_pool=redis_pool)


redis_connstr_sms='redis://:acsystem@101.200.221.216:6379/1'
redis_pool_sms = redis.ConnectionPool.from_url(redis_connstr_sms, decode_responses=True)
rd_sms = redis.StrictRedis(connection_pool=redis_pool_sms)

redis_connstr_pay='redis://:acsystem@101.201.101.70:6379/4'
redis_pool_pay = redis.ConnectionPool.from_url(redis_connstr_pay, decode_responses=True)
rd_pay = redis.StrictRedis(connection_pool=redis_pool_pay)



#app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://dev:1q2w!Q@W@101.201.101.70:3306/icrm?charset=utf8'
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://dev:java.ucrm1234@101.200.221.216:3306/gcrm?charset=utf8'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True
sb=SQLAlchemy(app)






