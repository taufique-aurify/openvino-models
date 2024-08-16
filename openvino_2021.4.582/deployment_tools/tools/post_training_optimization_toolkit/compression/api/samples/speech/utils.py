#
# Copyright 2021 Intel Corporation.
#
# LEGAL NOTICE: Your use of this software and any required dependent software
# (the "Software Package") is subject to the terms and conditions of
# the Intel(R) OpenVINO(TM) Distribution License for the Software Package,
# which may also include notices, disclaimers, or license terms for
# third party or open source software included in or with the Software Package,
# and your use indicates your acceptance of all such terms. Please refer
# to the "third-party-programs.txt" or other similarly-named text file
# included with the Software Package for additional details.

from compression.engines.simplified_engine import SimplifiedEngine


class ArkEngine(SimplifiedEngine):
    def _fill_input(self, model, image_batch):
        if 'input_names' in self.data_loader.config:
            feed_dict = {}
            for input_name in self.data_loader.config['input_names']:
                feed_dict[input_name] = image_batch[0][input_name]
            return feed_dict
        raise Exception('input_names is not provided!')
