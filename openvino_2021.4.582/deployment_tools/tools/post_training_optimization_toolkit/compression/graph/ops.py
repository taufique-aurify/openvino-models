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

import glob
import os.path
import importlib
import inspect
import mo.ops
import extensions.ops


def get_operations_list():
    ops = {}
    for package in [extensions.ops, mo.ops]:
        for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(package.__file__)), '*.py')):
            name = '.{}'.format(os.path.splitext(os.path.basename(file))[0])
            module = importlib.import_module(name, package.__name__)
            for key in dir(module):
                obj = getattr(module, key)
                if inspect.isclass(obj):
                    op = getattr(obj, 'op', None)
                    if op is not None:
                        ops[op] = obj
    return ops


OPERATIONS = get_operations_list()
