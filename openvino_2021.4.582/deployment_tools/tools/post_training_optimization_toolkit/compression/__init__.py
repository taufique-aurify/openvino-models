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

from .algorithms.quantization.accuracy_aware.algorithm import AccuracyAwareQuantization
from .algorithms.quantization.accuracy_aware.mixed_precision import (
    INT4MixedQuantization,
)
from .algorithms.quantization.fast_bias_correction.algorithm import FastBiasCorrection
from .algorithms.quantization.bias_correction.algorithm import BiasCorrection
from .algorithms.quantization.channel_alignment.algorithm import (
    ActivationChannelAlignment,
)
from .algorithms.quantization.datafree.algorithm import DataFreeQuantization
from .algorithms.quantization.default.algorithm import DefaultQuantization
from .algorithms.quantization.minmax.algorithm import MinMaxQuantization
from .algorithms.quantization.optimization.rangeopt import RangeOptimization
from .algorithms.quantization.optimization.params_tuning import (
    ParamsGridSearchAlgorithm,
)
from .algorithms.quantization.qnoise_estimator.algorithm import QuantNoiseEstimator
from .algorithms.quantization.tunable_quantization.algorithm import TunableQuantization
from .algorithms.quantization.outlier_channel_splitting.algorithm import (
    OutlierChannelSplitting,
)
from .algorithms.quantization.weight_bias_correction.algorithm import (
    WeightBiasCorrection,
)
from .algorithms.sparsity.magnitude_sparsity.algorithm import MagnitudeSparsity
from .algorithms.sparsity.default.algorithm import WeightSparsity
from .algorithms.sparsity.default.base_algorithm import BaseWeightSparsity
from .optimization.tpe.base_algorithm import Tpe
from .algorithms.quantization.overflow_correction.algorithm import OverflowCorrection

QUANTIZATION_ALGORITHMS = [
    'MinMaxQuantization',
    'RangeOptimization',
    'FastBiasCorrection',
    'BiasCorrection',
    'ActivationChannelAlignment',
    'DataFreeQuantization',
    'DefaultQuantization',
    'AccuracyAwareQuantization',
    'INT4MixedQuantization',
    'TunableQuantization',
    'Tpe',
    'QuantNoiseEstimator',
    'OutlierChannelSplitting',
    'WeightBiasCorrection',
    'ParamsGridSearchAlgorithm',
    'OverflowCorrection',
]

SPARSITY_ALGORITHMS = ['WeightSparsity',
                       'MagnitudeSparsity',
                       'BaseWeightSparsity']

__all__ = QUANTIZATION_ALGORITHMS + SPARSITY_ALGORITHMS
