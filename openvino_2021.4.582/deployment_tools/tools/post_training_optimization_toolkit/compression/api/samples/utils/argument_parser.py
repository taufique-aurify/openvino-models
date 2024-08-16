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

from argparse import ArgumentParser


def get_common_argparser():
    parser = ArgumentParser(description='Post-training Compression Toolkit Sample',
                            allow_abbrev=False)
    parser.add_argument(
        '-m',
        '--model',
        help='Path to the xml file with model',
        required=True)
    parser.add_argument(
        '-w',
        '--weights',
        help='Path to the bin file with model weights',
        required=False)
    parser.add_argument(
        '-d',
        '--dataset',
        help='Path to the directory with data',
        required=True)

    return parser
