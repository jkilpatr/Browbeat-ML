import psycopg2


def insert_values_db(config, uuid, test, osp_name, avg_runtime, grade):
    db_name = config['database'][0]
    user_name = config['user_name'][0]
    host_ip = config['host'][0]
    conn = psycopg2.connect(database=db_name, user=user_name, host=str(host_ip), port=26257)  # noqa
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS grades (uuid STRING, test STRING, osp_name STRING, avg_runtime FLOAT, grade INT)")  # noqa
    cur.execute("INSERT INTO grades (uuid, test, osp_name, avg_runtime, grade) VALUES (%s, %s, %s, %s, %s)" , (str(uuid), str(test), str(osp_name), float(avg_runtime), int(grade)))  # noqa

