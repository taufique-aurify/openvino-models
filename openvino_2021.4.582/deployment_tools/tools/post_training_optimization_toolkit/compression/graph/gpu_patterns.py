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

from .pattern_utils import check_fused_scale_shift_patterns, get_fused_scale_shift_patterns, \
    check_fused_op_const_patterns, get_fused_op_const_pattern, get_clamp_mult_const_pattern


def get_gpu_ignored_patterns():
    return {
        'blocks': [(pattern, check_fused_scale_shift_patterns) for pattern in get_fused_scale_shift_patterns()] +
                  [(pattern, check_fused_op_const_patterns) for pattern in get_fused_op_const_pattern()],
        'activations': [get_clamp_mult_const_pattern()],
        'inputs': []
    }
