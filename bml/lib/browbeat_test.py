

class browbeat_test(object):

    # Takes a uuid and a raw set of elastic data to populate the object
    # in this case raw_elastic is going to be a test of test indexes
    def __init__(self,
                 raw_elastic,
                 uuid, test_name,
                 workload,
                 training_output=None):
        self.uuid = uuid
        self.name = test_name
        self.workload = workload
        self._set_metadata(raw_elastic)
        self.raw = self._get_raw_data(raw_elastic)
        # Using during model training, true false for now, to be expanded
        self._training_output=training_output

    def _get_raw_data(self, raw_elastic):
        if 'raw' in raw_elastic['_source']:
            return raw_elastic['_source']['raw']
        else:
            raise ValueError('Invalid test data!')

    def _set_hardware_metadata(self, hardware_details):
        self.nodes = len(hardware_details)
        self.os_name = hardware_details[0]['os_name']
        self.os_name = self._typecheck_string(self.os_name)
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
            raise ValueError("String metadata value is not a string!")

    # Extracts details of the really run
    def _set_metadata(self, raw_elastic):
        self._set_hardware_metadata(
            raw_elastic['_source']['hardware-metadata']['hardware_details'])
        self._set_software_metadata(
            raw_elastic['_source']['software-metadata'])
        if 'rally' in self.workload:
            self.concurrency = \
                raw_elastic['_source']['rally_setup']\
                           ['kw']['runner']['concurrency']
            self.concurrency = self._typecheck_num(self.concurrency)
            self.times = \
                raw_elastic['_source']['rally_setup']['kw']['runner']['times']
            self.times = self._typecheck_num(self.times)
            self.version = raw_elastic['_source']['version']['osp_version']
            self.version = self._typecheck_string(self.version)
            self.cloud_name = raw_elastic['_source']['cloud_name']
            self.run = raw_elastic['_source']['iteration']
            self.run = self._typecheck_num(self.run)
            self.dlrn_hash = raw_elastic['_source']['version']['dlrn_hash']
