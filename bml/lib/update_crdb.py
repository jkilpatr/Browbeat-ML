from util import connect_crdb


def insert_grades_db(config, uuid, test, osp_name, avg_runtime, grade,
                     time_stamp, puddle, dlrn, concurrency, times,
                     perc95_score):
    conn = connect_crdb(config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    classify = True
    cur.execute("INSERT INTO {} VALUES ('{}', '{}', '{}', {}, '{}', '{}', \
                '{}', '{}', {}, {}, {}, {});" .format(config['table_name'][0],
                                                      str(uuid), str(test),
                                                      str(osp_name),
                                                      float(avg_runtime),
                                                      str(time_stamp),
                                                      str(puddle), str(dlrn),
                                                      bool(classify),
                                                      int(grade),
                                                      int(concurrency),
                                                      int(times),
                                                      float(perc95_score)))


def insert_values_db(config, uuid, test, osp_name, avg_runtime,
                     time_stamp, puddle, dlrn, concurrency, times,
                     perc95_score):
    conn = connect_crdb(config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    classify = False
    cur.execute("INSERT INTO {} (uuid, test, osp_version, avg_runtime, \
                timestamp, rhos_puddle, dlrn_hash, classify, concurrency, \
                times, percentile95) VALUES ('{}', '{}', '{}', {}, '{}', '{}',\
                '{}', '{}', {}, {}, {})" .format(config['table_name'][0],
                                                 str(uuid), str(test),
                                                 str(osp_name),
                                                 float(avg_runtime),
                                                 str(time_stamp), str(puddle),
                                                 str(dlrn), bool(classify),
                                                 int(concurrency), int(times),
                                                 float(perc95_score)))


def insert_errors_db(config, uuid, errors):
    conn = connect_crdb(config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    name_table = config['table_errors'][0]
    cur.execute("INSERT INTO {} VALUES ('{}', {});" .format(name_table,
                                                            str(uuid),
                                                            errors))
