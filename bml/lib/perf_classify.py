import tensorflow as tf
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run
import functools
import logging
from tensorflow.contrib.hooks import ProfilerHook
import random


#  This function is shamefully messy because it has to deal with all sorts of
#  issues with the data itself as well as enforce a ton of assumptions
def tf_train_uuid(conn, tset, tests):
    FEATURES_PER_TEST = ["_runs", "_concurrency", "_raw"]
    LABEL_COLUMN = "label"
    CATEGORICAL_COLUMNS = ["osp_version"]

    label_column = []
    categorical_columns = {}
    all_test_columns = {}

    for item in CATEGORICAL_COLUMNS:
        categorical_columns[item] = []

    for test in tests:
        for feature in FEATURES_PER_TEST:
            all_test_columns[test['test']+feature] = []

    for benchmark_run in tset:
        b_run = browbeat_run(conn,
                             benchmark_run['uuid'],
                             pass_fail=benchmark_run['category'],
                             caching=True)
        osp_version = None
        if benchmark_run['category'] == "pass":
            label_column.append(1)
        else:
            label_column.append(0)

        for benchmark in tests:
            # These are used to move the dimentionality of the test data up
            # that lets us get away with things like 10 nova boots vs 2000
            # keystone creates, because of this only the number of runs within
            # a test need to agree rather than all runs for all tests. Anything
            # more than this will require down/up sampling data.
            rc = []
            cc = []
            ruc = []
            test_list = b_run.get_tests(test_search=benchmark['test'],
                                        workload_search=benchmark['workload'])
            for test_run in : test_list
                # Times agreement within a test
                if (len(rc) > 0 and \
                    len(rc[0]) != len(test_run.raw)) or \
                    type(test_run.raw) != list:
                    continue
                rc.append(test_run.raw)
                cc.append(test_run.concurrency)
                ruc.append(test_run.run)
                if osp_version is None:
                    osp_version = test_run.version
                    categorical_columns['osp_version'].append(osp_version)
            # Times agreement across runs
            ll = len(all_test_columns[benchmark['test'] + '_raw'])
            if len(rc) > 0 and ll > 0 and ll == len(rc):
                all_test_columns[benchmark['test'] + '_concurrency'].append(cc)
                all_test_columns[benchmark['test'] + '_raw'].append(rc)
                all_test_columns[benchmark['test'] + '_runs'].append(ruc)
        if osp_version is None:
            raise ValueError('UUID ' + \
                             benchmark_run['uuid'] + \
                             ' has no tests that where not skipped')

    # Creates one hot vector for representation of OSP_version
    categorical_columns['osp_version'] = \
        tf.SparseTensor(indices=[[i, 0] for i in range(len(categorical_columns['osp_version']))],
                    values=categorical_columns['osp_version'],
                    dense_shape=[len(categorical_columns['osp_version']), 1])

    # Converts data to tensors, by default uses the largest format of that dtype
    # eg float64, int64 etc
    for column in all_test_columns:
        all_test_columns[column] = tf.constant(all_test_columns[column])
    label_column = tf.constant(label_column)
    data = {}
    data.update(all_test_columns)
    data.update(categorical_columns)
    return data, label_column

# The goal is to classify performance into a number across all tests
def perf_classify(config, es_backend):
    FEATURES_PER_TEST = ["_runs", "_concurrency", "_raw"]
    LABEL_COLUMN = "label"
    CATEGORICAL_COLUMNS = ["osp_version"]
    ALL_TEST_COLUMNS = []
    for test in config['tests']:
        for feature in FEATURES_PER_TEST:
            ALL_TEST_COLUMNS.append(test['test']+feature)

    all_test_columns = []
    for column in ALL_TEST_COLUMNS:
        all_test_columns.append(
            tf.contrib.layers.real_valued_column(ALL_TEST_COLUMNS,
                                                 dtype=tf.float32))

    osp_version = \
        tf.contrib.layers.sparse_column_with_keys(column_name="osp_version",
                                                  keys=["master-director",
                                                        "master-tripleo",
                                                        "11-director",
                                                        "11-tripleo",
                                                        "10-director",
                                                        "10-tripleo",
                                                        "9-director",
                                                        "9-tripleo"])
    osp_version_embed = tf.contrib.layers.embedding_column(osp_version, dimension=8)
    wide_columns=[osp_version]
    deep_columns=[osp_version_embed].extend(all_test_columns)

    partial_train = functools.partial(tf_train_uuid, es_backend, config['training-sets'], config['tests'])
    est = tf.contrib.learn.DNNLinearCombinedClassifier(linear_feature_columns=wide_columns,
                                                      dnn_feature_columns=deep_columns,
                                                      dnn_hidden_units=[2],
                                                      fix_global_step_increment_bug=True)
    partial_eval = functools.partial(tf_train_uuid, es_backend, config['validation-sets'], config['tests'])
    est.fit(input_fn=partial_train, steps=100)
    results = est.evaluate(input_fn=partial_eval, steps=1)
    print(results)
