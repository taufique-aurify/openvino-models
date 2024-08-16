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

from .ie_engine import IEEngine
from .utils import append_stats


class SimplifiedEngine(IEEngine):
    @staticmethod
    def _process_batch(batch):
        """ Processes batch data and returns lists of annotations, images and batch meta data
        :param batch: a list with batch data [image]
        :returns None as annotations
                 a list with input data  [image]
                 None as meta_data
        """
        return None, batch, None

    def _process_infer_output(self, stats_layout, predictions,
                              batch_annotations, batch_meta, need_metrics_per_sample):
        # Collect statistics
        if stats_layout:
            append_stats(self._accumulated_layer_stats, stats_layout, predictions, 0)
