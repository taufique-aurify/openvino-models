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

import numpy as np
import scipy.stats


def calc_clipped_mean(mean, sigma, a, b):
    normal = scipy.stats.norm()
    alpha = (a - mean) / sigma
    beta = (b - mean) / sigma
    result = sigma * (normal.pdf(alpha) - normal.pdf(beta)) + \
        mean * (normal.cdf(beta) - normal.cdf(alpha))

    if a < np.inf:
        result += a * normal.cdf(alpha)
    if b < np.inf:
        result += b * (1 - normal.cdf(beta))

    return result


def calc_clipped_sigma(mean, sigma, a, b):
    normal = scipy.stats.norm()
    alpha = (a - mean) / sigma
    beta = (b - mean) / sigma
    Z = normal.cdf(beta) - normal.cdf(alpha)
    cmean = calc_clipped_mean(mean, sigma, a, b)
    result = Z * ((mean ** 2) + (sigma ** 2) + (cmean ** 2) - 2 * cmean * mean) + \
        sigma * (mean - 2 * cmean) * (normal.pdf(alpha) - normal.pdf(beta))

    if a < np.inf:
        result += sigma * a * normal.pdf(alpha) + ((a - cmean) ** 2) * normal.cdf(alpha)
    if b < np.inf:
        result += -sigma * b * normal.pdf(beta) + ((b - cmean) ** 2) * (1 - normal.cdf(beta))

    if ((result < 0) & (abs(result) > 1e-10)).any():
        raise RuntimeError('Negative variance')

    result[result < 0] = 0
    result = np.sqrt(result)
    return result
