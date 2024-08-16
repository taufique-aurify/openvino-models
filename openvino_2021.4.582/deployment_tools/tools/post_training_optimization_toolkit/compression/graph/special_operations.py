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

QUANTIZE_AGNOSTIC_OPERATIONS = [
    {'type': 'MaxPool'},
    {'type': 'ReduceMax'},
    {'type': 'Reshape'},
    {'type': 'Concat'},
    {'type': 'Flatten'},
    {'type': 'Squeeze'},
    {'type': 'Unsqueeze'},
    {'type': 'Split'},
    {'type': 'VariadicSplit'},
    {'type': 'Crop'},
    {'type': 'Transpose'},
    {'type': 'Tile'},
    {'type': 'StridedSlice'},
    {'type': 'ShuffleChannels'},
    {'type': 'Broadcast'},
    {'type': 'Pad'},
    {'type': 'Minimum'},
    {'type': 'Maximum'},
    {'type': 'ConvertLike'},
]

OPERATIONS_WITH_BIAS = [
    {'type': 'Convolution'},
    {'type': 'MatMul'}
]

OPERATIONS_CHANNEL_AXIS = {'Convolution': 1, 'MatMul': -1}

OPERATIONS_WITH_WEIGHTS = [
    {'type': 'Convolution'},
    {'type': 'ConvolutionBackpropData'},
    {'type': 'GroupConvolution'},
    {'type': 'GroupConvolutionBackpropData'},
    {'type': 'MatMul'},
]

TRANSPOSED_OPERATIONS = [
    {'type': 'ConvolutionBackpropData'}
]

SPLIT_OPERATIONS = [
    {'type': 'VariadicSplit'},
    {'type': 'Split'}
]

DETECTION_OUTPUT_FINAL_TYPES = [
    {'type': 'NonMaxSuppression'},
    {'type': 'TopK'}
]

ELTWISE_TYPES = ['Add', 'Multiply', 'Subtract', 'Divide', 'Less', 'LessEqual', 'Greater', 'GreaterEqual',
                 'Equal', 'NotEqual', 'FloorMod', 'LogicalOr', 'LogicalXor', 'LogicalAnd', 'Maximum', 'Minimum']


def is_eltwise(node):
    return node.type in ELTWISE_TYPES
