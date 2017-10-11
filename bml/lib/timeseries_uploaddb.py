import numpy
import requests
from bml.lib.elastic_backend import Backend
from bml.lib.browbeat_run import browbeat_run
from bml.lib.util import connect_crdb

metrics_list = ["overcloud-controller-0.cpu-*.cpu-system",
                "overcloud-controller-0.cpu-*.cpu-user",
                "overcloud-controller-0.cpu-*.cpu-softirq",
                "overcloud-controller-0.cpu-*.cpu-wait",
                "overcloud-controller-0.memory.memory-slab_unrecl",
                "overcloud-controller-0.memory.memory-used"]

def get_features(gdata,pos):
    values = []
    for entry in gdata:
        if type(entry[pos]) is not list and entry[pos] is not None:
            values.append(entry[pos])
    values = numpy.array(values)
    return [numpy.mean(values),numpy.percentile(values,95)]

#'''
def insert_timeseriessummaries_db(config,uuid):
    elastic = Backend("elk.browbeatproject.org", "9200")
    brun = browbeat_run(elastic, uuid, timeseries=True)
    graphite_details = brun.get_graphite_details()
    graphite_url = graphite_details[0]
    start = graphite_details[1]
    end = graphite_details[2]
    metric_base = str(graphite_details[3]) + "."
    base_url = "{}/render?target={}"
    time_url = "&format=json&from={}&until={}"
    metric = metric_base
    base_url = base_url.format(graphite_url,
                               metric_base)
    time_url = time_url.format(start,
                               end)
    final_url = base_url + "{}" + time_url
    conn = connect_crdb(config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    cpu_system = summarize_metric(final_url,metrics_list[0])
    cpu_user = summarize_metric(final_url,metrics_list[1])
    cpu_softirq = summarize_metric(final_url,metrics_list[2])
    cpu_wait = summarize_metric(final_url,metrics_list[3])
    mem_slabunrecl = summarize_metric(final_url,metrics_list[4])
    mem_used = summarize_metric(final_url,metrics_list[5])
    cur.execute("INSERT INTO {} VALUES ('{}', {}, {}, {}, {}, {}, {},\
                {}, {}, {}, {}, {}, {});" .format(config['table_timeseries'][0],
                                                      str(uuid),
                                                      float(cpu_system[0]),
                                                      float(cpu_system[1]),
                                                      float(cpu_user[0]),
                                                      float(cpu_user[1]),
                                                      float(cpu_softirq[0]),
                                                      float(cpu_softirq[1]),
                                                      float(cpu_wait[0]),
                                                      float(cpu_wait[1]),
                                                      float(mem_used[0]),
                                                      float(mem_used[1]),
                                                      float(mem_slabunrecl[0]),
                                                      float(mem_slabunrecl[1])))

def summarize_metric(final_url,metric_id):
    data_url = final_url.format(metric_id)
    response = requests.get(data_url).json()
    if "cpu" in metric_id:
        cpu_val_list = []
        for data_item in response:
            if data_item['datapoints'][0] is not None and \
                data_item['datapoints'][1] is not None:
                cpu_val_list += data_item['datapoints']
        l = cpu_val_list
        dict_vals = {}
        # This is not the optimal way using this for now,
        # as can't figure out lambda function
        # to get the task done
        for v,k in cpu_val_list:
            if k in dict_vals:
                dict_vals[k].append(v)
                if len(dict_vals[k])==4:
                    if all(vals is not None for vals in dict_vals[k]):
                        dict_vals[k]=sum(dict_vals[k])/len(dict_vals[k])
            else:
                dict_vals[k]=[v]
        #print dict_vals
        list_vals = map(list, dict_vals.items())
        return get_features(list_vals,1)
    else:
        return get_features(response[0]['datapoints'],0)
