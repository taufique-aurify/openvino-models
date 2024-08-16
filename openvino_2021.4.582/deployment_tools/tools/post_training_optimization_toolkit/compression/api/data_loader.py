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

from abc import ABC, abstractmethod


class DataLoader(ABC):
    """An abstract class representing a dataset.

    All custom datasets should inherit.
    ``__len__`` provides the size of the dataset and
    ``__getitem__`` supports integer indexing in range from 0 to len(self)
    """

    def __init__(self, config):
        """ Constructor
        :param config: data loader specific config
        """
        self.config = config

    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __len__(self):
        pass
