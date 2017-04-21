import yaml
import sys
from backend import Backend
from browbeat_test import browbeat_test
from browbeat_run import browbeat_run
import tensorflow as tf
import numpy as np
from scipy import stats

def _load_config(path):
    try:
        stream = open(path, 'r')
    except IOError:
        self.logger.error("Configuration file {} passed is missing".format(path))
        exit(1)
    config = yaml.load(stream)
    stream.close()
    return config

# Dead simple test, tells you if two tests are significantly different
def pass_fail(conn, workload, test, uuid_A, uuid_B):
    A = browbeat_run(conn, uuid_A, caching=False)
    B = browbeat_run(conn, uuid_B, caching=False)
    A_tests = list(A.get_tests(workload_search=workload, test_search=test))
    B_tests = list(B.get_tests(workload_search=workload, test_search=test))
    A_tests.sort(key=lambda x: x.concurrency)
    B_tests.sort(key=lambda x: x.concurrency)
    for A_test, B_test in zip(A_tests,
                              B_tests):
        if A_test.concurrency != B_test.concurrency:
            print("Tests not comparable!")
            continue
        t, p = stats.ttest_ind(A_test.raw, B_test.raw, equal_var=False)
        print(str(t) + " " + str(p))


def main():
   config = "config.yml"
   config = _load_config(config)
   es_backend = Backend(config['elastic-host'],config['elastic-port'])
   uuid_A = "acde6660-bbe6-4b4c-a8d8-327543130073"
   uuid_B = "35c5766e-ecf7-4778-a773-b5895c0695a0"
   for test in config['tests']:
       pass_fail(es_backend, test['workload'], test['test'], uuid_A, uuid_B)

if __name__ == '__main__':
    sys.exit(main())







