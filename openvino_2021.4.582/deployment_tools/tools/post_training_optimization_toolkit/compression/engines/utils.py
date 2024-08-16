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

from collections import defaultdict
import numpy as np

from ..statistics.statistics import compute_statistic
from ..utils.logger import get_logger

logger = get_logger(__name__)


def append_stats(accumulated_layer_stats, stats_layout, value, dataset_index):
    if isinstance(value, list):
        value = parse_sequential_stats(value, stats_layout)

    for layer in value:
        if layer in stats_layout:
            if layer not in accumulated_layer_stats:
                accumulated_layer_stats[layer] = {stat_name: [] for stat_name in stats_layout[layer]}
            for stat_name, stat_fn in stats_layout[layer].items():
                accumulated_layer_stats[layer][stat_name].append(
                    (dataset_index, compute_statistic(stat_fn, value, layer)))


def parse_sequential_stats(value_sequential, stats_layout):
    activation_seq = defaultdict(lambda: [])
    for value in value_sequential:
        for layer, activations in value.items():
            if layer in stats_layout:
                activation_seq[layer].append(activations)

    for layer, act_seq in activation_seq.items():
        axis = 1 if len(act_seq[0].shape) == 2 else 2
        activation_seq[layer] = np.stack(act_seq, axis=axis)
    return activation_seq


def process_accumulated_stats(accumulated_stats, stat_names_aliases=None):
    for layer in accumulated_stats:
        for stat in accumulated_stats[layer]:
            accumulated_stats[layer][stat].sort(key=lambda el: el[0])
            accumulated_stats[layer][stat] = [el[1] for el in accumulated_stats[layer][stat]]

    # pack IE-like stats names into original ones
    if stat_names_aliases is not None:
        accumulated_stats = {stat_names_aliases[key]: value
                             for key, value in accumulated_stats.items()}

    return accumulated_stats
