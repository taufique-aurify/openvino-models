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

import numpy as np

from compression.graph import node_utils as nu
from compression.graph.model_utils import get_nodes_by_type
from compression.graph.special_operations import OPERATIONS_WITH_WEIGHTS
from compression.utils.logger import get_logger


logger = get_logger(__name__)


def check_model_sparsity_level(model,
                               sparsity_ignored_scope,
                               target_sparsity_level,
                               strict=False,
                               count_ignored_nodes=True):
    """
    Check if tuned model has the same sparsity level as set in the config
    :param model: model: NetworkX model
    :param sparsity_ignored_scope: list of layers ignored during sparsification: list
    :param target_sparsity_level: desired sparsity level of the model: float
    :param strict: whether to raise an error if actual sparsity does not equal target: bool
    :param count_ignored_nodes: whether to include non-sparsified nodes when considering total weight count: bool
    """
    perlayer_weight_sizes = []
    perlayer_sparsity_rates = []
    all_nodes_with_weights = get_nodes_by_type(
        model, [op['type'] for op in OPERATIONS_WITH_WEIGHTS]
    )
    all_nodes_with_weights = [n for n in all_nodes_with_weights if nu.get_node_input(n, 1).type == 'Const']
    if sparsity_ignored_scope is not None and not count_ignored_nodes:
        all_nodes_with_weights = [
            node
            for node in all_nodes_with_weights
            if (node.name not in sparsity_ignored_scope)
        ]
    for node in all_nodes_with_weights:
        weight_node = nu.get_weights_for_node(node)
        if weight_node is not None:
            weight = nu.get_node_value(weight_node)
            perlayer_sparsity_rates.append(np.sum(weight == 0) / weight.size)
            perlayer_weight_sizes.append(weight.size)

    logger.debug('Per-layer sparsity levels: %s', perlayer_sparsity_rates)
    logger.debug('Per-layer weight sizes %s', perlayer_weight_sizes)

    global_sparsity_rate = np.dot(
        perlayer_sparsity_rates, perlayer_weight_sizes
    ) / np.sum(perlayer_weight_sizes)
    logger.info('Sparsity rate after tuning: %s', global_sparsity_rate)
    if strict and not np.isclose(global_sparsity_rate, target_sparsity_level, atol=1e-2):
        raise RuntimeError('Target sparisty level {} was '
                           'not reached for the model: {}'.format(target_sparsity_level,
                                                                  global_sparsity_rate))
