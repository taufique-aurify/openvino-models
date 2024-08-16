#
# Copyright 2021 Intel Corporation.
#
# LEGAL NOTICE: Your use of this software and any required dependent software
# (the "Software Package") is subject to the terms and conditions of
# the Intel(R) OpenVINO(TM) Distribution License for the Software Package,
# which may also include notices, disclaimers, or license terms for
# third party or open source software included in or with the Software Package,
# and your use indicates your acceptance of all such terms. Please refer
# to the "third-party-programs.txt" or other similarly-named text file
# included with the Software Package for additional details.

import torch

from compression.graph import node_utils as nu
from compression.utils.logger import get_logger


logger = get_logger(__name__)


def get_optimization_params(loss_name, optimizer_name):
    loss_fn_map = {
        'l2': torch.nn.MSELoss(),
    }

    optimizer_map = {
        'Adam': torch.optim.Adam,
        'SGD': torch.optim.SGD,
    }
    return loss_fn_map[loss_name], optimizer_map[optimizer_name]


def get_weight_node(node, port_id=1):
    node_weight = nu.get_node_input(node, port_id)
    if node_weight.type == 'FakeQuantize':
        node_weight = nu.get_node_input(node_weight, 0)
    if node_weight.type != 'Const':
        raise ValueError('Provided weight node is not Const!')
    return node_weight
