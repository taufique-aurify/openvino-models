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


class Sampler(ABC):

    def __init__(self, data_loader=None, batch_size=1, subset_indices=None):
        """ Constructor
        :param data_loader: instance of DataLoader class to read data
        :param batch_size: number of items in batch
        :param subset_indices: indices of samples to read
        If subset_indices argument is set to None then Sampler class
        will take elements from the whole dataset"""
        self._data_loader, self.batch_size = data_loader, batch_size
        self._subset_indices = subset_indices

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @property
    def num_samples(self):
        if self._subset_indices is None:
            return len(self._data_loader) if self._data_loader else None
        return len(self._subset_indices)
