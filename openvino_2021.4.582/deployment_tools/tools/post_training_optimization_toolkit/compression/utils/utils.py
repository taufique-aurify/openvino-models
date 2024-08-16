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

import os
import tempfile


def create_tmp_dir(parent_dir=tempfile.gettempdir()):
    """ Creates temporary directory with unique name and auto cleanup
    :param parent_dir: directory in which temporary directory is created
    :return: TemporaryDirectory object
    """
    parent_dir = tempfile.TemporaryDirectory(dir=parent_dir)
    if not os.path.exists(parent_dir.name):
        try:
            os.makedirs(parent_dir.name)
        except PermissionError as e:
            raise type(e)(
                'Failed to create directory {}. Permission denied. '.format(parent_dir))
    return parent_dir


def convert_output_key(name):
    """ Convert output name into IE-like name
    :param name: output name to convert
    :return: IE-like output name
    """
    if not isinstance(name, tuple):
        return name
    if len(name) != 2:
        raise Exception('stats name should be a string name or 2 elements tuple '
                        'with string as the first item and port number the second')
    return '{}.{}'.format(*name)


class Environment:
    def __init__(self, variable, value):
        self.variable = variable
        self.value = value
        self.was_set = (self.variable in os.environ)

    def __enter__(self):
        os.environ[self.variable] = self.value

    def __exit__(self, *args):
        if not self.was_set:
            del os.environ[self.variable]
