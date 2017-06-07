import tensorflow as tf
from lib.browbeat_run import browbeat_run
import functools
import lib.util
import logging
# from tensorflow.contrib.hooks import ProfilerHook


#  This function is shamefully messy because it has to deal with all sorts of
#  issues with the data itself as well as enforce a ton of assumptions
def tf_train_uuid(conn, tset, tests):
    FEATURES_PER_TEST = ["_runs", "_concurrency", "_raw"]
    # LABEL_COLUMN = "label" Implied by test structure
    CATEGORICAL_COLUMNS = ["osp_version"]

    label_column = []
    categorical_columns = {}
    all_test_columns = {}

    for item in CATEGORICAL_COLUMNS:
        categorical_columns[item] = []

    for test in tests:
        for feature in FEATURES_PER_TEST:
            all_test_columns[test['test'] + feature] = []

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
            for test_run in test_list:
                # Times agreement within a test
                rc.append(lib.util.scale_values(test_run.raw, 512))
                cc.append(test_run.concurrency)
                ruc.append(test_run.run)
                if osp_version is None:
                    osp_version = test_run.version
                    categorical_columns['osp_version'].append(osp_version)
            con = all_test_columns[benchmark['test'] + '_concurrency']
            prev_run = len(con) > 0
            if prev_run:
                prev_size = len(con[-1])
            if (prev_run and prev_size == len(cc)) or not \
               prev_run and len(cc) > 0:
                con.append(cc)
                all_test_columns[benchmark['test'] + '_raw'].append(rc)
                all_test_columns[benchmark['test'] + '_runs'].append(ruc)
        if osp_version is None:
            message = 'UUID ' + benchmark_run['uuid']
            message += ' has no tests that where not skipped'
            raise ValueError(message)

    # Creates one hot vector for representation of OSP_version
    n = len(categorical_columns['osp_version'])
    categorical_columns['osp_version'] = \
        tf.SparseTensor(indices=[[i, 0] for i in range(n)],
                        values=categorical_columns['osp_version'],
                        dense_shape=[n, 1])

    # Converts data to tensors, by default uses the largest format
    # of that dtype eg float64, int64 etc
    for column in all_test_columns:
        if len(all_test_columns[column]) == 0:
            raise ValueError("No data made it to the network for " + column)
        all_test_columns[column] = tf.constant(all_test_columns[column])
    label_column = tf.constant(label_column)
    data = {}
    data.update(all_test_columns)
    data.update(categorical_columns)
    return data, label_column


# The goal is to classify performance into a number across all tests
def perf_classify(config, es_backend, uuid=None):
    # Take 30% of the data for validation and 70% for training at random
    training_data, validation_data = \
        lib.util.split_data(config['classify-data'],
                            .3)
    if len(validation_data) > len(training_data):
        print("You probably didn't intend to do this")
        exit(1)

    FEATURES_PER_TEST = ["_runs", "_concurrency", "_raw"]
    # LABEL_COLUMN = "label" implied explit here for readability
    # CATEGORICAL_COLUMNS = ["osp_version"] um why isn't this used?
    ALL_TEST_COLUMNS = []
    for test in config['tests']:
        for feature in FEATURES_PER_TEST:
            ALL_TEST_COLUMNS.append(test['test'] + feature)

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
    osp_version_embed = tf.contrib.layers.embedding_column(osp_version,
                                                           dimension=8)
    wide_columns = [osp_version]
    deep_columns = [osp_version_embed].extend(all_test_columns)

    partial_train = functools.partial(tf_train_uuid,
                                      es_backend,
                                      training_data,
                                      config['tests'])

    est = tf.contrib.learn.DNNLinearCombinedClassifier(linear_feature_columns=wide_columns,  # noqa
                                                       dnn_feature_columns=deep_columns,  # noqa
                                                       dnn_hidden_units=[10],  # noqa
                                                       dnn_dropout=0.5,  # noqa
                                                       n_classes=2,  # noqa
                                                       fix_global_step_increment_bug=True)  # noqa
    partial_eval = functools.partial(tf_train_uuid,
                                     es_backend,
                                     validation_data,
                                     config['tests'])

    logging.getLogger().setLevel(logging.INFO)
    est.fit(input_fn=partial_train, steps=10000)
    if uuid is None:
        results = est.evaluate(input_fn=partial_eval, steps=10)
        print(results['accuracy'])
    else:
        partial_predict = functools.partial(tf_train_uuid,
                                            es_backend,
                                            [{'uuid': uuid, 'category': None}],
                                            config['tests'])
        results = est.predict_classes(input_fn=partial_predict)
        for out in results:
            if int(out) == 1:
                print("UUID " + uuid + " has been classified as Passing!")
                exit(0)
            else:
                print("UUID " + uuid + " has been classified as Failing!")
                exit(0)
