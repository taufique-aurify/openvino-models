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

import itertools

from ..utils.logger import get_logger


logger = get_logger(__name__)


def product_dict(d):
    keys = d.keys()
    vals = d.values()
    for instance in itertools.product(*vals):
        yield dict(zip(keys, instance))


def check_params(algo_name, config, supported_params):
    """ Check algorithm parameters in config
        :param algo_name: name of algorithm
        :param config: config with parameters to check
        :param supported_params: parameters supported by algorithm
    """
    for key, value in config.items():
        if key not in supported_params:
            raise RuntimeError('Algorithm {}. Unknown parameter: {}'.format(algo_name, key))
        if isinstance(value, dict):
            if isinstance(supported_params[key], dict):
                check_params(algo_name, value, supported_params[key])
            else:
                raise RuntimeError('Algorithm {}. Wrong structure for parameter: {}'.format(algo_name, key))
