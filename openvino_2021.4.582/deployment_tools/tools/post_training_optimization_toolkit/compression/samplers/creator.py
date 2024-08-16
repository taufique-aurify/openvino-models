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

import random

from compression.engines.ac_engine import ACEngine
from compression.samplers.batch_sampler import BatchSampler
from compression.samplers.index_sampler import IndexSampler


def create_sampler(engine, samples, shuffle_data=False, seed=0):
    """ Helper function to create the most common samplers. Suits for the most algorithms
    :param engine: instance of engine class
    :param samples: a list of dataset indices or a number of samples to draw from dataset
    :param shuffle_data: a boolean flag. If it's True and samples param is a number then
     subset indices will be choice randomly
    :param seed: a number for initialization of the random number generator
    :return instance of Sampler class suitable to passed engine
    """

    if isinstance(samples, int):
        if shuffle_data:
            random.seed(seed)
            samples = random.sample(range(len(engine.data_loader)), samples)
        else:
            samples = range(samples)

    if isinstance(engine, ACEngine):
        return IndexSampler(subset_indices=samples)

    return BatchSampler(engine.data_loader, subset_indices=samples)
