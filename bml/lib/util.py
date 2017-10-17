import yaml
import logging
import numpy
import random
import requests
import psycopg2
from datetime import date


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
