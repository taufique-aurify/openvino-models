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

from ..utils.registry import Registry, RegistryStorage

COMPRESSION_ALGORITHMS = Registry('QuantizationAlgos')
REGISTRY_STORAGE = RegistryStorage(globals())


def get_registry(name):
    return REGISTRY_STORAGE.get_registry(name)


def get_algorithm(name):
    if name.startswith('.') or name.endswith('.'):
        raise Exception('The algorithm name cannot start or end with "."')

    if '.' in name:
        ind = name.find('.')
        reg_name = name[:ind]
        algo_name = name[ind + 1:]
    else:
        reg_name = 'QuantizationAlgos'
        algo_name = name

    reg = get_registry(reg_name)
    return reg.get(algo_name)
