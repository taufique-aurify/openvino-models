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

from cv2 import imread, IMREAD_GRAYSCALE

from ..api.data_loader import DataLoader
from ..data_loaders.utils import prepare_image, collect_img_files


class ImageLoader(DataLoader):

    def __init__(self, config):
        super().__init__(config)

        self._img_files = collect_img_files(config.data_source)
        self._shape = None
        self._crop_central_fraction = config.get('central_fraction', None)

    def __getitem__(self, idx):
        return self._read_and_preproc_image(self._img_files[idx])

    def __len__(self):
        return len(self._img_files)

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, shape):
        self._shape = tuple(shape)

    def _read_and_preproc_image(self, img_path):
        image = imread(img_path, IMREAD_GRAYSCALE)\
            if self._shape[1] == 1 else imread(img_path)

        if image is None:
            raise Exception('Can not read the image: {}'.format(img_path))

        return prepare_image(image, self.shape[-2:], self._crop_central_fraction)
