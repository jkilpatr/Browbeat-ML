import tensorflow as tf
import numpy
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run
import functools

# This file is where test functions go


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

# tf.learn training function, used across multiple tests
#  This function is shamefully messy because it has to deal with all sorts of
#  issues with the data itself as well as enforce a ton of assumptions
def tf_train(conn, tset, tests):
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
            rc = []
            cc = []
            ruc = []
            for test_run in b_run.get_tests(test_search=benchmark['test'],
                                                  workload_search=benchmark['workload']):
                # If it's not the first run, and the number of runs are different skip
                if (len(rc) > 0 and len(rc[0]) != len(test_run.raw)) or type(test_run.raw) != list:
                    continue
                rc.append(test_run.raw)
                cc.append(int(test_run.concurrency))

                # This is bad and elastic should feel bad
                if type(test_run.run) is list:
                    test_run.run = test_run.run[0]
                ruc.append(int(test_run.run))
                if osp_version is None:
                    osp_version = test_run.version
                    categorical_columns['osp_version'].append(osp_version)
            # length limiter used to take only the first times we encounter
            ll = len(all_test_columns[benchmark['test'] + '_raw'])
            if len(rc) > 0 and ll > 0 and ll == len(rc):
                all_test_columns[benchmark['test'] + '_concurrency'].append(cc)
                all_test_columns[benchmark['test'] + '_raw'].append(rc)
                all_test_columns[benchmark['test'] + '_runs'].append(ruc)
        if osp_version is None:
            raise ValueError('UUID ' + benchmark_run['uuid'] + ' has no tests that where not skipped')

    categorical_columns['osp_version'] = tf.SparseTensor(indices=[[i, 0] for i in range(len(categorical_columns['osp_version']))],
                    values=categorical_columns['osp_version'],
                    dense_shape=[len(categorical_columns['osp_version']), 1])

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

   partial_train = functools.partial(tf_train, es_backend, config['training-sets'], config['tests'])
   est = tf.contrib.learn.DNNLinearCombinedClassifier(linear_feature_columns=wide_columns,
                                                      dnn_feature_columns=deep_columns,
                                                      dnn_hidden_units=[1024,512,256,128,64,32,16,8,4,2],
                                                      fix_global_step_increment_bug=True)
   partial_eval = functools.partial(tf_train, es_backend, config['validation-sets'], config['tests'])
   est.fit(input_fn=partial_train, steps=10000)
   results = est.evaluate(input_fn=partial_eval, steps=1)
   print(results)

