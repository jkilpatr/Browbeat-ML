import yaml
import logging
import numpy
import random
from browbeat_run import browbeat_run
import psycopg2


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
    conn = psycopg2.connect(database=db_name, user=user_name,
                            host=str(host_ip), port=26257)
    return conn
