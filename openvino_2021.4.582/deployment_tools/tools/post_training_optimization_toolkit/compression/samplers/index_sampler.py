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


class IndexSampler(Sampler):

    def __init__(self, subset_indices):
        super().__init__(subset_indices=subset_indices)

    def __len__(self):
        return self.num_samples

    def __iter__(self):
        for idx in self._subset_indices:
            yield idx

    def __getitem__(self, idx):
        return self._subset_indices[idx]
