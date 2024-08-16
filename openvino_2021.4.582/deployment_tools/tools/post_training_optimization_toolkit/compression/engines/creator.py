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

from compression.engines.ac_engine import ACEngine
from compression.engines.simplified_engine import SimplifiedEngine


def create_engine(config, **kwargs):
    """
    Factory to create instance of engine class based on config
    :param config: engine config section from toolkit config file
    :param kwargs: additional arguments specific for every engine class (data_loader, metric)
    :return: instance of Engine descendant class
    """
    if config.type == 'accuracy_checker':
        return ACEngine(config)
    if config.type == 'simplified':
        return SimplifiedEngine(config, **kwargs)
    raise RuntimeError('Unsupported engine type')
