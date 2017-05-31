from browbeat_run import browbeat_run
import numpy


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
    return("Std_dev: " + std_dev + " Avg: " + avg + " Med: " + median)


# Used for an easy way to look at run data
def print_run_details(config, es_backend, uuid):
    brun = browbeat_run(es_backend, uuid, caching=True)
    output_string = ""
    osp_version = ""
    padding = longest_test_name(config)
    for test_type in config['tests']:
        test_name = test_type['test']
        data = []
        for test_run in brun.get_tests(test_search=test_name):
            if 'pipeline' in test_run.dlrn_hash or \
               'trunk' in test_run.dlrn_hash:
                return False
            data.extend(test_run.raw)
            osp_version = test_run.version
        output_string += test_name.ljust(padding) + \
            " " + data_summary(data) + "\n"
    header = ("Browbeat UUID: " + uuid + " OSP_version: " + osp_version + "\n")
    header += ("".ljust(80, "-")) + "\n"
    output_string = header + output_string
    return output_string
