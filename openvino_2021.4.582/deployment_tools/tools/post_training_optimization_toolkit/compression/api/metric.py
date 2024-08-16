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


class Metric(ABC):
    """An abstract class representing an accuracy metric. """

    def __init__(self):
        """ Constructor """
        self.reset()

    @property
    @abstractmethod
    def value(self):
        """ Returns accuracy metric value for the last model output. """

    @property
    @abstractmethod
    def avg_value(self):
        """ Returns accuracy metric value for all model outputs. """

    @abstractmethod
    def update(self, output, target):
        """ Calculates and updates accuracy metric value
        :param output: model output
        :param target: annotations
        """

    @abstractmethod
    def reset(self):
        """ Reset accuracy metric """

    def __call__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @property
    def higher_better(self):
        """Attribute whether the metric should be increased"""
        return True

    @abstractmethod
    def get_attributes(self):
        """
        Returns a dictionary of metric attributes {metric_name: {attribute_name: value}}.
        Required attributes: 'direction': 'higher-better' or 'higher-worse'
                             'type': metric type
        """
