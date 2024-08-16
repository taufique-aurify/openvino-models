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
from copy import deepcopy
import numpy as np

from ...algorithm_selector import COMPRESSION_ALGORITHMS
from ....algorithms.algorithm import Algorithm
from ....graph import model_utils as mu, node_utils as nu
from ....graph.special_operations import OPERATIONS_WITH_WEIGHTS
from ....samplers.creator import create_sampler
from ....statistics.functions import activations as acf
from ....utils.logger import get_logger

logger = get_logger(__name__)


@COMPRESSION_ALGORITHMS.register('OverflowCorrection')
class OverflowCorrection(Algorithm):
    name = 'OverflowCorrection'

    def __init__(self, config, engine):
        super().__init__(config, engine)
        self._conv_node_names = []
        stat_subset_size = min(
            self._config.get(
                'stat_subset_size', len(self._engine.data_loader)),
            len(self._engine.data_loader))
        self.total_exec_steps = stat_subset_size
        shuffle_data = self._config.get('shuffle_data', False)
        seed = self._config.get('seed', 0)
        self._sampler = create_sampler(engine, stat_subset_size, shuffle_data, seed)

    def run(self, model):
        """ this function applies the overflow correction algorithm
         :param model: model to apply algo
         :return model with corrected scales & weights to prevent overflow for INT ranges
         """
        activation_statistics = self._stats_collector.get_statistics_for_algorithm(self.name)

        weighted_nodes = mu.get_nodes_by_type(model, [n['type'] for n in OPERATIONS_WITH_WEIGHTS])
        weighted_nodes = [n for n in weighted_nodes if nu.node_with_quantized_weights(n)]
        for weighted_node in weighted_nodes:
            bias_node = nu.get_bias_for_node(weighted_node)
            if bias_node is None:
                continue
            add_node = nu.get_node_output(bias_node, 0)[0]
            add_node_name = add_node.name
            if add_node_name not in activation_statistics \
                    or 'max_per_tensor' not in activation_statistics[add_node_name]:
                logger.debug('Skipping {}'.format(weighted_node.name))
                continue
            logger.debug('Processing {}'.format(weighted_node.name))
            weight_fq = nu.get_node_input(weighted_node, 1)
            if weight_fq.levels <= np.iinfo(np.uint8).max:
                logger.debug('Skipping {} due to INT8 weights quantization'.format(weighted_node.name))
                continue
            weights_node = nu.get_node_input(weight_fq, 0)
            weights = deepcopy(nu.get_node_value(weights_node))
            weights_dtype = weights.dtype
            w_output_low = nu.get_node_input(weight_fq, 3)
            w_output_high = nu.get_node_input(weight_fq, 4)
            w_output_low_value = deepcopy(nu.get_node_value(w_output_low))
            w_output_high_value = deepcopy(nu.get_node_value(w_output_high))
            weight_scale = self.compute_scale(weight_fq)

            # Get input FQ node and compute input scale (in_scale)
            input_fqs = self._get_propagated_input_fq(weighted_node)
            input_scales = []
            for input_fq in input_fqs:
                input_scales.append(self.compute_scale(input_fq))
            input_scale = np.max(input_scales)

            # Get maximum values
            after_add_output = np.max(activation_statistics[add_node_name]['max_per_tensor'])
            max_quantized_output = int(after_add_output / (input_scale * weight_scale))
            int32_type_max = np.iinfo(np.int32).max

            if max_quantized_output > int32_type_max:
                rescale_value = max_quantized_output / int32_type_max
                weights = weights / rescale_value

                w_output_low_value = w_output_low_value * rescale_value
                w_output_high_value = w_output_high_value * rescale_value
                logger.debug('Weights and scales for node {} '
                             'updated with scale coefficient: {}'.format(weighted_node.name, rescale_value))
            nu.set_node_value(weights_node, np.array(weights, dtype=weights_dtype))
            nu.set_node_value(w_output_low, w_output_low_value)
            nu.set_node_value(w_output_high, w_output_high_value)
        return model

    def _get_propagated_input_fq(self, node):
        def walk_to_parents(node):
            node_parents = self.get_node_parents(node)
            if node.type == 'FakeQuantize' and nu.get_node_input(node, 0).type != 'Const':
                input_fqs.append(node)
                return
            for node_parent in node_parents:
                walk_to_parents(node_parent)

        input_fqs = []
        for input_node in self.get_node_parents(node):
            walk_to_parents(input_node)
        return input_fqs

    def register_statistics(self, model, stats_collector):
        self._stats_collector = stats_collector
        conv_nodes = mu.get_nodes_by_type(model, [n['type'] for n in OPERATIONS_WITH_WEIGHTS])
        stats_layout = {}
        for conv_node in conv_nodes:
            bias_node = nu.get_bias_for_node(conv_node)
            if bias_node is None:
                continue
            add_node = nu.get_node_output(bias_node, 0)[0]
            stats_layout[add_node.name] = {'max_per_tensor': acf.abs_max_per_tensor}
        stats_collector.register(self.name, stats_layout, self._sampler)

    @property
    def change_original_model(self):
        return True

    @staticmethod
    def get_node_parents(node):
        return [n for n in nu.get_node_inputs(node) if n is not None and n.type != 'Const']

    @staticmethod
    def compute_scale(fq):
        output_low = nu.get_node_input(fq, 3)
        output_high = nu.get_node_input(fq, 4)
        output_low_value = nu.get_node_value(output_low)
        output_high_value = nu.get_node_value(output_high)
        return np.max((output_high_value - output_low_value) / (fq.levels - 1))
