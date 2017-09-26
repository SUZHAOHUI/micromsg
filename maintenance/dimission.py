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
                                   update user set status='I',status_date=now() where code='{}' and set_id='{}';
                                   update user_acms_rela set state='I',state_date=now()
                                   where user_id in (select user_id from user where code='{}')
                                   """.format(empl_id,set_id,empl_id))
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
                        r=f_unbind('wywawj',prtms,acms,"+ZOLLJ/EFIQEVIWM")
                        logging.info(r)

                        if r['result']=='200':
                            sb.session.execute("""
                                               update acms a set a.status='I',status=now()  where acms='{}';
                                               update subs_rela  set state='U',state_date=now() where anum='{}' and xnum='{}' and state='B';
                                               """.format(acms,acms,prtms,empl_id,set_id,empl_id,set_id))
                sb.session.execute("""
                                   insert into emp_dismission_his
                                   select * from emp_dismission where empl_id='{}' and set_id='{}';
                                   delete from emp_dismission where empl_id='{}' and set_id='{}';
                                   """.format(empl_id,set_id,empl_id,set_id))
                sb.session.commit()
            except Exception as ex:
                logging.info(ex)
            cnt+=1
            logging.info(cnt)
            logging.info('update dismission success!')
    except Exception as ex:
        logging.info(ex)
    finally:
        sb.session.close()

def get_personal_ad():
    try:
        sb.session.execute("""
                drop table if exists temp_empl;
                create table temp_empl
                select e.empl_id,ep1.name_format,ep1.sex,ep1.set_id,
                case when ep1.set_id='10002' then ep1.c_mobile else e.c_mobile end 'c_mobile'
                from erp e ,
                (select name_format,sex,set_id,empl_id,c_mobile,transfer_date_time
                from emp_personal) ep1 ,
                (select empl_id,max(transfer_date_time) transfer_date_time
                from emp_personal group by empl_id) ep2
                where e.empl_id=ep1.empl_id
                and ep1.empl_id=ep2.empl_id
                and ep1.transfer_date_time=ep2.transfer_date_time;

                drop table if exists temp_user;
                create table temp_user
                select ed.dept_id,ep.empl_id,ep.name_format,ep.sex ,vdi.descr,'V' status,current_date() create_date,ep.c_mobile,ep.set_id
                from
                ( select distinct * from temp_empl) ep
                inner join
                (select ed2.empl_id,ed2.dept_id,ed2.hr_status,ed2.setid_job_code set_id,ed2.job_code from
                (select empl_id,max(transfer_date_time) transfer_date_time
                from emp_duty where hr_status='A' group by empl_id) ed1
                inner join emp_duty ed2
                on ed1.empl_id=ed2.empl_id and ed1.transfer_date_time=ed2.transfer_date_time  ) ed
                on ep.empl_id=ed.empl_id and ep.set_id=ed.set_id
                inner join v_duty_info vdi
                on vdi.job_code=ed.job_code and vdi.set_id=ed.set_id
                where ed.hr_status='A';

                update user u,temp_user t
                set u.duty=t.descr
                where u.code=t.empl_id;

                insert into user(org_id,code,name,sex,duty,status,status_date,tel,set_id)
                select * from temp_user tu where not exists (select 1 from user u where u.code=tu.empl_id);

                delete from user_role;
                insert into user_role
                select u.user_id,role_id,'V',now() from
                (select user_id,duty from user where duty in ('经纪人','店经理','区经理','区总监','管理员')) u
                inner join role on  role.role_name= u.duty;
             """)
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
            drop table  if exists temp_dept;

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
            FROM
            (select CAST(dt1.tree_node AS SIGNED integer) as tree_node ,
                        case when dt1.parent_node_name = 'null' then '0' else dt1.parent_node_name end as parent_node_name,
                        di.descr,
                        'V' status,
                        now() status_date,1 operator,dt1.set_id AS set_id ,dt1.transfer_date_time
            from
            (select set_id,tree_node,max(transfer_date_time) transfer_date_time ,max(effdt) effdt,parent_node_name from dept_tree
            group by set_id,tree_node,parent_node_name) dt1
            inner join (select set_id,tree_node,max(transfer_date_time) transfer_date_time,max(effdt) effdt
            from dept_tree
            group by set_id,tree_node) dt2
            on dt1.tree_node=dt2.tree_node
            and dt1.set_id = dt2.set_id
            and dt1.transfer_date_time=dt2.transfer_date_time
            and dt1.effdt = dt2.effdt
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
              on di.dept_id=dt1.tree_node and dt1.set_id=di.set_id) dept
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