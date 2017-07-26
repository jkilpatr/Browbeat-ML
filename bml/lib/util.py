import yaml
import logging
import numpy
import random
import requests
import psycopg2
from datetime import date


def is_power_of_two(num):
    log = numpy.log2(num)
    if log - int(log) > 0:
        return False
    else:
        return True


def list_metrics(graphite_url, metric):
    metrics_list = []
    for submetric in get_submetrics(metric, graphite_url):
        if submetric['leaf'] == 1:
            metrics_list.extend([submetric['id']])
        else:
            children = list_metrics(graphite_url,
                                    submetric['id'])
            metrics_list.extend(children)
    return metrics_list


# Helper function for navigating metric trees, returns children or None
def get_submetrics(metric_id, graphite_url):
    metrics_url = "{}/metrics/find?query={}.*".format(graphite_url,
                                                      metric_id)
    response = requests.get(metrics_url).json()
    return response


def compress_timeseries(uncompressed):
    compressed = []
    for point in uncompressed:
        if point[0] is not None:
            compressed.append(point)
    return compressed


def get_raw_metrics(metric_id, graphite_url, start, end):
    base_url = "{}/render?target={}&format=json&from={}&until={}"
    data_url = base_url.format(graphite_url,
                               metric_id,
                               start,
                               end)
    response = requests.get(data_url).json()
    if len(response) > 0:
        response = response[0]
    else:
        return None
    compressed = compress_timeseries(response['datapoints'])
    response['datapoints'] = compressed
    return response


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
    conn = psycopg2.connect(database=db_name, user=user_name,
                            host=str(host_ip), port=26257)
    conn.set_session(autocommit=True)
    return conn


# WIP make it loop through all the ignore_tests and it's not one of em
def test_ignore_check(test, config):
    for tests in config['ignored_tests']:
        if tests in test:
            return False
    return True
