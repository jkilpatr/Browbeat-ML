from browbeat_test import browbeat_test


class browbeat_run(object):

    # Takes a uuid and a raw set of elastic data to populate the object
    # in this case raw_elastic is just a dump from elastic for the uuid
    # disable caching when you need to use less ram at the cost of thrasing
    # the elastic DB more
    def __init__(self,
                 elastic_connection,
                 uuid,
                 caching=True,
                 pass_fail=None,
                 timeseries=False):
        self._caching = caching
        self._elastic_connection = elastic_connection.grab_uuid(uuid)
        if self._caching:
            self._tests = None
        self.uuid = uuid
        self.num_errors = 0
        # If timeseries metadata is enabled we will go and grab all of it.
        if timeseries:
            self._init_timeseries()

    def _init_timeseries(self):
        # this timestamp should never be smaller than any time in
        # the next few thousand years
        start = 2000000000
        end = 0
        for test in self.get_tests():
            start = min(start, test._metrics_start)
            end = max(end, test._metrics_end)
            url = test._graphite_url
        self._metrics_root = test._metrics_root
        self._graphite_start = start
        self._graphite_end = end
        self._graphite_url = url

    def get_graphite_details(self):
        graphite_support_data = [self._graphite_url, self._graphite_start,
                                 self._graphite_end, self._metrics_root]
        return graphite_support_data

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
        # return False
        raise ValueError('Failed to find index!')

    def _validate_result(self, index_result, test, uuid):
        if 'result' not in index_result['_type']:
            self.num_errors += 1
            # print("UUID " + uuid + " has errors! In test " + test)
            return False
        else:
            return True

    def get_tests(self, workload_search=None,
                  test_search=None,
                  concurrency_search=None,
                  times_search=None,
                  scenario_search=None):
        if self._caching:
            if self._tests is None:
                self._tests = list(self._get_tests())
            return self._get_tests_list(workload_search=workload_search,
                                        test_search=test_search,
                                        concurrency_search=concurrency_search,
                                        times_search=times_search,
                                        scenario_search=scenario_search)
        else:
            return self._get_tests(workload_search=workload_search,
                                   test_search=test_search,
                                   concurrency_search=concurrency_search,
                                   times_search=times_search,
                                   scenario_search=scenario_search)

    def _get_tests(self, workload_search=None,
                   test_search=None,
                   concurrency_search=None,
                   times_search=None,
                   scenario_search=None):
        for index_result in self._elastic_connection:
            try:
            # if self._map_index_to_workload(index_result['_index']) != False:  # noqa
                workload = self._map_index_to_workload(index_result['_index'])
            except ValueError:
                continue
            if workload_search is not None and workload not in workload_search:
                # print(workload_search + " not in " + workload)
                continue

            try:
                test = self._map_scenario_to_test(index_result['_source'])
            except ValueError:
                # print("Found scenarios that could not be mapped!")
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
                                     caching=self._caching)
            except ValueError:
                print("ValueError in test processing " +
                      str(test) + " For UUID: " + self.uuid)
                continue
            except KeyError:
                print("KeyError in test processing " +
                      str(test) + " For UUID: " + self.uuid)
                continue

            if scenario_search is not None \
               and scenario_search not in test.scenario_name:
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
                        times_search=None,
                        scenario_search=None):
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
            if scenario_search is not None \
               and scenario_search not in test.scenario_name:
                continue

            ret.append(test)
        return ret

    def get_num_errors(self):
        return self.num_errors
