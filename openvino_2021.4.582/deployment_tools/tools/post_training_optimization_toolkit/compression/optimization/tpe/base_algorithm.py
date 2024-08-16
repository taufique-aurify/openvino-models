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

try:
    # pylint: disable=unused-import
    import hyperopt
    from .algorithm import TpeOptimizer

    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False


from compression.optimization.optimizer import Optimizer
from compression.optimization.optimizer_selector import OPTIMIZATION_ALGORITHMS


@OPTIMIZATION_ALGORITHMS.register('Tpe')
class Tpe(Optimizer):
    def __init__(self, config, pipeline, engine):
        super().__init__(config, pipeline, engine)
        if HYPEROPT_AVAILABLE:
            self.optimizer = TpeOptimizer(config, pipeline, engine)
        else:
            raise ModuleNotFoundError(
                'Cannot import the hyperopt package which is a dependency '
                'of the TPE algorithm. '
                'Please install hyperopt via `pip install hyperopt==0.1.2 pandas==0.24.2`'
            )

    def run(self, model):
        return self.optimizer.run(model)
