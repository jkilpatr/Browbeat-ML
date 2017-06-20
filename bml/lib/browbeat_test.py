import requests


class browbeat_test(object):

    # Takes a uuid and a raw set of elastic data to populate the object
    # in this case raw_elastic is going to be a test of test indexes
    def __init__(self,
                 raw_elastic,
                 uuid, test_name,
                 workload,
                 training_output=None,
                 caching=None):
        self.uuid = uuid
        self.name = test_name
        self.workload = workload
        self._set_metadata(raw_elastic)
        self.raw = self._get_raw_data(raw_elastic)
        # Using during model training, true false for now, to be expanded
        self._training_output = training_output
        self._caching = caching
        self._metrics_cache = None
        self._timeseries_metadata_present = False

    def _get_raw_data(self, raw_elastic):
        if 'raw' in raw_elastic['_source']:
            return raw_elastic['_source']['raw']
        else:
            raise ValueError('Invalid test data!')

    def _set_hardware_metadata(self, hardware_details):
        self.nodes = len(hardware_details)
        self.os_name = hardware_details[0]['os_name']
        self.os_name = self._typecheck_string(self.os_name)
        self.kernel = hardware_details[0]['kernel']
        self.kernel = self._typecheck_string(self.kernel)
        self.controller = {}
        self.compute = {}
        self.undercloud = {}
        for node in hardware_details:
            if 'undercloud' in node['label'] and not len(self.undercloud):
                self.undercloud['machine_make'] \
                    = self._typecheck_string(node['machine_make'])
                self.undercloud['processor_type'] \
                    = self._typecheck_string(node['processor_type'])
                self.undercloud['mem'] \
                    = self._typecheck_num(node['total_mem'])
                self.undercloud['cores'] \
                    = self._typecheck_num(node['total_logical_cores'])
            elif 'controller' in node['label'] and not len(self.controller):
                self.controller['machine_make'] \
                    = self._typecheck_string(node['machine_make'])
                self.controller['processor_type'] \
                    = self._typecheck_string(node['processor_type'])
                self.controller['mem'] \
                    = self._typecheck_num(node['total_mem'])
                self.controller['cores'] \
                    = self._typecheck_num(node['total_logical_cores'])
            elif 'compute' in node['label'] and not len(self.compute):
                self.compute['machine_make'] \
                    = self._typecheck_string(node['machine_make'])
                self.compute['processor_type'] \
                    = self._typecheck_string(node['processor_type'])
                self.compute['mem'] \
                    = self._typecheck_num(node['total_mem'])
                self.compute['cores'] \
                    = self._typecheck_num(node['total_logical_cores'])

    def _set_software_metadata(self, software_metadata):
        # Not sure what to do here yet, worker counts?
        return True

    # Some values out of elastic have been inserted wrong
    # this makes sure things we think are numbers are
    def _typecheck_num(self, val):
        if type(val) is list:
            return int(val[0])
        else:
            return int(val)

    def _typecheck_string(self, val):
        if type(val) is str:
            return val
        else:
            return str(val)

    # Extracts details of the really run
    def _set_metadata(self, raw_elastic):
        self._set_timeseries_metadata(raw_elastic)
        self._set_hardware_metadata(
            raw_elastic['_source']['hardware-metadata']['hardware_details'])
        self._set_software_metadata(
            raw_elastic['_source']['software-metadata'])
        if 'rally' in self.workload:
            self.concurrency = raw_elastic['_source']['rally_setup']['kw']['runner']['concurrency']  # noqa
            self.concurrency = self._typecheck_num(self.concurrency)
            self.times = raw_elastic['_source']['rally_setup']['kw']['runner']['times'] # noqa
            self.times = self._typecheck_num(self.times)
            self.version = raw_elastic['_source']['version']['osp_version']
            self.version = self._typecheck_string(self.version)
            self.cloud_name = raw_elastic['_source']['cloud_name']
            self.run = raw_elastic['_source']['iteration']
            self.run = self._typecheck_num(self.run)
            self.dlrn_hash = raw_elastic['_source']['version']['dlrn_hash']
            self.scenario_name = raw_elastic['_source']['rally_setup']['name']
            self.timestamp = raw_elastic['_source']['timestamp']
            self.num_computes = raw_elastic['_source']['environment-metadata']['environment_setup']['osp_computes_number']  # noqa
            self.num_controller = raw_elastic['_source']['environment-metadata']['environment_setup']['osp_controllers_number']  # noqa
            self.errortype = raw_elastic['_type']

    # Returns the name/data tuple of anything that maches a pattern
    # if caching is on in the browbeat_run object cache the results
    def get_timeseries_metadata(self, filterlist):
        if self._timeseries_metadata_present:
            if self._caching:
                return self._get_timeseries_metadata_list(filterlist)
            else:
                return self._get_timeseries_metadata_generator(filterlist)
        else:
            return []

    def _get_timeseries_metadata_list(self, filterlist):
        if self._metrics_cache is not None:
            return self._metrics_cache
        else:
            self._metrics_cache = []
            for entry in self._list_metrics_filtered(self._metrics_root,
                                                     filterlist):
                data = self._get_raw_metrics(entry)
                self._metrics_cache.append(data)
            return self._metrics_cache

    def _get_timeseries_metadata_generator(self, filterlist):
        for entry in self._list_metrics_filtered(self._metrics_root,
                                                 filterlist):
            yield self._get_raw_metrics(entry)

    def _is_filter_match(self, string, filterlist):
        for item in filterlist:
            if item in string:
                return True
        return False

    def _list_metrics_filtered(self, metric, filterlist):
        metrics_list = []
        for submetric in self._get_submetrics(metric):
            # cloud->machine->metric so we need to ignore the top two levels of
            # delimiters which happen to be .'s here
            if submetric['id'].count('.') >= 2 and \
               not self._is_filter_match(submetric['id'],
                                         filterlist):
                continue
            elif submetric['leaf'] is 0:
                children = self._list_metrics_filtered(submetric['id'],
                                                       filterlist)
                metrics_list.extend(children)
            else:
                return [submetric['id']]
        return metrics_list

    # Helper function for navigating metric trees, returns children or None
    def _get_submetrics(self, metric_id):
        metrics_url = "{}/metrics/find?query={}.*".format(self._graphite_url,
                                                          metric_id)
        response = requests.get(metrics_url).json()
        return response

    def _compress_timeseries(self, uncompressed):
        compressed = []
        for point in uncompressed:
            if point[0] is not None:
                compressed.append(point)
        return compressed

    def _get_raw_metrics(self, metric_id):
        base_url = "{}/render?target={}&format=json&from={}&to={}"
        data_url = base_url.format(self._graphite_url,
                                   metric_id,
                                   self._metrics_start,
                                   self._metrics_end)
        response = requests.get(data_url).json()[0]
        compressed = self._compress_timeseries(response['datapoints'])
        response['datapoints'] = compressed
        return response

    def _set_timeseries_metadata(self, raw_elastic):
        # This code maintains two assumptions
        # 1. the graphite and grafana machine is the same (mostly true)
        # 2. that graphite is on port 8008 this is a horrible assumption
        #    because it's usually not true. 80 is the default port.
        # These issues can be solved by adding a top level index item in
        # Browbeat's metadata to support this specific bml feature.
        grafana_url = raw_elastic['_source']['grafana_url'][0]
        cloud_name = raw_elastic['_source']['cloud_name']

        # There should really only be one daskboard in the list but if there is
        # more than one taking the last one is fine.
        for dashboard in grafana_url:
            start = grafana_url[dashboard].split("?")[1]
            start = start.split("&")[0].split('=')[1]
            end = grafana_url[dashboard].split("&")[1].split('=')[1]
            graphite_url = grafana_url[dashboard].split(":")[1].strip("/")
            graphite_port = "8008"
            self._timeseries_metadata_present = True
            self._graphite_url = "http://{}:{}".format(graphite_url,
                                                       graphite_port)
            self._metrics_root = cloud_name
            self._metrics_start = int(int(start) / 1000)
            self._metrics_end = int(int(end) / 1000)
