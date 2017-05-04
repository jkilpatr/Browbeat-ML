import yaml
import sys
from backend import Backend
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run
import tests
import tensorflow as tf
import numpy as np
from scipy import stats
from itertools import chain
import functools
import pdb

def _load_config(path):
    try:
        stream = open(path, 'r')
    except IOError:
        self.logger.error("Configuration file {} passed is missing".format(path))
        exit(1)
    config = yaml.load(stream)
    stream.close()
    return config

def main():
   config = "config.yml"
   config = _load_config(config)
   es_backend = Backend(config['elastic-host'],config['elastic-port'])
   #tests.perf_classify(config, es_backend)
   tests.perf_predict(config, es_backend, "neutron.create_network")

if __name__ == '__main__':
    sys.exit(main())

