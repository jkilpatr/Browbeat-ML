from browbeat_run import browbeat_run
from dtree_classifier import classify_value
import numpy
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


def longest_test_name(config):
    val = 0
    for test in config['tests']:
        if len(test['test']) > val:
            val = len(test['test'])
    return val


def time_summary(config, es_backend, time_period, osp_version):
    if osp_version is not None:
        uuids = es_backend.grab_uuids_by_date(osp_version, time_period)
    else:
        uuids = []
        for version in config['watched_versions']:
            uuids.extend(es_backend.grab_uuids_by_date(version, time_period))
    for uuid in uuids:
        val = print_run_details(config, es_backend, uuid)
        if val is not False:
            print(val)


def summary_uuid(es_backend, config, uuid):
    val = print_run_details(config, es_backend, uuid)
    if val is not False:
        print(val)


def data_summary(data):
    std_dev = "{:.4f}".format(numpy.std(data)).ljust(10)
    avg = "{:.4f}".format(numpy.mean(data)).ljust(10)
    median = "{:.4f}".format(numpy.median(data)).ljust(10)
    summary = [avg, std_dev, median]
    return(summary)


# Used for an easy way to look at run data
def print_run_details(config, es_backend, uuid):
    brun = browbeat_run(es_backend, uuid, caching=True)
    output_string = ""
    osp_version = ""
    padding = longest_test_name(config)
    '''
    conn=sqlite3.connect('database.sqlite')
    c=conn.cursor()
    '''
    for test_type in config['tests']:
        test_name = test_type['test']
        data = []
        for test_run in brun.get_tests(test_search=test_name):
            data.extend(test_run.raw)
            osp_version = test_run.version
        statistics_uuid = data_summary(data)
        average_runtime = statistics_uuid[0]
        output_string += test_name.ljust(padding) + \
            " " + str(average_runtime) + " " + str(statistics_uuid[1])
        if float(average_runtime) > 0.0 and test_run.errortype == "result" \
           and test_name != "nova.boot_server" and \
           test_run.cloud_name in config['clouds'] and \
           'pipeline' not in test_run.dlrn_hash and \
           'trunk' not in test_run.dlrn_hash:  # noqa
            if str(test_name) in config['test_with_scenario_list']:
                test_name = str(test_run.scenario_name) + "." + str(test_name)
            output_prediction = classify_value(config, average_runtime, test_name, osp_version)  # noqa
            insert_values_db(config, uuid, test_name, osp_version, average_runtime, output_prediction)  # noqa
            if str(output_prediction[0]) == "1":
                print("ALERT!!!!")
                print(uuid, test_name, osp_version, average_runtime)
                exit(1)
            output_string = output_string + str(output_prediction) + "\n"
        else:
            output_string += "\n"
    '''
    conn.commit()
    conn.close()
    '''
    header = ("Browbeat UUID: " + uuid + " OSP_version: " + osp_version + "\n")
    header += ("".ljust(80, "-")) + "\n"
    output_string = header + output_string
    return output_string
