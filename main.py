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
   feature_columns = []
   feature_columns.append(tf.contrib.layers.real_valued_column('raw', dimension=2500))
   feature_columns.append(tf.contrib.layers.real_valued_column('concurrency'))
   feature_columns.append(tf.contrib.layers.real_valued_column('runs'))
   #feature_columns.append(tf.contrib.layers.embedding_column(
   #                       tf.contrib.layers.sparse_column_with_hash_bucket(column_name='osp_version',
   #                                                                                  hash_bucket_size=8,
   #                                                                                  combiner="sqrtn"), 8))
   #feature_columns.append(tf.contrib.layers.real_valued_column(column_name='outcome'))
   es_backend = Backend(config['elastic-host'],config['elastic-port'])
   #estimator = tf.contrib.learn.DNNClassifier(feature_columns=feature_columns,
   #                                           hidden_units=[64, 32])
   estimator = tf.contrib.learn.LinearClassifier(feature_columns=feature_columns)

   partial_train = functools.partial(tests.tf_svm_train, es_backend, config['training-sets'])
   estimator.fit(input_fn=partial_train)
   partial_eval = functools.partial(tests.tf_svm_train, es_backend, config['validation-sets'])
   estimator.evaluate(input_fn=partial_eval)


if __name__ == '__main__':
    sys.exit(main())

