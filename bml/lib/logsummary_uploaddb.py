from elasticsearch import Elasticsearch
from bml.lib.elastic_backend import Backend
from bml.lib.browbeat_run import browbeat_run
from bml.lib.util import connect_crdb


def compute_hits(start,end,cloud_name,level_type):
    es = Elasticsearch([{'host': 'elk.browbeatproject.org', 'port': 9200}])
    bool_true = "true"
    time_dict = {
      "format": "epoch_millis"
    }
    time_dict["gte"] = start
    time_dict["lte"] = end
    query_input = {
    "query": {
    "filtered": {
      "query": {
        "query_string": {
          "query": "browbeat.cloud_name: " + cloud_name +" AND level: "+ level_type
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "range": {
                "@timestamp": time_dict
              }
            }
          ],
          "must_not": []
        }}}}}
    res = es.search(index="logstash-*", body=query_input)
    return res['hits']['total']


def insert_logsummary_db(config,uuid):
    es = Elasticsearch([{'host': 'elk.browbeatproject.org', 'port': 9200}])
    res = es.search(index="browbeat-rally-*", body= {"query": {"match": {'browbeat_uuid': uuid}},"aggs": {"max_time": {"max": {"field": "timestamp"}},"min_time":{"min": {"field": "timestamp"}}}})
    start=int(res['aggregations']['min_time']['value'])
    end=int(res['aggregations']['max_time']['value'])
    cloud_name=res['hits']['hits'][0]['_source']['cloud_name']
    num_errors = compute_hits(start,end,cloud_name,'error')
    num_warn = compute_hits(start,end,cloud_name,'warning')
    num_debug = compute_hits(start,end,cloud_name,'debug')
    num_notice = compute_hits(start,end,cloud_name,'notice')
    num_info = compute_hits(start,end,cloud_name,'info')
    conn = connect_crdb(config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    cur.execute("INSERT INTO {} VALUES ('{}', \
                {}, {}, {}, {}, {});".format(config['table_logsummary'][0],
                                                 str(uuid),
                                                 int(num_errors),
                                                 int(num_warn),
                                                 int(num_debug),
                                                 int(num_notice),
                                                 int(num_info)))
