from elasticsearch import Elasticsearch
from elasticsearch import helpers

# Grabs data out of ElasticSearch, prepares for usage
# If you want to use data out of multiple ES's
# just create multiple backend objects


class Backend(object):

    def __init__(self, host, port):
        self.es = Elasticsearch([
            {'host': host,
             'port': port}],
            send_get_body_as='POST',
            retries=True,
            sniff_on_start=False,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
            timeout=60)

    def get_uuids_by_action(self, action):
        query = {"query": {"match": {'action': action}}}
        results = helpers.scan(self.es,
                               query,
                               size=100,
                               request_timeout=1000)

        if results == []:
            raise ValueError("No results!")

        # Use a set for O(1) membership tests
        uuid_list = set()
        print("Grabbing list of uuid's matching action " + action)
        for entry in results:
            if 'browbeat_uuid' in entry['_source']:
                uuid = entry['_source']['browbeat_uuid']
                if uuid not in uuid_list:
                    uuid_list.add(uuid)
        return list(uuid_list)

    def grab_uuids_by_date(self, version, time_period):
        query = {
                  "query": {
                    "filtered": {
                      "query": {"match": {'version.osp_version': version}},
                      "filter": {
                        "range": {"timestamp": {"gt": "now-" + time_period}}
                      }
                    }
                  }
                }
        results = helpers.scan(self.es, query, size=100, request_timeout=1000)

        if results == []:
            raise ValueError("No results!")

        # Use a set for O(1) membership tests
        uuid_list = set()
        for entry in results:
            if 'browbeat_uuid' in entry['_source']:
                uuid = entry['_source']['browbeat_uuid']
                if uuid not in uuid_list:
                    uuid_list.add(uuid)
        return list(uuid_list)

    # Searches and grabs the raw source data for a Browbeat UUID
    def grab_uuid(self, uuid):
        query = {"query": {"match": {'browbeat_uuid': uuid}}}
        results = helpers.scan(self.es,
                               query,
                               size=100,
                               request_timeout=1000)

        if results == []:
            raise ValueError(uuid + " Has no results!")

        return results
