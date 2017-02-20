from datetime import datetime
from elasticsearch import Elasticsearch
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
            sniff_on_start=False,
            sniff_on_connection_fail=True,
            sniffer_timeout=60)

    # Returns a list of training vectors
    def get_training_vectors(self, config):
      training_data = config['training-sets']
      for tset in training_data:
        print("Grabbing UUID " + tset['uuid'])
        raw_data = self._grab_uuids(tset['uuid'])
        tset['data'] = self._vectorize(raw_data, config)

    # Returns a list of validation vectors
    def get_validation_vectors(self, config):
      validation_data = config['validation-sets']
      for vset in validation_data:
        print("Grabbing UUID " + vset['uuid'])
        raw_data = self._grab_uuids(vset['uuid'])
        vset['data'] = self._vectorize(raw_data, config)

    # Searches and grabs the raw source data for a Browbeat UUID
    def _grab_uuids(self, uuid):
        results = self.es.search(body={"query": {"match": {'browbeat_uuid': uuid}}})['hits']['hits']
        if results == []:
            print(uuid + " Has no results!")
            exit(1)

        return results


    def _vectorize(self, data, config):
        vector = []

        # Filter indexes out of all UUID hits using lambda functions
        all_rally_tests = list(filter(lambda test: 'rally' in test['_index'], data))
        all_shaker_tests = list(filter(lambda test: 'shaker' in test['_index'], data))
        all_perfkit_tests = list(filter(lambda test: 'perfkit' in test['_index'], data))
        all_yoda_tests = list(filter(lambda test: 'yoda' in test['_index'], data))

        rally_tests = {}
        for test in config['rally_tests']:
            rally_tests[test] = list(filter(lambda x: x['_source']['scenario'] == test, all_rally_tests))

        shaker_tests = {}
        for test in config['shaker_tests']:
            shaker_tests[test] = list(filter(lambda x: x['_source']['browbeat_scenario'] == test, all_shaker_tests))

        perfkit_tests = {}
        for test in config['perfkit_tests']:
            perfkit_tests[test] = list(filter(lambda x: x['_source']['browbeat_scenario']['name'] == test, all_perfkit_tests))

        yoda_tests = {}
        for test in config['yoda_tests']:
            yoda_tests[test] = list(filter(lambda x: x['_source']['scenario'] == test, all_yoda_tests))

        for test in rally_tests:
            try:
                print list(map(lambda a, b: a['_source']['raw'] + b['_source']['raw'], rally_tests[test]))
            except:
                print "only one hit!"
