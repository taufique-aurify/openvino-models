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

from typing import Union

from ..api.data_loader import DataLoader
from ..utils.ac_imports import Dataset, DatasetWrapper


class ACDataLoader(DataLoader):

    def __init__(self, data_loader: Union[Dataset, DatasetWrapper]):
        super().__init__(config=None)
        self._data_loader = data_loader

    def __len__(self):
        return self._data_loader.full_size

    def __getitem__(self, item):
        return self._data_loader[item]
