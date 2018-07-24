"""
Carbon/Grafana client module usable for generating data for Tendrl-Grafana.
"""

import json
import socket
import urllib.request

import logging

import usmqe_cmdg.data_generators

LOGGER = logging.getLogger("usmqe_cmdg.%s" % __name__)


class CarbonClient(object):
    """
    Carbon Client class.
    """

    def __init__(self, server, carbon_port, grafana_port):
        """
        Initialize CarbonClient, required parameters are:
        * server
        * carbon_port
        * grafana_port
        """
        self.server = server
        self.carbon_port = carbon_port
        self.grafana_port = grafana_port
        self.__carbon_socket = None

    def __get_carbon_socket(self):
        """
        Prepare and return carbon socket.
        """
        if not self.__carbon_socket:
            self.__carbon_socket = socket.socket()
            self.__carbon_socket.connect((self.server, self.carbon_port))
        return self.__carbon_socket

    def list_metrics(self, filters=""):
        """
        Load list of available metrics from Grafana.
        * filters:  space separated list of filtered strings,
                    exclamation mark before word means negative filter
        """
        metrics = urllib.request.urlopen( \
            "http://%s:%s/api/datasources/proxy/1/metrics/index.json" % \
            (self.server, self.grafana_port)).read()
        metrics = json.loads(metrics)
        metrics = filter_metrics_list(metrics, filters)
        return metrics

    def generate_metrics(self, cfg):
        """
        Generate and push metrics based on cfg.
        """
        # filter available metrics based on cfg"[filter"]
        for metric in self.list_metrics(cfg["filter"]):
            LOGGER.info("Generating metrics for: %s", metric)
            dg = usmqe_cmdg.data_generators.DataGenerators(metric, cfg["since"], cfg["until"])
            # iterate through the time period
            for timestamp in range(cfg["since"], cfg["until"], cfg["interval"]):
                dg.prev_value = 0
                # combine all listed generators to one value
                for generator in cfg["generators"]:
                    value = dg.data_generator( \
                            generator['name'], \
                            timestamp, \
                            generator)
                # push generated value into carbon
                self.__push_metric(metric, value, timestamp)

    def __push_metric(self, metric_name, value, timestamp):
        """
        Push metrics into carbon.
        """
        sock = self.__get_carbon_socket()
        _data = "%s %d %d\n" % (metric_name, value, timestamp)
        LOGGER.debug("SEND: %s", _data.replace("\n", ""))
        sock.send(_data.encode('utf-8'))

def filter_metrics_list(metrics_list, filters):
    """
    Filter metrics list based on filters:
    * filters:  space separated list of filtered strings,
                exclamation mark before word means negative filter
    """
    if isinstance(filters, str):
        filters = filters.split()
    for _filter in filters:
        if _filter[0] == '!':
            # process negative filter
            _filter = _filter[1:]
            _filtered_metrics = [metric for metric in metrics_list if _filter not in metric]
        else:
            # process positive filter
            _filtered_metrics = [metric for metric in metrics_list if _filter in metric]
        metrics_list = _filtered_metrics

    # filter "archive" metrics
    _filtered_metrics = [metric for metric in metrics_list if ".archive." not in metric]
    metrics_list = _filtered_metrics
    return metrics_list
