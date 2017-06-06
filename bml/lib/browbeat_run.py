from lib.browbeat_test import browbeat_test


class browbeat_run(object):

    # Takes a uuid and a raw set of elastic data to populate the object
    # in this case raw_elastic is just a dump from elastic for the uuid
    # disable caching when you need to use less ram at the cost of thrasing
    # the elastic DB more
    def __init__(self, elastic_connection, uuid, caching=True, pass_fail=None):
        self._caching = caching
        self._elastic_connection = elastic_connection.grab_uuid(uuid)
        if self._caching:
            self._tests = None
        self.uuid = uuid
        # Used for training, pass_fail at the run level right now, should be
        # brought down to the test level later.
        self._pass_fail = pass_fail

    def _map_scenario_to_test(self, source):
        if 'action' in source:
            return source['action']
        else:
            raise ValueError("Failed to find test name!")

    def _map_index_to_workload(self, index):
        workloads = ['rally', 'shaker', 'perfkit', 'yoda']
        for workload in workloads:
            if workload in index:
                return workload
        raise ValueError('Failed to find index!')

    def _validate_result(self, index_result, test, uuid):
        if 'result' not in index_result['_type']:
            # print("UUID " + uuid + " has errors! In test " + test)
            return False
        else:
            return True

    def get_tests(self, workload_search=None,
                  test_search=None,
                  concurrency_search=None,
                  times_search=None):
        if self._caching:
            if self._tests is None:
                self._tests = list(self._get_tests())
            return self._get_tests_list(workload_search=workload_search,
                                        test_search=test_search,
                                        concurrency_search=concurrency_search,
                                        times_search=times_search)
        else:
            return self._get_tests(workload_search=workload_search,
                                   test_search=test_search,
                                   concurrency_search=concurrency_search,
                                   times_search=times_search)

    def _get_tests(self, workload_search=None,
                   test_search=None,
                   concurrency_search=None,
                   times_search=None):
        for index_result in self._elastic_connection:
            workload = self._map_index_to_workload(index_result['_index'])
            if workload_search is not None and workload not in workload_search:
                # print(workload_search + " not in " + workload)
                continue

            try:
                test = self._map_scenario_to_test(index_result['_source'])
            except ValueError:
                print("Found scenarios that could not be mapped!")
                continue
            if not self._validate_result(index_result, test, self.uuid):
                continue
            if test_search is not None and test not in test_search:
                # print(test_search + " not in " + test)
                continue

            try:
                test = browbeat_test(index_result,
                                     self.uuid,
                                     test,
                                     workload,
                                     training_output=self._pass_fail)
            except ValueError:
                print("ValueError in test processing " +
                      str(test) + " For UUID: " + self.uuid)
                continue
            except KeyError:
                print("KeyError in test processing " +
                      str(test) + " For UUID: " + self.uuid)
                continue

            if concurrency_search is not None \
               and test.concurrency != concurrency_search:
                continue
            if times_search is not None and test.times != times_search:
                continue

            yield test

    def _get_tests_list(self, workload_search=None,
                        test_search=None,
                        concurrency_search=None,
                        times_search=None):
        ret = []
        for test in self._tests:
            if workload_search is not None and \
               test.workload not in workload_search:
                # print(workload_search + " not in " + workload)
                continue
            if test_search is not None and test.name not in test_search:
                # print(test_search + " not in " + test)
                continue
            if concurrency_search is not None and \
               test.concurrency != concurrency_search:
                continue
            if times_search is not None and test.times != times_search:
                continue

            ret.append(test)
        return ret
