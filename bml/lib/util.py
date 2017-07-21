import yaml
import logging
import numpy
import random
from browbeat_run import browbeat_run
import psycopg2
from datetime import date


def is_power_of_two(num):
    log = numpy.log2(num)
    if log - int(log) > 0:
        return False
    else:
        return True


# Takes a list, vals of arbitrary size scales it up or down to `size`
def scale_values(vals, size):
    # Scale up
    if len(vals) < size:
        while len(vals) < size:
            vals = vals + vals
        return vals[:size]
    # Scale down
    elif len(vals) > size:
        return vals[:size]
    # List is the correct size already
    else:
        return vals


# Takes an input data set, returns two datasets taken randomly
def split_data(data_set, split=.5):
    a = []
    b = []
    for thing in data_set:
        if random.random() > split:
            a.append(thing)
        else:
            b.append(thing)
    return a, b


def longest_scenario_test_name(config):
    val = 0
    test_dic = config['test_name_dic']
    for key in test_dic:
        for value in key:
            if len(value) > val:
                val = len(value)
    return val


def longest_test_name(config):
    val = 0
    for test in config['tests']:
        if len(test['test']) > val:
            val = len(test['test'])
    return val


def date_valid(input_date, time_days):
    input_date = input_date.split("T")[0].split("-")
    year = input_date[0]
    month = input_date[1]
    day = input_date[2]
    input_date = date(int(year), int(month), int(day))
    today = date.today()
    difference = today - input_date
    if difference.days <= time_days:
        return True
    return False


# takes a list of uuids, returns list of run objects
def uuids_to_runs(uuids, es_backend, caching=False):
    for uuid in uuids:
        yield browbeat_run(es_backend, uuid, caching=caching)


def load_config(path):
    try:
        stream = open(path, 'r')
    except IOError:
        logging.critial("Configuration file {} passed is missing".format(path))
        exit(1)
    config = yaml.load(stream)
    stream.close()
    return config


def connect_crdb(config):
    db_name = config['database'][0]
    user_name = config['user_name'][0]
    host_ip = config['host'][0]
    conn = psycopg2.connect(database = db_name, user = user_name,
                            host = str(host_ip), port = 26257)
    conn.set_session(autocommit=True)
    return conn
