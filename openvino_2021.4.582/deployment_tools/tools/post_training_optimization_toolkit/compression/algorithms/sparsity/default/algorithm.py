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

from .base_algorithm import BaseWeightSparsity
from ....algorithms.algorithm import Algorithm
from ....algorithms.algorithm_selector import COMPRESSION_ALGORITHMS
from ....utils.logger import get_logger

# pylint: disable=W0611
try:
    import torch
    from ..layerwise_finetuning.algorithm import SparseModelFinetuning

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = get_logger(__name__)


@COMPRESSION_ALGORITHMS.register('WeightSparsity')
class WeightSparsity(Algorithm):
    name = 'WeightSparsity'

    def __init__(self, config, engine):
        super().__init__(config, engine)
        use_layerwise_tuning = self._config.get('use_layerwise_tuning', False)
        if use_layerwise_tuning:
            if TORCH_AVAILABLE:
                self.algo_pipeline = SparseModelFinetuning(config, engine)
            else:
                raise ModuleNotFoundError('Cannot import the torch package which is a dependency '
                                          'of the LayerwiseFinetuning algorithm. '
                                          'Please install torch via `pip install torch==1.6.0')
        else:
            self.algo_pipeline = BaseWeightSparsity(config, engine)

    @property
    def change_original_model(self):
        return True

    def run(self, model):
        self.algo_pipeline.run(model)
        logger.info('\n' + self.algo_pipeline.statistics_table.draw())
        return model
