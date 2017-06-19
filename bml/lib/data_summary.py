from browbeat_run import browbeat_run
from dtree_classifier import classify_value
import numpy
import sqlite3
import cPickle
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.svm import NuSVC
from sklearn.tree import DecisionTreeClassifier
import json



def longest_test_name(config):
    val = 0
    for test in config['tests']:
        if len(test['test']) > val:
            val = len(test['test'])
    return val


def time_summary(config, es_backend, time_period, osp_version):
    if osp_version is not None:
        uuids = es_backend.grab_uuids_by_date(osp_version, time_period)
    else:
        uuids = []
        for version in config['watched_versions']:
            uuids.extend(es_backend.grab_uuids_by_date(version, time_period))
    for uuid in uuids:
        val = print_run_details(config, es_backend, uuid)
        if val is not False:
            print(val)


def summary_uuid(es_backend, config, uuid):
    val = print_run_details(config, es_backend, uuid)
    if val is not False:
        print(val)


def data_summary(data):
    std_dev = "{:.4f}".format(numpy.std(data)).ljust(10)
    avg = "{:.4f}".format(numpy.mean(data)).ljust(10)
    median = "{:.4f}".format(numpy.median(data)).ljust(10)
    summary=[avg,std_dev,median]
    return(summary)


# Used for an easy way to look at run data
def print_run_details(config, es_backend, uuid):
    brun = browbeat_run(es_backend, uuid, caching=True)
    output_string = ""
    osp_version = ""
    padding = longest_test_name(config) #gets the test with highest run time
    '''
    conn=sqlite3.connect('database.sqlite')
    c=conn.cursor()
    '''
    for test_type in config['tests']:
        test_name = test_type['test']
        data = []
        for test_run in brun.get_tests(test_search=test_name):
            if 'pipeline' in test_run.dlrn_hash or \
               'trunk' in test_run.dlrn_hash:
                return False
            if len(str(test_run.dlrn_hash))<=45:
                return False
            data.extend(test_run.raw)
            osp_version = test_run.version
        statistics_uuid=data_summary(data)
        average_runtime=statistics_uuid[0]
        output_string += test_name.ljust(padding) + \
            " " + str(average_runtime) +" "+ str(statistics_uuid[1])  #typecasting data_summary(data) to string because if it returns false it's going to throw an error
        if float(average_runtime)>0.0 and test_run.errortype=="result" and test_name!="nova.boot_server":
            if str(test_name) in config['test_with_scenario_list']:
                test_name=str(test_run.scenario_name)+"."+str(test_name)
            output_prediction=classify_value(config,average_runtime,test_name,osp_version)
            if str(output_prediction[0])=="1":
                print("ALERT!!!!")
                print (uuid,test_name,osp_version)
                exit(1)

            #print("EEEEEEEEEEENNNNNNNNNNDDDDDD")
            output_string=output_string+ str(output_prediction) + "\n"
            #c.execute('INSERT INTO scenario_test VALUES (?,?,?,?,?)',(str(uuid),str(osp_version),str(test_run.scenario_name),str(test_name),average_runtime))
            '''
            if test_run.cloud_name in config['clouds']:
                c.execute('INSERT INTO avg_values2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',\
                          (str(uuid),str(test_run.timestamp),str(osp_version),str(test_run.cloud_name),\
                           str(test_run.os_name),str(test_run.kernel),test_run.num_computes,\
                           test_run.num_controller,test_run.controller['cores'],test_run.controller['mem'],\
                           test_run.undercloud['cores'],test_run.undercloud['mem'],\
                           str(test_run.dlrn_hash),str(test_name),str(test_run.scenario_name),\
                           average_runtime))
        '''
        else:
            output_string+="\n"
    '''
    conn.commit()
    conn.close()
    '''


    header = ("Browbeat UUID: " + uuid + " OSP_version: " + osp_version + "\n")
    header += ("".ljust(80, "-")) + "\n"
    output_string = header + output_string
    return output_string
