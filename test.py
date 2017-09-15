import datetime
from datetime import timedelta
from database import sb
def get_expire_date(acms):
    try:
        unsubts = sb.session.execute("""
              select unsubts from acms where use_location='A' and state='U' and acms='{}'
               """.format(acms))
        for i in unsubts:
            expire_date = i[0]
    except Exception as ex:
        print(ex)
        return 0
    finally:
        sb.session.close()
    return expire_date



acms='13100504065'
days=3
expire_date = get_expire_date(acms)
current_date = datetime.datetime.now()
if not expire_date:
    expire_date = current_date
expire_date = expire_date + timedelta(days=int(days))
expire_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')

print(expire_date)
