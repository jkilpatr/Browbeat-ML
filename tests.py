import tensorflow as tf
import numpy
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run
import functools
from backend import Backend
import logging
from tensorflow.contrib.hooks import ProfilerHook
import random

# This file is where test functions go

def is_power_of_two(num):
    log = numpy.log2(num)
    if log - int(log) > 0:
        return False
    else:
        return True

# Takes a list, vals of arbitrary size scales it up or down to `size`
# Takes only power of 2 values right now, super simple, probably
# want to do interpolation or somthing before seriously using it.
def scale_values(vals, size):
    if not is_power_of_two(len(vals)) or not is_power_of_two(size):
        raise ValueError('len(vals)=' + str(len(vals)) + ' size=' + str(size))
    # Scale up
    elif len(vals) < size:
        return list(scale_values(vals+vals, size))
    # Scale down
    elif len(vals) > size:
        return list(scale_values([vals[x] for x in range(int(len(vals)/2))], size))
    # List is the correct size already
    else:
        return vals

# Takes an input data set, returns two datasets taken randomly
def split_data(data_set):
    a = []
    b = []
    for thing in data_set:
        if random.random() > .5:
            a.append(thing)
        else:
            b.append(thing)
    return a, b


# Dead simple test, tells you if two tests are significantly different
def pass_fail(conn, workload, test, A, B):
    A_tests = list(A.get_tests(workload_search=workload, test_search=test))
    B_tests = list(B.get_tests(workload_search=workload, test_search=test))
    A_tests.sort(key=lambda x: x.concurrency)
    B_tests.sort(key=lambda x: x.concurrency)
    for A_test, B_test in zip(A_tests,
                              B_tests):
        if A_test.concurrency != B_test.concurrency:
            print("Tests not comparable because of concurrency!")
            continue
        elif A_test.run != B_test.run:
            print("Tests not comparable because of run!")
            continue
        elif A_test.times != B_test.times:
            print("Tests not comparable because of times!")
            continue
        t, p = stats.ttest_ind(A_test.raw, B_test.raw, equal_var=False)

        print("Test: " + test + " at concurrency " + str(A_test.concurrency) +" has a p value of " + str(p))
        if(p < .5):
            print("These uuid's are statistically different!")
        else:
            print("These are statistically similar!")

# tf.learn training function, grabs a series of tests from a series of uuids
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
        b_run = browbeat_run(conn, benchmark_run['uuid'], pass_fail=benchmark_run['category'], caching=True)
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
            for test_run in b_run.get_tests(test_search=benchmark['test'],
                                                  workload_search=benchmark['workload']):
                # Times agreement within a test
                if (len(rc) > 0 and len(rc[0]) != len(test_run.raw)) or type(test_run.raw) != list:
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
            raise ValueError('UUID ' + benchmark_run['uuid'] + ' has no tests that where not skipped')

    # Creates one hot vector for representation of OSP_version
    categorical_columns['osp_version'] = tf.SparseTensor(indices=[[i, 0] for i in range(len(categorical_columns['osp_version']))],
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
       all_test_columns.append(tf.contrib.layers.real_valued_column(ALL_TEST_COLUMNS, dtype=tf.float32))

   osp_version = tf.contrib.layers.sparse_column_with_keys(column_name="osp_version",
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

# Finds a specified action trains itself on all data for that action in Elastic
def tf_train_action(conn, action, uuids):
   NUMERICAL_FEATURES = ["run",
   "concurrency",
   "raw",
   "nodes",
   "undercloud_cores",
   "undercloud_mem",
   "compute_cores",
   "compute_mem",
   "controller_cores",
   "controller_mem"]

   PREDICTON_FEATURE = "average_raw"

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
       if n > 1000:
           break
       print("Building data for " + uuid + " " + str(n) + " samples so far")
       test_runs = browbeat_run(conn, uuid, caching=False).get_tests(test_search=action)
       for test_run in test_runs:
           if not is_power_of_two(len(test_run.raw)) or type(test_run.raw) is not list:
               continue
           n = n + 1
           data['run'].append(test_run.run)
           data['raw'].append(scale_values(test_run.raw, 256))
           prediction_column.append(numpy.mean(test_run.raw))
           data['concurrency'].append(test_run.concurrency)
           data['nodes'].append(test_run.nodes)
           data['os_name'].append(test_run.os_name)
           data['osp_version'].append(test_run.version)

           data['undercloud_cores'].append(test_run.undercloud['cores'])
           data['undercloud_mem'].append(test_run.undercloud['mem'])
           data['undercloud_make'].append(test_run.undercloud['machine_make'])
           data['undercloud_processor_type'].append(test_run.undercloud['processor_type'])

           data['compute_cores'].append(test_run.compute['cores'])
           data['compute_mem'].append(test_run.compute['mem'])
           data['compute_make'].append(test_run.compute['machine_make'])
           data['compute_processor_type'].append(test_run.compute['processor_type'])

           data['controller_cores'].append(test_run.controller['cores'])
           data['controller_mem'].append(test_run.controller['mem'])
           data['controller_make'].append(test_run.controller['machine_make'])
           data['controller_processor_type'].append(test_run.controller['processor_type'])

   for column in NUMERICAL_FEATURES:
       data[column] = tf.constant(data[column])

   for column in CATEGORICAL_FEATURES:
       data[column] = tf.SparseTensor(indices=[[i, 0] for i in range(len(data[column]))],
                    values=data[column],
                    dense_shape=[len(data[column]), 1])

   prediction_column = tf.constant(prediction_column)

   return data, prediction_column


# The goal is to predict the average time taken for an action given hardware
def perf_predict(config, es_backend, action):
   NUMERICAL_FEATURES = ["run",
   "concurrency",
   "raw",
   "nodes",
   "undercloud_cores",
   "undercloud_mem",
   "compute_cores",
   "compute_mem",
   "controller_cores",
   "controller_mem"]

   PREDICTON_FEATURE = "average_raw"

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
       numerical_columns.append(tf.contrib.layers.real_valued_column(column, dtype=tf.float32))

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

   wide_columns=[]
   deep_columns=[]
   deep_columns.extend(categorical_columns)
   deep_columns.extend(numerical_columns)
   wide_columns.extend(numerical_columns)

   all_action_uuids = es_backend.get_uuids_by_action(action)
   train_set, validate_set = split_data(all_action_uuids)

   partial_train = functools.partial(tf_train_action, es_backend, action, train_set)

   est = tf.contrib.learn.LinearRegressor(feature_columns=deep_columns)
   logging.getLogger().setLevel(logging.INFO)
   #hooks = [ProfilerHook(save_steps=10, output_dir="profiling")]
   est.fit(input_fn=partial_train, steps=100000, monitors=None)
   partial_eval = functools.partial(tf_train_action, es_backend, action, validate_set)
   results = est.evaluate(input_fn=partial_eval, steps=1)
   print(results)
