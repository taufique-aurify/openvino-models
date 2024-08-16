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

from ..api.engine import Engine
from ..pipeline.pipeline import Pipeline


class Optimizer(ABC):
    def __init__(self, config, pipeline: Pipeline, engine: Engine):
        """ Constructor
         :param config: optimizer config
         :param pipeline: pipeline of algorithms to optimize
         :param engine: entity responsible for communication with dataset
          """
        self._config, self._pipeline, self._engine = config.params, pipeline, engine
        self.name = config.name

    @abstractmethod
    def run(self, model):
        """ Run optimizer on model
        :param model: model to apply optimization
         """
