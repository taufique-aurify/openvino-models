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

from cv2 import VideoCapture, CAP_PROP_FRAME_COUNT


class VideoLoader:

    def __init__(self, video_file):
        self._frame_pointer = -1

        self._video_file = video_file
        self._capture = VideoCapture(video_file)

    def __getitem__(self, idx):

        if idx >= len(self) or idx < 0:
            raise IndexError

        if idx < self._frame_pointer:
            self._capture = VideoCapture(self._video_file)
            self._frame_pointer = -1

        image = None
        while self._frame_pointer < idx:
            _, image = self._capture.read()
            self._frame_pointer += 1

        if image is not None:
            return image

    def __len__(self):
        return int(self._capture.get(CAP_PROP_FRAME_COUNT))
