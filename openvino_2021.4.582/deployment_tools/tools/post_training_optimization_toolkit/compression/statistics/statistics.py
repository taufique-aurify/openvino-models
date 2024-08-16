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

from functools import partial


class Statistic:
    def __init__(self, func, *argv, **kwargs):
        self.func = func
        self.argv = argv
        self.kwargs = kwargs

    def compute(self, *input_tensor, **kwargs):
        pass

    def __eq__(self, other):
        if isinstance(other, Statistic):
            return self.func == other.func and self.argv == other.argv \
                   and self.kwargs == other.kwargs
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __call__(self, *argv, **kwargs):
        return self.compute(*argv, **kwargs)

    def __hash__(self):
        data = (self.func, frozenset(self.argv), frozenset(self.kwargs))
        if isinstance(self.func, partial):
            data = (*data, frozenset(self.func.keywords))
        return hash(data)


class TensorStatistic(Statistic):
    def compute(self, *input_tensor, **kwargs):
        return self.func(*(input_tensor + self.argv), **self.kwargs)


class TensorStatisticAxis(Statistic):
    def compute(self, *input_tensor, **kwargs):
        return self.func(*(input_tensor + self.argv), **self.kwargs)


class SQNRStatistic(Statistic):
    def __init__(self, func, qsuffix, *argv, **kwargs):
        super().__init__(func, *argv, **kwargs)
        self.qsuffix = qsuffix

    # pylint: disable=W0221
    def compute(self, activation_dict, layer_key, **kwargs):
        return self.func(
            activation_dict[layer_key],
            activation_dict[layer_key + self.qsuffix],
            **kwargs
        )


def compute_statistic(statistic, *argv, **kwargs):
    if isinstance(argv[0], dict):
        activations_dict, layer_key = argv
        tensor = (activations_dict[layer_key],)
        if isinstance(statistic, SQNRStatistic):
            return statistic.compute(activations_dict, layer_key)
        if isinstance(statistic, TensorStatisticAxis):
            return statistic.compute(*tensor, layer_key)
    else:
        tensor = argv
    return statistic(*tensor, **kwargs)
