import tensorflow as tf
import numpy
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run

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

def tf_svm_train(conn, tset):
    feature_columns = {}
    label = []
    data = {'raw': [], 'concurrency': [], 'runs': [], 'osp_version': []}
    for test in tset:
        test_run = browbeat_run(conn, test['uuid'], pass_fail=test['category'], caching=False)
        for run in test_run.get_tests(test_search="authenticate.keystone"):
            if len(run.raw) != 2500:
                continue
            data['raw'].append(run.raw)
            data['concurrency'].append(run.concurrency)
            data['runs'].append(run.run)
            # This might be useless  ^
            data['osp_version'].append(run.version)
            if test['category']:
                label.append(True)
            else:
                label.append(False)
    data['raw'] = numpy.array(data['raw'])
    for feature in data:
        data[feature] = tf.constant(data[feature])
    data['raw'] = tf.cast(data['raw'], tf.float16)
    label = tf.constant(label)
    return data, label


