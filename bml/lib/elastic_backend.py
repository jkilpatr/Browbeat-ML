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
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniff_timeout=10,
            sniffer_timeout=120,
            timeout=120)

    def grab_uuids_by_date(self, version, time_period):
        query = {
            "query": {
                "filtered": {
                    "query": {"match": {'version.osp_version': version}},
                    "filter": {
                        "range": {"timestamp": {"gt": "now-" + time_period}}
                        }
                    }
                },
            "size": 0,
            "aggs": {
                "langs": {
                    "terms": {"field": "browbeat_uuid", "size": 15000}
                    # size is max number of unique uuids that can be expected.
                    }
                }
            }
        res = self.es.search(index="browbeat-rally-*", body=query)
        if res == []:
            raise ValueError("No results!")
        number_uuid = len(res['aggregations']['langs']['buckets'])
        uuid_list = []
        for x in range(number_uuid):
            uuid = res['aggregations']['langs']['buckets'][x]['key']
            uuid_list.append(uuid)
        return uuid_list

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

    def compute_start_end(self, uuid):
        query_input = {
            "query": {
                "match": {
                    'browbeat_uuid': uuid
                    }
                },
            "size": 1,
            "aggs": {
                "max_time": {
                    "max": {
                        "field": "timestamp"
                        }
                    },
                "min_time": {
                    "min": {
                        "field": "timestamp"
                        }}}}
        res = self.es.search(index="browbeat-rally-*", body=query_input)
        start = int(res['aggregations']['min_time']['value'])
        end = int(res['aggregations']['max_time']['value'])
        cloud_name = res['hits']['hits'][0]['_source']['cloud_name']
        grafana_url = \
            res['hits']['hits'][0]['_source']['grafana_url'][0]
        for dashboard in grafana_url:
            graphite_url = grafana_url[dashboard].split(":")[1].strip("/")
            graphite_port = "80"
            graphite_url = "http://{}:{}".format(graphite_url, graphite_port)
        return [start, end, cloud_name, graphite_url]
