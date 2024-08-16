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


import datetime


def get_timestamp():
    return datetime.datetime.strftime(
        datetime.datetime.now(), '%Y-%m-%d_%H-%M-%S')


def get_timestamp_precise():
    return datetime.datetime.strftime(
        datetime.datetime.now(), '%Y-%m-%d_%H-%M-%S.%f')


def get_timestamp_short():
    return datetime.datetime.strftime(
        datetime.datetime.now(), '%H-%M-%S')
