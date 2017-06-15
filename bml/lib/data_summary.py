from lib.browbeat_run import browbeat_run
import numpy
import sqlite3
import cPickle
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.svm import NuSVC
from sklearn.tree import DecisionTreeClassifier

osp_version_dic={"10-director":1,"10-tripleo":2,"11-director":3,"11-tripleo":4,"12-director":5,"master-tripleo":6,"9-director":7,"9-tripleo":8}
test_name_dic={"authenticate.keystone":1,
"glance.create_image":2,
"glance.delete_image":3,
"keystone_v2.create_tenant":4,
"neutron.add_interface_router":5,
"BrowbeatPlugin.create_network_nova_boot.neutron.create_network":61,
"NeutronNetworks.create_and_list_routers.neutron.create_network":62,
"NeutronNetworks.create_and_list_subnets.neutron.create_network":63,
"NeutronNetworks.create_and_list_ports.neutron.create_network":64,
"NeutronNetworks.create_and_list_networks.neutron.create_network":65,
"neutron.create_port":7,
"neutron.create_router":8,
"neutron.create_security_group":9,
"NeutronNetworks.create_and_list_subnets.neutron.create_subnet":101,
"NeutronNetworks.create_and_list_routers.neutron.create_subnet":102,
"BrowbeatPlugin.create_network_nova_boot.neutron.create_subnet":103,
"neutron.list_networks":11,
"neutron.list_ports":12,
"neutron.list_routers":13,
"neutron.list_security_groups":14,
"neutron.list_subnets":15,
"nova.boot_server":16,
"nova.create_image":17,
"nova.delete_image":18,
"nova.delete_server":19,
"nova.list_servers":20}

test_with_scenario_list=["neutron.create_network","neutron.create_subnet"]


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

        average_runtime=data_summary(data)[0]
        output_string += test_name.ljust(padding) + \
            " " + str(average_runtime)  #typecasting data_summary(data) to string because if it returns false it's going to throw an error
        if float(average_runtime)>0.0 and test_run.errortype=="result" and test_name!="nova.boot_server":
            if str(test_name) in test_with_scenario_list:
                test_name=str(test_run.scenario_name)+"."+str(test_name)
            predictors=numpy.array([0,1,2])
            predictors[0]=osp_version_dic[str(osp_version)]
            predictors[1]=test_name_dic[str(test_name)]
            predictors[2]=float(average_runtime)
            predictors.reshape(1, -1)
            with open('lib/classifier/dumped_dtree.pkl', 'rb') as fid:
                clf=cPickle.load(fid)
            output_prediction=clf.predict([predictors])
            if str(output_prediction[0])=="1":
                print("ALERT!!!!")
                print uuid,test_name,predictors[2]
                exit(1)

            #print("EEEEEEEEEEENNNNNNNNNNDDDDDD")
            output_string=output_string+ str(output_prediction) + "\n"
            #c.execute('INSERT INTO scenario_test VALUES (?,?,?,?,?)',(str(uuid),str(osp_version),str(test_run.scenario_name),str(test_name),average_runtime))
            '''
            if test_run.cloud_name in config['clouds']:
                c.execute('INSERT INTO avg_values2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',\
                          (str(uuid),str(test_run.timestamp),str(osp_version),str(test_run.cloud_name),\
                           str(test_run.os_name),str(test_run.kernel),test_run.no_computes,\
                           test_run.no_controller,test_run.controller['cores'],test_run.controller['mem'],\
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
