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

from compression.data_loaders.image_loader import ImageLoader
from compression.graph.model_utils import get_nodes_by_type


def create_data_loader(config, model):
    """
    Factory to create instance of engine class based on config
    :param config: engine config section from toolkit config file
    :param model: NXModel instance to find out input shape
    :return: instance of DataLoader descendant class
    """

    inputs = get_nodes_by_type(model, ['Parameter'])

    if len(inputs) > 1 and\
            not any([tuple(i.shape) == (1, 3) for i in inputs]):
        raise RuntimeError('IEEngine supports networks with single input or net with 2 inputs. '
                           'In second case there are image input and image info input '
                           'Actual inputs number: {}'.format(len(inputs)))

    data_loader = None
    for in_node in inputs:
        if tuple(in_node.shape) != (1, 3):
            data_loader = ImageLoader(config)
            data_loader.shape = in_node.shape
            return data_loader

    if data_loader is None:
        raise RuntimeError('There is no node with image input')

    return data_loader
