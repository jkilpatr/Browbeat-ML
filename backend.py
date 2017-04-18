from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import json
import tensorflow as tf
import numpy

# Grabs data out of ElasticSearch, prepares for usage

class Backend(object):

    def __init__(self, config):
        self.es = Elasticsearch([
            {'host': config["elastic-host"],
             'port': config["elastic-port"]}],
            send_get_body_as='POST',
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60)


    # Utility function, prints a list of UUIDS meeting a serious of requirements
    #  otherwise it's hard to gather a list of training vectors to investigate
    #  Takes forever to run and requires an absurd amount of ram, use with caution
    def get_uuids_by_cloud(self, config):
      uuids = []
      for cloud_name in config['clouds']:
        print(cloud_name)
        results = helpers.scan(self.es, {"query": {"match": {'cloud_name': cloud_name}}}, size=100,request_timeout=1000)
        for result in results:
          uuid = result['_source']['browbeat_uuid']
          if uuid not in uuids:
            uuids.append(uuid)

      for uuid in uuids:
        print(uuid)

    # Returns a list of training vectors
    def get_training_sets(self, config):
      training_data = config['training-sets']
      for tset in training_data:
        print("Grabbing UUID " + tset['uuid'])
        raw_data = self._grab_uuid(tset['uuid'])
        tset['data'] = self._vectorize(raw_data, config, tset['uuid'])

    # Returns a list of validation vectors
    def get_validation_sets(self, config):
      validation_data = config['validation-sets']
      for vset in validation_data:
        print("Grabbing UUID " + vset['uuid'])
        raw_data = self._grab_uuid(vset['uuid'])
        vset['data'] = self._vectorize(raw_data, config, vset['uuid'])

    # Searches and grabs the raw source data for a Browbeat UUID
    def _grab_uuid(self, uuid):
        results = helpers.scan(self.es, {"query": {"match": {'browbeat_uuid': uuid}}}, size=100,request_timeout=1000)

        if results == []:
            print(uuid + " Has no results!")
            exit(1)

        return results

    def check_test_name(elastic_data, test):
        if 'scenario' in elastic_data['_source'] and elastic_data['_source']['scenario'] == test:
           return True
        elif 'scenario' in elastic_data['_source'] \
              and 'name' in elastic_data['_source']['browbeat_scenario'] \
              and elastic_data['_source']['browbeat_scenario']['name'] == test:
           return True
        elif 'scenario' in elastic_data['_source'] and elastic_data['_source']['browbeat_scenario'] == test:
           return True
        else:
           return False

    def filter_errors(test_result, uuid):
        if 'raw' in test_result['_source'] and len(run['_source']['raw'] > 0):
           return True
        else:
           print("UUID " + uuid + " has errors! Remove it")
           exit(1)

    # Takes a set of tests parses out their tests and produces a set of training vectors for each test
    def _vectorize(self, data, config, uuid):
        vectors = {}
        for test in tests:
           vectors[test] = list(itertools.chain(
                                map(lambda raw_data: raw_data['_source']['raw'],
                                filter(lambda test_result: filter_errors(test_result, uuid),
                                filter(lambda workload_result: check_test_name(workload_result, test['test']),
                                filter(lambda index_result: test['workload'] in index_result['_index'], data)))))

