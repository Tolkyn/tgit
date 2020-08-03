import requests
import pyodbc
import datetime
from datetime import timedelta
from datetime import datetime
import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


default_args= {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020,7,28),
    'email': ['airflow@example.com'],
    'retries':2}


dag = DAG('Mult_func_parsing',
    default_args=default_args,
    description='This DAG will help u to find errors', catchup=False, 
    schedule_interval='@daily')
    


def Token(**contex):
    URL_1 = 'https://www.ets-tender.kz/integration/json/User.Login/?login=galym.b@geometry.kz&password=Geometry987'
    headers_1 = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(URL_1, headers=headers_1)
    rr = r.json()
    token = rr['access_token']
    tokens = ('Bearer' + ' ' + rr['access_token'])
    print("First funct works")
    
    
    contex['ti'].xcom_push(key='SendToken', value=token)
    contex['ti'].xcom_push(key='SendTokens', value=tokens)
    
    return token,tokens


def ID(**contex):

    token=contex['ti'].xcom_pull(key='SendToken', task_ids='Token')
    tokens=contex['ti'].xcom_pull(key='SendTokens', task_ids='Token')
    
    today = datetime.now()
    d_from = datetime(2020, 7, 1)
    d_to=d_from + timedelta(days=7)
    
    sett = []
    
    while  int(d_to.timestamp()) <= int(today.timestamp()):
        print('from:', d_from)
        print('To', d_to)
        to= int(d_to.timestamp())
        from_=int(d_from.timestamp())
        print('Token:', token)
        print('Tokens:',tokens)

        URL_2 = 'https://www.ets-tender.kz/integration/json/TradeProcedures.GetList?access_token=' + str(token) + '&date_from=' + str(from_) + '&date_to=' + str(to)
        d_from = d_from + timedelta(days=7)
        d_to=d_from+timedelta(days=7)
        headers_2 = {'Authorization': 'Bearer  $ACCESS_TOKEN'}
        headers_2['Authorization'] = tokens
        r_2 = requests.get(URL_2, headers=headers_2)
        r_2 = r_2.json()
        print('IT IS R2:', r_2)
        r_2 = r_2['trade_list']
        for i in r_2:
            ID = i['id']
            sett.append(ID)
    else:

        d_from=d_from
        d_to=today
        to= int(d_to.timestamp())
        from_=int(d_from.timestamp())
        print( 'From:', d_from)
        print('To:', d_to)

        URL_2 = 'https://www.ets-tender.kz/integration/json/TradeProcedures.GetList?access_token=' + str(token) + '&date_from=' + str(from_) + '&date_to=' + str(to)
        d_from = d_from + timedelta(days=7)
        d_to=d_from+timedelta(days=7)
        headers_2 = {'Authorization': 'Bearer  $ACCESS_TOKEN'}
        headers_2['Authorization'] = tokens
        r_2 = requests.get(URL_2, headers=headers_2).json()
        r_2 = r_2['trade_list']
        for i in r_2:
            ID = i['id']
            sett.append(ID)
    print(len(sett), sett)
    contex['ti'].xcom_push(key='Send_sett', value=sett)
    return sett
    

def Connector(**contex):
    token=contex['ti'].xcom_pull(key='SendToken', task_ids='Token')
    tokens=contex['ti'].xcom_pull(key='SendTokens', task_ids='Token')
    sett=contex['ti'].xcom_pull(key='Send_sett', task_ids='ID_of_b')
    
    dsn = 'sqlserverdatasource'
    user='sa'
    password = 'P@ssw0rd@2020'
    database = 'expDB'
    con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;'% (dsn, user, password, database)
    cnxn = pyodbc.connect(con_string)
    print (len(sett), sett)
    for j in sett:
        print('J:', j)
        URL_3 = 'https://www.ets-tender.kz/integration/json/TradeProcedures.GetShortTrade?access_token=' + str(token) + '&id=' + str(j)
        headers_2 = {'Authorization': 'Bearer  $ACCESS_TOKEN'}
        
        headers_2['Authorization'] = tokens
        r_3 = requests.get(URL_3, headers=headers_2)
        r_3 = r_3.json()
        data = r_3['short_trade_procedure']
        
        query = 'insert into Tender_(id, number, _description, _type, procedure_place, trade_type, federal_law, organizer_name, organizer_iin, organizer_kpp, organizer_country, customer_name, customer_iin, customer_kpp, customer_country, _status, date_begin, date_end, date_trade_end, payment_terms, currency, alternate_offer, _url, lots_id, lots_description, lots_delivery_place, lots_quantity, lots_unit_name, lots_price, lots_price_no_tax, positions,os_number, os_name, publish_date, change_date, comment, delivery_address) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        print('norm')
        args = (str(data['id']), data['number'], data['description'], str(data['type']), data['procedure_place'], data['trade_type'], data['federal_law'], data['organizer']['name'], str(data['organizer']['inn']), data['organizer']['kpp'], str(data['organizer']['country']), data['customer']['name'], str(data['customer']['inn']), data['customer']['kpp'], str(data['customer']['country']), data['status'], str(data['date_begin']),  str(data['date_end']), str(data['date_trade_end']), data['payment_terms'], data['currency'], str(data['alternate_offer']), data['url'], str(data['lots'][0]['id']), data['lots'][0]['name'], data['lots'][0]['description'], data['lots'][0]['delivery_place'][0], str(data['lots'][0]['quantity']), data['lots'][0]['unit_name'], str(data['lots'][0]['price']), str(data['lots'][0]['price_no_tax']), data['os_number'], data['os_name'], str(data['publish_date']), str(data['change_date']), data['comment'], str(data['delivery_address']))
        cnxn.execute(query, args)
        cnxn.commit()

task_1=PythonOperator(task_id='Token', provide_context=True, python_callable= Token, dag=dag)
task_2=PythonOperator(task_id='ID_of_b', provide_context=True, python_callable= ID, dag=dag)
task_3=PythonOperator(task_id='SQL_connector', provide_context=True, python_callable= Connector, dag=dag)

task_1>>task_2
task_2>>task_3

print("the end programm")




