import sys
import logging
import logging.handlers
# sys.path.append("/data/micromsg")
from database import sb,rd
from common import f_unbind,f_log
# f_log('/data/log/aci/dimission.log')
f_log('dimission.log')
def get_dimission_info():
    try:
        dimission_info = sb.session.execute("SELECT DISTINCT set_id,empl_id FROM emp_dismission").fetchall()
        cnt=0
        for i in dimission_info:
            empl_id=i[1]
            set_id=i[0]
            logging.info('empl_id={},set_id={}'.format(empl_id,set_id))
            try:
                sb.session.execute("""
                                   update user set status='I' where code='{}' and set_id='{}';
                                   update user_acms_rela set state='I'
                                   where user_id in (select user_id from user where code='{}')
                                   """.format(empl_id,set_id,empl_id))
                sb.session.commit()
                xai=sb.session.execute("""
                            select acms,sr.anum from user u,user_acms_rela uar,acms a,subs_rela sr
                            where u.user_id = uar.user_id
                              and uar.acms_id = a.acms_id
                              and sr.xnum=a.acms
                              and sr.state='B'
                              and u.code='{}'
                """.format(empl_id)).fetchall()
                logging.info('aaa')
                logging.info(xai)
                for j in xai:
                    acms=j[0]
                    prtms=j[1]

                    if acms and prtms:
                        r=f_unbind('wywiwj',prtms,acms,"+ZOLLJ/EFIQEVIWM")
                        logging.info(r)

                    sb.session.execute("""
                                       update acms a set a.status='I' where acms='{}';
                                       update subs_rela  set state='U',state_date=now() where anum='{}' and xnum='{}' and state='B';
                                       """.format(acms,acms,prtms,empl_id,set_id,empl_id,set_id))
                sb.session.execute("""
                                   insert into emp_dismission_his
                                   select * from emp_dismission where empl_id='{}' and set_id='{}';
                                   delete from emp_dismission where empl_id='{}' and set_id='{}';
                                   """.format(empl_id,set_id,empl_id,set_id))
                sb.session.commit()
            except Exception as ex:
                print(ex)
            cnt+=1
            logging.info(cnt)
            logging.info('update dismission success!')
    except Exception as ex:
        logging.info(ex)
    finally:
        sb.session.close()
def get_personal_ad():
    last_batchnum=rd.get('emp_personal')
    try:
        sb.session.execute("""
            drop table if exists temp_empl;
            create table temp_empl
            select e.empl_id,ep.name_format,ep.sex,ep.set_id,e.c_mobile
            from erp e ,
            (select name_format,sex,set_id,empl_id
            from emp_personal ep0 where batch_num>{} and
            not exists (select 1 from user where code=ep0.empl_id)) ep
            where e.empl_id=ep.empl_id ;
            insert into user(org_id,code,name,sex,duty,status,status_date,tel,set_id)
            select ed.dept_id,ep.empl_id,ep.name_format,ep.sex ,drr.name,'V',current_date(),ep.c_mobile,ep.set_id
            from
            temp_empl ep
            inner join
            (select ed2.empl_id,ed2.dept_id,ed2.job_code,ed2.hr_status,ed2.setid_job_code,ed2.c_quarters_id from
            (select empl_id,max(transfer_date_time) transfer_date_time
            from emp_duty group by empl_id) ed1
            inner join emp_duty ed2
            on ed1.empl_id=ed2.empl_id and ed1.transfer_date_time=ed2.transfer_date_time  ) ed
            on ep.empl_id=ed.empl_id and ep.set_id=ed.setid_job_code
            inner join duty_role_rela drr
            on drr.c_quarters_id=ed.c_quarters_id and drr.set_id=ed.setid_job_code
            where ed.hr_status='A' ;
             """.format(int(last_batchnum)))
        sb.session.commit()
        batch_num_i=sb.session.execute("select max(batch_num) from emp_personal").fetchone()
        batch_num_max=batch_num_i[0]
        rd.set('emp_personal',batch_num_max)
        logging.info('update personal success!')

    except Exception as ex:
        logging.info(ex)
    finally:
        sb.session.close()

def get_org_al():
    try:
        sb.session.execute("""
            drop table temp_dept;
            create table temp_dept
            as
                select
                 dept.tree_node,
                 CAST(dept.parent_node_name AS SIGNED integer) as parent_node_name,
               descr,
                 status,
                 status_date,
                 operator,
                 set_id,
                 transfer_date_time
                from
                (select CAST(dt.tree_node AS SIGNED integer) as tree_node ,
                        case when dt.parent_node_name = 'null' then '0' else dt.parent_node_name end as parent_node_name,
                        di.descr,
                        'V' status,
                        now() status_date,1 operator,dt.set_id AS set_id ,dt.transfer_date_time
                 from
                 (select dt1.* from dept_tree dt1
                 inner join (select set_id,tree_node,max(transfer_date_time) transfer_date_time
                             from dept_tree
                             group by set_id,tree_node) dt2
               on dt1.tree_node=dt2.tree_node
                 and dt1.set_id = dt2.set_id
                 and dt1.transfer_date_time=dt2.transfer_date_time) dt
                inner join
                  (select di2.* from
                  (select dept_id,set_id,max(transfer_date_time) transfer_date_time
                from dept_info
                where eff_status='A'
                group by dept_id,set_id) di1
                inner join
                dept_info di2
                on di1.dept_id=di2.dept_id
                and di1.set_id=di2.set_id
                and di1.transfer_date_time=di2.transfer_date_time
                ) di
                  on di.dept_id=dt.tree_node and dt.set_id=di.set_id) dept
                  where dept.descr is not null;
            delete from org;
            insert into org (org_id,parent_org_id,org_name,status,status_date,operator,set_id)
            select  t2.tree_node,t2.parent_node_name,t2.descr,t2.status,t2.status_date,t2.operator,t2.set_id
            from
            (select tree_node,parent_node_name,set_id,max(transfer_date_time) transfer_date_time
            from temp_dept
            group by tree_node,parent_node_name,set_id) t1
            inner join temp_dept t2
            on t1.tree_node=t2.tree_node
            and t1.parent_node_name=t2.parent_node_name
            and t1.set_id=t2.set_id
            and t1.transfer_date_time=t2.transfer_date_time;
             """)
        sb.session.commit()
        logging.info('update org success!')
    except Exception as ex:
        logging.info(ex)
    finally:
        sb.session.close()



if __name__ == '__main__':
    # get_personal_ad()
    get_dimission_info()
    #get_org_al()