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

import os
from addict import Dict

from compression.graph import load_model, save_model
from compression.pipeline.initializer import create_pipeline
from compression.utils.logger import init_logger
from compression.api.samples.utils.argument_parser import get_common_argparser
from compression.api.samples.speech.data_loader import ArkDataLoader
from compression.api.samples.speech.utils import ArkEngine


def parse_args():
    parser = get_common_argparser()
    parser.add_argument(
        '-i',
        '--input_names',
        help='List of input names of network',
        required=True
    )
    parser.add_argument(
        '-f',
        '--files_for_input',
        help='List of filenames mapped to input names (without .ark extension)',
        required=True
    )
    parser.add_argument(
        '-p',
        '--preset',
        help='Preset for quantization.'
             '-performance for INT8 weights and INT16 inputs'
             '-accuracy for INT16 weights and inputs',
        default='accuracy',
        choices=['performance', 'accuracy'])
    parser.add_argument(
        '-o',
        '--output',
        help='Path to save the quantized model',
        default='./model/optimized')
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='Log level to print')
    parser.add_argument(
        '-s',
        '--subset_size',
        help='Subset size for calibration',
        default=2000,
        type=int)
    return parser.parse_args()


def get_configs(args):
    if not args.weights:
        args.weights = '{}.bin'.format(os.path.splitext(args.model)[0])

    model_config = Dict({
        'model_name': 'gna_model',
        'model': os.path.expanduser(args.model),
        'weights': os.path.expanduser(args.weights)
    })
    engine_config = Dict({
        'device': 'CPU'
    })
    dataset_config = {
        'data_source': os.path.expanduser(args.dataset),
        'type': 'simplified',
        'input_names': args.input_names.split(',')
    }

    if args.files_for_input is not None:
        dataset_config['input_files'] = args.files_for_input.split(',')

    algorithms = [
        {
            'name': 'DefaultQuantization',
            'params': {
                'target_device': 'GNA',
                'preset': args.preset,
                # The custom configuration is for speech recognition models
                'stat_subset_size': args.subset_size,
                'activations': {
                    'range_estimator': {
                        'max': {
                            'type': 'abs_max',
                            'aggregator': 'max'
                        }
                    }
                }
            }
        }
    ]

    return model_config, engine_config, dataset_config, algorithms


def optimize_model(args):
    model_config, engine_config, dataset_config, algorithms = get_configs(args)
    data_loader = ArkDataLoader(dataset_config)
    engine = ArkEngine(config=engine_config, data_loader=data_loader)
    pipeline = create_pipeline(algorithms, engine)

    model = load_model(model_config)
    return pipeline.run(model)


def main():
    args = parse_args()
    out_dir = os.path.expanduser(args.output)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    init_logger(level=args.log_level, file_name=os.path.join(out_dir, 'log.txt'))
    compressed_model = optimize_model(args)
    save_model(compressed_model, out_dir)


if __name__ == '__main__':
    main()
