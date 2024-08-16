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

import sys
from argparse import ArgumentParser

import extractor


def parse_args(argv):
    """
    Parse and process arguments for frames-extractor tool
    """
    parser = ArgumentParser(description='Frames-extractor toolkit', allow_abbrev=False)
    parser.add_argument(
        '-v',
        '--video',
        help='Full path to video file',
        required=True)
    parser.add_argument(
        '-o',
        '--output_dir',
        help='Directory to save valuable frames from video.',
        required=True)
    parser.add_argument(
        '-f',
        '--frame_step',
        type=int,
        help='Read frames from video with step',
        default=1,
        required=False
    )
    parser.add_argument(
        '-e',
        '--ext',
        type=str,
        help='Extension of images in resulting dataset',
        choices=['jpg', 'png'],
        default='png',
        required=False
    )
    parser.add_argument(
        '-s',
        '--dataset_size',
        type=int,
        help='Number of frames to save from video as dataset.'
             'Should be less then video frames number',
        default=None,
        required=False)
    args = parser.parse_args(args=argv)

    return args.video, args.output_dir, args.dataset_size, args.frame_step


if __name__ == '__main__':
    extractor.extract_frames_and_make_dataset(*parse_args(sys.argv[1:]))
