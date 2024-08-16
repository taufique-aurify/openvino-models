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

from compression.samplers.sampler import Sampler


class BatchSampler(Sampler):

    def __init__(self, data_loader, batch_size=1, subset_indices=None):
        super().__init__(data_loader, batch_size, subset_indices)
        if self._subset_indices is None:
            self._subset_indices = range(self.num_samples)

    def __len__(self):
        return self.num_samples

    def __iter__(self):
        batch = []
        for idx in self._subset_indices:
            batch.append(self._data_loader[idx])
            if len(batch) == self.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch
