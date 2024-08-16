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


try:
    from libs.open_model_zoo.tools.accuracy_checker.\
        accuracy_checker.evaluators.quantization_model_evaluator import create_model_evaluator
    from libs.open_model_zoo.tools.accuracy_checker.accuracy_checker.config import ConfigReader
    from libs.open_model_zoo.tools.accuracy_checker.accuracy_checker.dataset import\
        Dataset, DataProvider as DatasetWrapper
    from libs.open_model_zoo.tools.accuracy_checker.accuracy_checker.logging\
        import _DEFAULT_LOGGER_NAME

except ImportError:
    from accuracy_checker.evaluators.quantization_model_evaluator import create_model_evaluator
    from accuracy_checker.config import ConfigReader
    from accuracy_checker.dataset import Dataset
    from accuracy_checker.logging import _DEFAULT_LOGGER_NAME
    try:
        from accuracy_checker.dataset import DataProvider as DatasetWrapper
    except ImportError:
        from accuracy_checker.dataset import DatasetWrapper
