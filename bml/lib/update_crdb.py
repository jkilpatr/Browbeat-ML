import psycopg2


def insert_grades_db(config, uuid, test, osp_name, avg_runtime, grade, time_stamp, puddle, dlrn, concurrency, times):  # noqa
    db_name = config['database'][0]
    user_name = config['user_name'][0]
    host_ip = config['host'][0]
    table =  config['table'][0]
    conn = psycopg2.connect(database=db_name, user=user_name, host=str(host_ip), port=26257)  # noqa
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    classify = True
    cur.execute("INSERT INTO prod_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , (str(uuid), str(test), str(osp_name), float(avg_runtime), str(time_stamp), str(puddle), str(dlrn), bool(classify), int(grade), int(concurrency), int(times)  ))  # noqa


def insert_values_db(config, uuid, test, osp_name, avg_runtime, time_stamp, puddle, dlrn, concurrency, times):  # noqa
    db_name = config['database'][0]
    user_name = config['user_name'][0]
    host_ip = config['host'][0]
    conn = psycopg2.connect(database=db_name, user=user_name, host=str(host_ip), port=26257)  # noqa
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    classify = False
    grade = "NULL"
    cur.execute("INSERT INTO prod_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , (str(uuid), str(test), str(osp_name), float(avg_runtime), str(time_stamp), str(puddle), str(dlrn), bool(classify), None, int(concurrency), int(times)  ))  # noqa

