#
# Copyright 2020-2021 Intel Corporation.
#
# LEGAL NOTICE: Your use of this software and any required dependent software
# (the "Software Package") is subject to the terms and conditions of
# the Intel(R) OpenVINO(TM) Distribution License for the Software Package,
# which may also include notices, disclaimers, or license terms for
# third party or open source software included in or with the Software Package,
# and your use indicates your acceptance of all such terms. Please refer
# to the "third-party-programs.txt" or other similarly-named text file
# included with the Software Package for additional details.

from abc import ABC, abstractmethod


class Engine(ABC):
    """Engine for model inference. Collects statistics for activations,
    calculates accuracy metrics for the dataset
    """

    def __init__(self, config, data_loader=None, metric=None):
        """ Constructor
         :param config: engine specific config
         :param data_loader: entity responsible for communication with dataset
         :param metric: entity for metric calculation
        """
        self.config = config
        self._data_loader = data_loader
        self._metric = metric
        self._stat_requests_number = config.get('stat_requests_number', None)
        self._eval_requests_number = config.get('eval_requests_number', None)

    def set_model(self, model):
        """ Set/reset model to instance of engine class
         :param model: NXModel instance for inference
        """

    @property
    def data_loader(self):
        if self._data_loader.__len__() == 0:
            raise RuntimeError('Empty data loader! '
                               'Please make sure that the calibration dataset '
                               'you provided is correct and contains at least a number of samples '
                               'defined in the configuration file.')
        return self._data_loader

    @property
    def metric(self):
        return self._metric

    @abstractmethod
    def predict(self, stats_layout=None, sampler=None, metric_per_sample=False, print_progress=False):
        """ Performs model inference on specified dataset subset
         :param stats_layout: dict of stats collection functions {node_name: {stat_name: fn}} (optional)
         :param sampler: sampling dataset to make inference
         :param metric_per_sample: If Metric is specified and the value is True,
                then the metric value will be calculated for each data sample, otherwise for the whole dataset
         :param print_progress: Whether to print inference progress
         :returns a tuple of dictionaries of persample and overall metric values if 'metric_per_sample' is True
                  ({sample_id: sample index, 'metric_name': metric name, 'result': metric value},
                   {metric_name: metric value}), otherwise, a dictionary of overall metrics
                   {metric_name: metric value}
                  a dictionary of collected statistics {node_name: {stat_name: [statistics]}}
        """

    def get_metrics_attributes(self):
        """Returns a dictionary of metrics attributes {metric_name: {attribute_name: value}}"""
        return self._metric.get_attributes()
