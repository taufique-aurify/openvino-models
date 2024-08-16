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
from functools import partial

import numpy as np
from ..function_selector import WEIGHTS_STATS_FN, PERTENSOR, PERCHANNEL

w_stats_fn_per_tensor = WEIGHTS_STATS_FN[PERTENSOR]
w_stats_fn_per_channel = WEIGHTS_STATS_FN[PERCHANNEL]


# helper functions to calculate per-filter statistics for weights
def calculate_per_filter_stats(weights, fn, transpose=False):
    """ Calculates per-filter statistics for weights using a specific function
    :param weights: model layer weights
    :param fn: function to calculate per-filter statistics
    :param transpose: transpose weights data from IOHW to OIHW to collect stats
    :return statistics generated by fn
    """
    if transpose:
        weights_shape = [1, 0]
        original_axes = np.array(range(len(weights.shape)))
        weights_shape.extend(original_axes[2:])
        weights = np.transpose(weights, weights_shape)
    t = np.reshape(weights, (weights.shape[0], -1))
    return fn(t, axis=1)


@w_stats_fn_per_tensor.register('max')
def max_per_tensor(weights):
    return np.max(weights)


@w_stats_fn_per_tensor.register('min')
def min_per_tensor(weights):
    return np.min(weights)


@w_stats_fn_per_tensor.register('abs_max')
def abs_max_per_tensor(weights):
    return np.max(np.abs(weights))


@w_stats_fn_per_tensor.register('quantile')
def quantile_per_tensor(weights, q):
    return np.quantile(weights, q=q)


@w_stats_fn_per_tensor.register('abs_quantile')
def abs_quantile_per_tensor(weights, q):
    return np.quantile(np.abs(weights), q=q)


@w_stats_fn_per_channel.register('max')
def max_per_filter(weights, transpose=False):
    return calculate_per_filter_stats(weights, np.max, transpose=transpose)


@w_stats_fn_per_channel.register('min')
def min_per_filter(weights, transpose=False):
    return calculate_per_filter_stats(weights, np.min, transpose=transpose)


@w_stats_fn_per_channel.register('abs_max')
def abs_max_per_filter(weights, transpose=False):
    return max_per_filter(np.abs(weights), transpose=transpose)


@w_stats_fn_per_channel.register('quantile')
def quantile_per_filter(weights, q, transpose=False):
    return calculate_per_filter_stats(weights, partial(np.quantile, q=q), transpose=transpose)


@w_stats_fn_per_channel.register('abs_quantile')
def abs_quantile_per_filter(weights, q, transpose=False):
    return quantile_per_filter(np.abs(weights), q, transpose=transpose)
