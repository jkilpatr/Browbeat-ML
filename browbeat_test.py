# Test class, the goal of this class is to encapsulate a single run of a test for a browbeat
# run with a browbeat workload, as well as easy run, raw data mapped by concurrency values and
# metadata

import backend
import browbeat_test
import numpy

class browbeat_test(object):

    # Takes a uuid and a raw set of elastic data to populate the object
    # in this case raw_elastic is going to be a test of test indexes
    def __init__(self, raw_elastic, uuid, test_name, workload, training_output=None):
        self.uuid = uuid
        self.name = test_name
        self.workload = workload
        self._set_metadata(raw_elastic)
        self.raw = self._get_raw_data(raw_elastic)
        # Using during model training, true false for now, to be expanded
        self._training_output=training_output


    def _get_raw_data(self, raw_elastic):
        if 'raw' in raw_elastic['_source']:
            return raw_elastic['_source']['raw']
        else:
            raise ValueError('Invalid test data!')

    # Extracts details of the really run
    def _set_metadata(self, raw_elastic):
        if 'rally' in self.workload:
            self.concurrency = raw_elastic['_source']['rally_setup']['kw']['runner']['concurrency']
            self.times = raw_elastic['_source']['rally_setup']['kw']['runner']['times']
            self.version = raw_elastic['_source']['version']['osp_version']
            self.cloud_name = raw_elastic['_source']['cloud_name']
            self.run = raw_elastic['_source']['iteration']
