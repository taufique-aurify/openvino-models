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

from collections import OrderedDict
from copy import deepcopy

import numpy as np

from ..utils import load_hardware_config
from ...algorithm import Algorithm
from ...algorithm_selector import COMPRESSION_ALGORITHMS
from ....algorithms.quantization.fake_quantize import insert_fake_quantize_nodes
from ....graph import editor as ge
from ....graph import node_utils as nu
from ....graph import model_utils as mu
from ....graph.special_operations import OPERATIONS_WITH_BIAS, SPLIT_OPERATIONS, OPERATIONS_CHANNEL_AXIS
from ....graph.transformer import GraphTransformer
from ....samplers.creator import create_sampler
from ....statistics.functions import activations as asf
from ....statistics.functions import aggregation as agf
from ....statistics.statistics import TensorStatisticAxis
from ....utils.launcher import IELauncher
from ....utils.logger import get_logger

logger = get_logger(__name__)


@COMPRESSION_ALGORITHMS.register('BiasCorrection')
class BiasCorrection(Algorithm):
    algo_type = 'bias_correction'
    name = 'BiasCorrection'

    @property
    def change_original_model(self):
        return True

    def __init__(self, config, engine):
        super().__init__(config, engine)
        self._stat_subset_size = min(
            self._config.get('stat_subset_size', len(self._engine.data_loader)),
            len(self._engine.data_loader)
        )
        self._batch_stat_size = max(np.int(self._stat_subset_size * 0.2), 1)
        self._graph_transformer = GraphTransformer(load_hardware_config(self._config))
        self._shuffle_data = self._config.get('shuffle_data', False)
        self._seed = self._config.get('seed', 0)
        self._sampler = create_sampler(engine, self._batch_stat_size, self._shuffle_data, self._seed)
        self._types_with_bias = [op['type'] for op in OPERATIONS_WITH_BIAS]
        self._split_types = [op['type'] for op in SPLIT_OPERATIONS]
        self._nodes_with_bias_names = []
        self._fp32_statistics = []
        self._launcher = None
        self._collected_stat_inputs = []
        self._subgraphs_data = OrderedDict()
        self._channel_axis = {}
        self._threshold = float(self._config.get('threshold', 1000.0))
        self._apply_for_all_nodes = self._config.get('apply_for_all_nodes', False)
        self.total_exec_steps = self._stat_subset_size

    def run(self, model):
        '''
        This function applies the bias correction algorithm.
        :param model: model to apply algorithm
        :return: model with corrected biases for layers with bias
        '''
        self._fp32_statistics = self._stats_collector.get_statistics_for_algorithm(self.name)
        self._launcher = IELauncher()

        stat_inputs = deepcopy(self._collected_stat_inputs)

        self._subgraphs_data = self._fill_subgraphs_data(model)

        for node_name in self._subgraphs_data:
            node = mu.get_node_by_name(model, node_name)
            model_copy = deepcopy(model)
            node_copy = mu.get_node_by_name(model_copy, node_name)
            node_copy_bias_add = self._get_add_node_for_bias(node_copy)

            self._remove_fq_from_inputs(model_copy)

            model_copy, params = self._prepare_model_and_params(model_copy, node_copy, node_copy_bias_add)

            bias_shift_value = self._compute_bias_shift(model_copy, **params)
            logger.update_progress(self._batch_stat_size)

            bias = nu.get_bias_for_node(node)
            bias_copy = nu.get_node_input(node_copy_bias_add, 1)
            current_bias_value = nu.get_node_value(bias)

            bias_is_updated = False
            bias_magnitude = np.inf
            if np.count_nonzero(current_bias_value == 0) == 0:
                bias_magnitude = np.max(np.abs(bias_shift_value / current_bias_value))
            if current_bias_value.shape != bias_shift_value.shape:
                logger.debug('{} skipped because shift shape and original shape are inconsistent'.format(node_name))
            elif bias_magnitude < self._threshold:
                logger.debug('Setting bias for {}. Magnitude: {}'.format(node_name, bias_magnitude))
                node['original_bias'] = current_bias_value
                new_bias_value = current_bias_value + bias_shift_value
                nu.set_node_value(bias, new_bias_value)
                nu.set_node_value(bias_copy, new_bias_value)
                bias_is_updated = True
            else:
                logger.debug('Magnitude for {}: {}. Skipping'.format(node_name, bias_magnitude))

            self._collect_new_stats(model_copy, bias_is_updated, **params)
            self._remove_unnecessary_stats(model, node_name)
        self._collected_stat_inputs = stat_inputs
        return model

    def _fill_subgraphs_data(self, model):

        def skip_node(node):
            if not nu.node_with_quantized_weights(node) and not self._apply_for_all_nodes:
                logger.debug('{} skipped because it does not have FQ weights.'.format(node.name))
                return True

            if not nu.check_const_input(node):
                logger.debug('{} skipped because channel axis is not defiened'.format(node.name))
                return True

            bias_node = nu.get_bias_for_node(node)
            if bias_node is None:
                logger.debug('{} skipped because its bias is empty.'.format(node.name))
                return True

            return False

        model_copy = deepcopy(model)
        subgraphs_data = OrderedDict()
        self._remove_fq_from_inputs(model_copy)
        for node_name in self._nodes_with_bias_names:
            node = mu.get_node_by_name(model_copy, node_name)
            if skip_node(node):
                continue
            first_nodes, last_nodes = self._get_subgraph_data_for_node(node)
            subgraphs_data[node_name] = {
                'first_nodes': [n.name for n in first_nodes],
                'last_nodes': [n.name for n in last_nodes]
            }
        del model_copy
        return subgraphs_data

    def _remove_fq_from_inputs(self, model):
        fq_nodes = mu.get_nodes_by_type(model, ['FakeQuantize'])
        fq_names_to_cut = []
        for fq_node in fq_nodes:
            if nu.get_node_input(fq_node, 0).type != 'Const':
                fq_names_to_cut.append(fq_node.name)
        self._graph_transformer.remove_fq_nodes(model, fq_names_to_cut, True)

    def _get_subgraph_data_for_node(self, main_node):
        output_nodes = []
        checked_output_names = []
        input_nodes = []
        checked_input_names = []

        def fill_output_nodes():
            main_node_children = self.get_node_children(main_node)
            for main_node_child in main_node_children:
                walk_to_children(main_node_child)

        def fill_input_nodes():
            last_nodes_list = output_nodes if output_nodes else [main_node]
            for last_node in last_nodes_list:
                last_node_parents = self.get_node_parents(last_node)
                for last_node_parent in last_node_parents:
                    walk_to_parents(last_node_parent)

        def walk_to_children(node, is_this_branch_node=False):
            node_parents = self.get_node_parents(node)
            node_input_0 = nu.get_node_input(node, 0)
            if is_this_branch_node:
                # Jump over Split nodes
                if node_input_0.type in self._split_types:
                    node_input_0 = nu.get_node_input(node_input_0, 0)
            if node.type in self._types_with_bias \
                    and (nu.node_with_quantized_weights(node) and not self._apply_for_all_nodes):
                if node_input_0.name not in checked_output_names:
                    checked_output_names.append(node_input_0.name)
                    checked_input_names.append(node_input_0.name)
                    output_nodes.append(node_input_0)
                    self._collected_stat_inputs.append(node_input_0.name)
            elif is_this_branch_node and len(node_parents) > 1:
                return
            else:
                node_children = self.get_node_children(node)
                is_branching = len(node_children) > 1
                for node_child in node_children:
                    walk_to_children(node_child, is_branching)

        def walk_to_parents(node):
            node_parents = self.get_node_parents(node)
            if node.name in checked_input_names:
                return
            checked_input_names.append(node.name)
            if node.name in self._collected_stat_inputs:
                if node not in input_nodes:
                    input_nodes.append(node)
            else:
                for node_parent in node_parents:
                    walk_to_parents(node_parent)

        fill_output_nodes()
        fill_input_nodes()

        return input_nodes, output_nodes

    def _prepare_model_and_params(self, model, node, node_bias_add):
        params = {'node_bias_add': node_bias_add}

        if model.is_cascade:
            model.clean_up()
        else:
            first_nodes = [mu.get_node_by_name(model, name) for name in
                           self._subgraphs_data[node.name]['first_nodes']]
            last_nodes = [mu.get_node_by_name(model, name) for name in
                          self._subgraphs_data[node.name]['last_nodes']]

            self._remove_default_results(node.graph)
            if node_bias_add not in last_nodes:
                last_nodes.append(node_bias_add)

            params['parameters_data_dict'] = self._create_parameters_for_first_nodes(first_nodes)
            params['results_data_dict'] = self._create_results_for_last_nodes(last_nodes)

            model.clean_up()

            self._update_split_subgraphs(model)
            params['feed_dicts'] = self._create_feed_dicts(params['parameters_data_dict'])
        return model, params

    def _remove_default_results(self, graph):
        graph_outputs = ge.get_nodes_by_type(graph, ['Result'])
        for graph_output in graph_outputs:
            graph.remove_node(graph_output.id)

    def _create_parameters_for_first_nodes(self, input_nodes):
        outputs_shapes = {n.name: nu.get_output_shape(n, 0).copy() for n in input_nodes}
        inputs_data = []
        for input_node in input_nodes:
            c_input_shape = outputs_shapes[input_node.name]
            c_input_shape[0] = 1
            parameter_name = input_node.name + '/parameter'
            param_node = ge.create_node(input_node.graph, parameter_name, 'Parameter',
                                        {'shape': c_input_shape})
            for _, port in input_node.out_ports().items():
                for in_port in port.get_destinations():
                    in_port.disconnect()
                    in_port.connect(param_node.out_port(0))

            inputs_data.append({
                'param_name': param_node.name,
                'param_shape': tuple(c_input_shape),
                'input_name': input_node.name
            })

        return inputs_data

    def _create_results_for_last_nodes(self, output_nodes):
        outputs_data = []
        for output_node in output_nodes:
            output_name = output_node.name
            result_name = output_name + '/result'
            result_node = ge.create_node(output_node.graph, result_name, 'Result', {})
            result_node.in_port(0).connect(output_node.out_port(0))
            if output_name in self._fp32_statistics:
                self._fp32_statistics[output_name]['batch_mean_in'] = []
            else:
                self._fp32_statistics[output_name] = {'batch_mean_in': []}

            outputs_data.append({
                'result_name': result_name,
                'output_name': output_name
            })
        return outputs_data

    def _update_split_subgraphs(self, model_copy):
        for node_split in mu.get_nodes_by_type(model_copy, self._split_types):
            for port_id in node_split.out_ports():
                split_result_name = '{}/result/{}'.format(node_split.name, port_id)
                split_result = ge.create_node(node_split.graph, split_result_name, 'Result', {})
                split_result.in_port(0).connect(node_split.out_port(port_id))

    def _create_feed_dicts(self, params_data):
        feed_dicts = []
        for stat_id in range(self._batch_stat_size):
            feed_dict = {}
            for param_data in params_data:
                if 'batch_mean_param_in' in self._fp32_statistics[param_data['input_name']]:
                    stats_by_param = self._fp32_statistics[param_data['input_name']]['batch_mean_param_in'][stat_id]
                else:
                    stats_by_param = self._fp32_statistics[param_data['input_name']]['batch_mean_in'][stat_id]
                feed_dict[param_data['param_name']] = np.mean(stats_by_param, axis=0, keepdims=True)
            feed_dicts.append(feed_dict)
        return feed_dicts

    def _reshape_model_by_feed_dict(self, feed_dict, model_copy):
        current_inputs = self._launcher.model.input_info
        current_shapes = {input_name: tuple(current_inputs[input_name].input_data.shape) for input_name in
                          current_inputs}
        feed_shapes = {input_name: tuple(feed_dict[input_name].shape) for input_name in feed_dict}
        if feed_shapes != current_shapes:
            self._launcher.set_model(model_copy, md_shapes=feed_shapes)

    def _compute_bias_shift(self, model_copy, **params):
        add_name = params['node_bias_add'].name
        fp32_output = agf.mean(self._fp32_statistics[add_name]['mean_per_channel'])

        if model_copy.is_cascade:
            ref_stats_layout = {add_name: {'mean_per_channel': TensorStatisticAxis(asf.mean_per_channel_axis,
                                                                                   channel=self._channel_axis)}}
            self._engine.set_model(model_copy)
            _, q_outputs = self._engine.predict(ref_stats_layout, self._sampler)
            q_output = agf.mean(q_outputs[add_name]['mean_per_channel'])
        else:
            self._launcher.set_model(model_copy)
            q_outputs = []
            for feed_dict in params['feed_dicts']:
                self._reshape_model_by_feed_dict(feed_dict, model_copy)
                q_output = self._launcher.infer(feed_dict)
                q_outputs.append(asf.mean_per_channel_axis(q_output[add_name], add_name, channel=self._channel_axis))
            q_output = agf.mean(q_outputs)

        add_out_shape = nu.get_input_shape_for_bias(params['node_bias_add'])
        axis_channel = self.get_channel_axis(add_name)
        bias_shift_value = fp32_output - q_output
        bias_shape = np.ones(len(add_out_shape), dtype=np.int)
        bias_shape[axis_channel] = add_out_shape[axis_channel]

        bias_shift_value = bias_shift_value.reshape(bias_shape)
        return bias_shift_value

    def _collect_new_stats(self, model_copy, bias_is_updated, **params):
        if not model_copy.is_cascade and params['results_data_dict']:
            if not bias_is_updated:
                fq_nodes = mu.get_nodes_by_type(model_copy, ['FakeQuantize'])
                self._graph_transformer.remove_fq_nodes(model_copy, fq_nodes)
            self._launcher.set_model(model_copy)
            for feed_dict in params['feed_dicts']:
                self._reshape_model_by_feed_dict(feed_dict, model_copy)
                q_output = self._launcher.infer(feed_dict)
                for result_data_dict in params['results_data_dict']:
                    q_stat_updated = q_output[result_data_dict['output_name']]
                    self._fp32_statistics[result_data_dict['output_name']]['batch_mean_in'].append(q_stat_updated)

    def _remove_unnecessary_stats(self, model, node_name):
        if model.is_cascade:
            return
        needed_stats_list = self._get_current_stats_list(model, node_name)
        node_inputs_name = self._subgraphs_data[node_name]['first_nodes']
        for node_input_name in node_inputs_name:
            if node_input_name not in needed_stats_list and 'batch_mean_in' in self._fp32_statistics[node_input_name]:
                logger.debug('Dropped {}'.format(node_input_name))
                self._fp32_statistics[node_input_name]['batch_mean_in'] = []

    def _get_current_stats_list(self, graph, current_node_name):
        stat_nodes_list = []
        trigger = False
        for node_name in self._subgraphs_data:
            if node_name == current_node_name:
                trigger = True
                continue
            if trigger:
                for stat_node_name in self._subgraphs_data[node_name]['first_nodes']:
                    input_node = mu.get_node_by_name(graph, stat_node_name)
                    stat_nodes_list.append(input_node.name)
        return stat_nodes_list

    def register_statistics(self, model, stats_collector):
        self._stats_collector = stats_collector
        statistics_layout = {}
        if model.is_cascade:
            self._sampler = create_sampler(self._engine, self._stat_subset_size, self._shuffle_data, self._seed)

        topological_biased_ops = self._get_topological_biased_ops(model)
        self._nodes_with_bias_names = [node.name for node in topological_biased_ops]
        parameter_nodes = mu.get_nodes_by_type(model, ['Parameter'])
        biased_after_param_nodes = self._get_biased_after_params(parameter_nodes)
        for node in topological_biased_ops:
            add_node = self._get_add_node_for_bias(node)
            axis = OPERATIONS_CHANNEL_AXIS[node.type]
            self._channel_axis[add_node.name] = axis
            if node.name in biased_after_param_nodes:
                input_name = biased_after_param_nodes[node.name]
                statistics_layout[input_name] = {'batch_mean_param_in': agf.batch_mean}
                self._collected_stat_inputs.append(input_name)
            statistics_layout[add_node.name] = {'mean_per_channel': TensorStatisticAxis(asf.mean_per_channel_axis,
                                                                                        channel=self._channel_axis)}

        self._stats_collector.register(self.name, statistics_layout, self._sampler)

    def compute_total_exec_steps(self, model=None):
        total_steps = 0
        nodes_length = len(self._get_topological_biased_ops(model))
        total_steps += self._stat_subset_size
        total_steps += nodes_length * self._batch_stat_size
        self.total_exec_steps = total_steps

    def _get_topological_biased_ops(self, model):
        quantized_model = deepcopy(model)
        insert_fake_quantize_nodes(self._config, quantized_model)
        biased_ops_list = []
        ops_list = [op for op in quantized_model.pseudo_topological_sort() if op.kind == 'op']
        for op in ops_list:
            if op.type in self._types_with_bias and \
                    nu.get_bias_for_node(op) is not None and \
                    nu.get_input_shape(op, 0)[0] == 1 and \
                    nu.node_with_quantized_weights(op):
                biased_ops_list.append(op)
        return biased_ops_list

    def _get_biased_after_params(self, parameter_nodes):
        biased_after_param_nodes = {}

        def walk_to_children(node, parameter_name):
            node_children = self.get_node_children(node)
            if node.type in self._types_with_bias:
                node_input = nu.get_node_input(node, 0)
                biased_after_param_nodes[node.name] = node_input.name
                return
            for node_child in node_children:
                walk_to_children(node_child, parameter_name)

        for param_node in parameter_nodes:
            walk_to_children(param_node, param_node.name)

        return biased_after_param_nodes

    def get_channel_axis(self, node):
        if isinstance(node, tuple):
            return self._channel_axis[node[0]]
        return self._channel_axis[node]

    @staticmethod
    def _get_add_node_for_bias(node):
        bias = nu.get_bias_for_node(node)
        return nu.get_node_output(bias, 0)[0]

    @staticmethod
    def get_node_parents(node):
        return [n for n in nu.get_node_inputs(node) if n is not None and n.type != 'Const']

    @staticmethod
    def get_node_children(node):
        return [n for n in nu.get_all_node_outputs(node) if n is not None and nu.get_input_data_value(n, 0) is None]
