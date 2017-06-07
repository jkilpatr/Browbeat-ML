import tensorflow as tf
import numpy
from lib.browbeat_run import browbeat_run
import lib.util
import functools
import logging


# Finds a specified action trains itself on all data for that action in Elastic
def tf_train_action(conn, action, uuids):
    NUMERICAL_FEATURES = ["run",
                          "concurrency",
                          "nodes",
                          "undercloud_cores",
                          "undercloud_mem",
                          "compute_cores",
                          "compute_mem",
                          "controller_cores",
                          "controller_mem"]

    # PREDICTON_FEATURE = "average_raw"

    CATEGORICAL_FEATURES = ["osp_version",
                            "undercloud_processor_type",
                            "compute_processor_type",
                            "controller_processor_type",
                            "os_name",
                            "undercloud_make",
                            "compute_make",
                            "controller_make"]

    prediction_column = []
    data = {}
    for column in NUMERICAL_FEATURES:
        data[column] = []
    for column in CATEGORICAL_FEATURES:
        data[column] = []

    n = 0
    for uuid in uuids:
        print("Building data for " + uuid + " " + str(n) + " samples so far")
        test_runs = browbeat_run(conn,
                                 uuid,
                                 caching=False).get_tests(test_search=action)
        for test_run in test_runs:
            if type(test_run.raw) is not list:
                continue
            n = n + 1
            data['run'].append(test_run.run)
            # data['raw'].append(scale_values(test_run.raw, 512))
            prediction_column.append(numpy.mean(test_run.raw))
            data['concurrency'].append(test_run.concurrency)
            data['nodes'].append(test_run.nodes)
            data['os_name'].append(test_run.os_name)
            data['osp_version'].append(test_run.version)

            data['undercloud_cores'].append(
                test_run.undercloud['cores'])
            data['undercloud_mem'].append(
                test_run.undercloud['mem'])
            data['undercloud_make'].append(
                test_run.undercloud['machine_make'])
            data['undercloud_processor_type'].append(
                test_run.undercloud['processor_type'])

            data['compute_cores'].append(
                test_run.compute['cores'])
            data['compute_mem'].append(
                test_run.compute['mem'])
            data['compute_make'].append(
                test_run.compute['machine_make'])
            data['compute_processor_type'].append(
                test_run.compute['processor_type'])

            data['controller_cores'].append(
                test_run.controller['cores'])
            data['controller_mem'].append(
                test_run.controller['mem'])
            data['controller_make'].append(
                test_run.controller['machine_make'])
            data['controller_processor_type'].append(
                test_run.controller['processor_type'])

    for column in NUMERICAL_FEATURES:
        data[column] = tf.constant(data[column])

    for column in CATEGORICAL_FEATURES:
        data[column] = tf.SparseTensor(
            indices=[[i, 0] for i in range(len(data[column]))],
            values=data[column],
            dense_shape=[len(data[column]), 1])

    prediction_column = tf.constant(prediction_column)

    return data, prediction_column


# The goal is to predict the average time taken for an action given hardware
def perf_predict(config, es_backend, action):
    NUMERICAL_FEATURES = ["run",
                          "concurrency",
                          "nodes",
                          "undercloud_cores",
                          "undercloud_mem",
                          "compute_cores",
                          "compute_mem",
                          "controller_cores",
                          "controller_mem"]

    # PREDICTON_FEATURE = "average_raw"

    CATEGORICAL_FEATURES = ["osp_version",
                            "undercloud_processor_type",
                            "compute_processor_type",
                            "controller_processor_type",
                            "os_name",
                            "undercloud_make",
                            "compute_make",
                            "controller_make"]

    numerical_columns = []
    for column in NUMERICAL_FEATURES:
        numerical_columns.append(
            tf.contrib.layers.real_valued_column(column,
                                                 dtype=tf.float32))

    categorical_columns = []
    embedding = False
    for column in CATEGORICAL_FEATURES:
        if embedding:
            categorical_columns.append(tf.contrib.layers.embedding_column(
                tf.contrib.layers.sparse_column_with_hash_bucket(
                    column, hash_bucket_size=25), dimension=8))
        else:
            categorical_columns.append(
                tf.contrib.layers.sparse_column_with_hash_bucket(
                    column, hash_bucket_size=25))

    wide_columns = []
    deep_columns = []
    deep_columns.extend(categorical_columns)
    deep_columns.extend(numerical_columns)
    wide_columns.extend(numerical_columns)

    all_action_uuids = es_backend.get_uuids_by_action(action)
    train_set, validate_set = lib.util.split_data(all_action_uuids)

    partial_train = functools.partial(tf_train_action,
                                      es_backend,
                                      action,
                                      train_set)

    est = tf.contrib.learn.LinearRegressor(feature_columns=deep_columns)
    logging.getLogger().setLevel(logging.INFO)
    # hooks = [ProfilerHook(save_steps=10, output_dir="profiling")]
    est.fit(input_fn=partial_train, steps=1000000, monitors=None)
    partial_eval = functools.partial(tf_train_action,
                                     es_backend,
                                     action,
                                     validate_set)
    results = est.evaluate(input_fn=partial_eval, steps=1)
    print(results)
