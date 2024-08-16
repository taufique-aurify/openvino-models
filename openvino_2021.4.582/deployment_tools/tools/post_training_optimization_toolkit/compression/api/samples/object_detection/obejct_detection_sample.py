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

from compression.engines.ie_engine import IEEngine
from compression.graph import load_model, save_model
from compression.graph.model_utils import compress_model_weights
from compression.pipeline.initializer import create_pipeline
from compression.utils.logger import init_logger
from compression.api.samples.utils.argument_parser import get_common_argparser
from compression.api.samples.object_detection.metric import MAP
from compression.api.samples.object_detection.data_loader import COCOLoader

init_logger(level='INFO')


def main():
    parser = get_common_argparser()
    parser.add_argument(
        '--annotation-path',
        help='Path to the directory with annotation file',
        required=True
    )
    args = parser.parse_args()
    if not args.weights:
        args.weights = '{}.bin'.format(os.path.splitext(args.model)[0])

    model_config = Dict({
        'model_name': 'ssd_mobilenet_v1_fpn',
        'model': os.path.expanduser(args.model),
        'weights': os.path.expanduser(args.weights)
    })

    engine_config = Dict({
        'device': 'CPU'
    })

    dataset_config = Dict({
        'images_path': os.path.expanduser(args.dataset),
        'annotation_path': os.path.expanduser(args.annotation_path),
    })
    algorithms = [
        {
            'name': 'AccuracyAwareQuantization',
            'params': {
                'target_device': 'CPU',
                'preset': 'mixed',
                'stat_subset_size': 300,
                'maximal_drop': 0.004
            }
        }
    ]

    # Step 1: Load the model.
    model = load_model(model_config)

    # Step 2: Initialize the data loader.
    data_loader = COCOLoader(dataset_config)
    # Step 3 (Optional. Required for AccuracyAwareQuantization): Initialize the metric.
    metric = MAP(91, data_loader.labels)

    # Step 4: Initialize the engine for metric calculation and statistics collection.
    engine = IEEngine(config=engine_config,
                      data_loader=data_loader,
                      metric=metric)

    # Step 5: Create a pipeline of compression algorithms.
    pipeline = create_pipeline(algorithms, engine)

    # Step 6: Execute the pipeline.
    compressed_model = pipeline.run(model)

    # Step 7 (Optional): Compress model weights to quantized precision
    #                    in order to reduce the size of final .bin file.
    compress_model_weights(compressed_model)

    # Step 8: Save the compressed model to the desired path.
    save_model(compressed_model, os.path.join(os.path.curdir, 'optimized'))

    # Step 9 (Optional): Evaluate the compressed model. Print the results.
    metric_results = pipeline.evaluate(compressed_model)
    if metric_results:
        for name, value in metric_results.items():
            print('{: <27s}: {}'.format(name, value))


if __name__ == '__main__':
    main()
