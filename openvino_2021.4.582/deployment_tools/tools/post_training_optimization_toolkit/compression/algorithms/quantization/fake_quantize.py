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

from copy import copy, deepcopy

import numpy as np
from addict import Dict

from .fake_quantize_configuration import read_all_fake_quantize_configurations, get_configurations_by_preset, \
    get_configurations_by_qscheme, find_fqs_to_unify, add_range_estimator_configs
from .utils import load_hardware_config, merge_nested_dicts, get_ignored_operations
from ...graph.model_utils import get_nodes_by_type, get_node_by_name
from ...graph.node_utils import get_node_input, set_node_value, \
    get_node_value, get_node_output, get_node_inputs, get_input_shape, \
    get_quantized_input_key, get_input_data_value, get_first_convolutions
from ...graph.special_operations import OPERATIONS_WITH_WEIGHTS, TRANSPOSED_OPERATIONS
from ...graph.transformer import GraphTransformer
from ...utils.logger import get_logger

logger = get_logger(__name__)


def tune_range(a, b, num_bits):
    """ Tunes asymmetric quantization range to set zero quant precisely to zero value.
    Function moves left or right borders to do this and doesn't make left border higher or
    right border lesser than its original values
    :param a: range left border
    :param b: range right border
    :param num_bits: number of bits to perform quantization
    :return tuple with recomputed ranges
    """
    level_high = 2 ** num_bits - 1
    s = level_high / (b - a)
    fval = -a * s
    qval = np.round(fval)

    with np.errstate(invalid='ignore', divide='ignore'):
        ra = np.where(qval < level_high, qval / (qval - level_high) * b, a)
        rb = np.where(qval > 0.0, (qval - level_high) / qval * a, b)

    range_a = b - ra
    range_b = rb - a

    mask = np.where(range_a > range_b, 1.0, 0.0)
    inv_mask = np.abs(1.0 - mask)

    ra = mask * ra + inv_mask * a
    rb = inv_mask * rb + mask * b

    return ra, rb


def fill_fake_quantize_node(fq, min_level, max_level, output_low=None, output_high=None):
    """ Fills fake quantize input nodes with min/max values
    :param fq: fake quantize node to fill
    :param min_level: low border of quantization range
    :param max_level: high border of quantization range
    """
    if output_low is None:
        output_low = min_level
    if output_high is None:
        output_high = max_level

    def _update_node_val(port_idx, value):
        _node = get_node_input(fq, port_idx)
        set_node_value(_node, value)

    _update_node_val(1, min_level)
    _update_node_val(2, max_level)
    _update_node_val(3, output_low)
    _update_node_val(4, output_high)


def compute_stats_layouts(config, model, qscheme=None):
    """
    Compute stats layouts and hardware configuration
    :param config: dictionary with params algo section from toolkit config
    :param model: NXModel instance
    :return: configuration dictionary
    """
    hardware_config = load_hardware_config(config)
    fq_configuration = \
        read_all_fake_quantize_configurations(config, hardware_config, model)
    if not config.preset:
        config.preset = 'performance'
    if not qscheme:
        fq_configuration = get_configurations_by_preset(config, model, fq_configuration)
        fq_configuration = add_range_estimator_configs(fq_configuration, config)
    else:
        fq_configuration = get_configurations_by_qscheme(fq_configuration, qscheme)

    # get all fake quantize nodes
    fq_nodes = get_nodes_by_type(model, ['FakeQuantize'])

    def _get_value(key, default=None):
        return fq_config[key] if key in fq_config else default

    def _compute_levels():
        def_levels = 2 ** _get_value('bits', 8)

        if is_weights and fq_config['mode'] == 'symmetric':
            level_low = _get_value('level_low', -def_levels / 2 + 1)
        else:
            level_low = _get_value('level_low', -def_levels / 2)
        level_high = _get_value('level_high', def_levels / 2 - 1)
        return int(abs(level_high) + abs(level_low) + 1)

    fake_quantize_config = {}
    for fq in fq_nodes:
        node_input = get_node_input(fq, 0)
        is_weights = node_input.type == 'Const'
        if is_weights:
            fq_config = copy(fq_configuration[fq.name]['weights'])
        else:
            fq_config = copy(fq_configuration[fq.name]['activations'])
        fake_quantize_config[fq.name] = fq_config
        if fq.name in config.layerwise_configs[0]:
            fq_config = Dict(merge_nested_dicts(fq_config, config.layerwise_configs[0][fq.name]))

        fq_config['signed'] = False
        if 'level_low' in fq_config and 'level_high' in fq_config and fq_config['level_low'] < 0:
            fq_config['signed'] = True

        fake_quantize_config[fq.name] = fq_config
        fq.levels = _compute_levels()

    return fake_quantize_config


def insert_fake_quantize_nodes(config, model, qscheme=None):
    """ Inserts fake quantize nodes, fill them according config
    :param config: dictionary with params algo section from toolkit config
    :param model: NXModel instance
    :param qscheme: The quantization scheme generated from the space
    :return None
    """
    hardware_config = load_hardware_config(config)
    ignored_params = {
        'skip_model': False,
        'scope': [],
        'operations': []
    }
    if config['ignored']:
        ignored_params.update(deepcopy(config['ignored']))

    if config['model_type']:
        ignored_params['operations'] += get_ignored_operations(config['model_type'])

    if qscheme:
        for key in qscheme:
            if qscheme[key]['quantize'] == 0 and key not in ignored_params['scope']:
                ignored_params['scope'].append(key)

    GraphTransformer(hardware_config).insert_fake_quantize(model, ignored_params)


def get_fake_quantize_input(fake_quantize):
    """ Returns input into fake quantize node
    :param fake_quantize: fake quantize node
    :return Input node of fake quantize node
    """
    parent = get_node_input(fake_quantize, 0)
    if parent.attrs()['op'] == 'Cast':
        parent = get_node_input(parent, 0)
    return parent


def get_fake_quantize_input_value(fake_quantize):
    """ Returns input into fake quantize node
    :param fake_quantize: fake quantize node
    :return Input node of fake quantize node
    """
    input_node = fake_quantize
    if input_node.attrs()['op'] == 'Cast':
        input_node = get_node_input(input_node, 0)
    return get_input_data_value(input_node, 0)


def get_fake_quantize_first_output(fake_quantize):
    """ Returns first output of the fake quantize node (usually used for weights)
    :param fake_quantize: fake quantize node
    :return metadata of the node which is first output of the fake quantize node
    """
    return get_node_output(fake_quantize, 0)[0]


def fix_zero_filters_symmetric(max_level, eps=0.01):
    max_range = np.max(max_level)
    lower_threshold = np.maximum(1e-5, eps * max_range)
    return np.maximum(lower_threshold, max_level)


def fix_zero_filters_asymmetric(max_level, min_level, eps=1e-8):
    ranges = max_level - min_level
    ranges = ranges if isinstance(ranges, np.ndarray) else np.array([ranges])
    min_correction = 8 * 10e-5
    corrections = [(np.maximum(eps * rng, rng) - rng) * 0.5 if rng > min_correction
                   else min_correction for rng in ranges]
    max_level = max_level + corrections
    min_level = min_level - corrections
    return max_level, min_level


def symmetric_range(node, fq, weights_stats,
                    batch_inputs_stats, fake_quantize_config):
    name = get_quantized_input_key(fq)
    if node.type == 'Const' or get_input_data_value(fq, 0) is not None:
        node_output = get_fake_quantize_first_output(fq)
        max_level = weights_stats[node_output.name]['max']
        max_level = fix_zero_filters_symmetric(max_level)
        min_level = -max_level
    elif name in batch_inputs_stats:
        max_level = batch_inputs_stats[name]['max']
        min_level = batch_inputs_stats[name]['min']
        max_level = fix_zero_filters_symmetric(max_level)
        signed = fake_quantize_config[fq.name]['signed']
        min_level = np.zeros(max_level.shape) if np.all(min_level >= 0) and not signed else \
            -max_level * fq.levels / (fq.levels - 2)
    else:
        raise Exception(
            'WARNING: Fake quantize node {} is missed'.format(fq.name))
    min_level, max_level = broadcast_fq_values(fq, node, min_level, max_level, fake_quantize_config)
    return min_level, max_level


def asymmetric_range(node, fq, weights_stats,
                     batch_inputs_stats, fake_quantize_config):
    name = get_quantized_input_key(fq)
    if node.type == 'Const' or get_input_data_value(fq, 0) is not None:
        node_output = get_fake_quantize_first_output(fq)
        max_level = weights_stats[node_output.name]['max']
        min_level = weights_stats[node_output.name]['min']
    elif name in batch_inputs_stats:
        max_level = batch_inputs_stats[name]['max']
        min_level = batch_inputs_stats[name]['min']
    else:
        raise Exception(
            'WARNING: Fake quantize node {} is missed'.format(fq.name))

    max_level, min_level = fix_zero_filters_asymmetric(max_level, min_level)
    min_level = np.where(min_level < 0.0, min_level, 0.0)
    max_level = np.where(max_level > 0.0, max_level, 0.0)
    min_level, max_level = tune_range(
        min_level, max_level, fake_quantize_config[fq.name]['bits'])
    min_level, max_level = broadcast_fq_values(fq, node, min_level, max_level, fake_quantize_config)
    return min_level, max_level


def get_quantized_model(model, create_stats_collector, activations_statistics,
                        fill_fq_range, config, qscheme=None):
    """
    Returns a calibrated low precision model via four steps:
    1. Quantize the model
    2. Calculate quantization config for FQ nodes
    3. Collect the weight stats based on config
    4. Calibrate [min, max] for inserted fq nodes
    :param model: original model (NXModel instance)
    :param create_stats_collector: functor to create function for stats collector callback
    :param activations_statistics: precomputed statistics for activations layers
    :param fill_fq_range: functor to generate min and max range for fake quantize node
    :param config: dictionary with params algo section from toolkit config
     """
    # FakeQuantize nodes insertion
    insert_fake_quantize_nodes(config, model, qscheme=qscheme)

    fake_quantize_config = compute_stats_layouts(config, model, qscheme=qscheme)

    # generate a list of fq nodes that require rescaling (first convolutions weight FQs)
    fake_quantize_config.update(set_rescaling_factors(config['target_device'], model))

    weights_stats_layout = create_stats_collector(fake_quantize_config, model, for_weights=True)

    # compute weights statistics
    weights_stats = compute_weights_stats(model, weights_stats_layout)

    # calculate and fill min and max range for fq nodes
    fill_fq_range(model, weights_stats, activations_statistics, fake_quantize_config, config)
    return model


def compute_weights_stats(model, stats_layout):
    """ Computes weights statistic from provided statistics layout
    :param model: NXModel instance
    :param stats_layout: dictionary with layer names as keys and
     functions list with rules how to compute statistics as values
    :return dictionary with layers names as keys and list of evaluated statistics as values"""
    # compute weights statistics
    weights_stats = {}
    for fq_name, stats in stats_layout.items():
        fq_node = get_node_by_name(model, fq_name)
        if fq_node.type != 'FakeQuantize':
            raise Exception('FakeQuantize node for weights is missed')
        node = get_fake_quantize_first_output(fq_node)
        weights_node = get_node_input(fq_node, 0)
        weights_value = get_input_data_value(fq_node, 0)
        if weights_node.type != 'Const' and weights_value is None:
            raise Exception('Incorrect stats layout for weights:'
                            ' {} is activation'.format(weights_node.name))
        if node.name not in weights_stats:
            weights_stats[node.name] = {}
        for stat_name, stat_fn in stats.items():
            weights = weights_value.astype(np.float32)
            weights_stats[node.name][stat_name] = stat_fn(weights)
    return weights_stats


def broadcast_fq_values(fq, node, min_level, max_level, fq_config):
    """ Reshapes weights and activations in perchannel mode for next fusing
    :param fq: current Fake Quantize node
    :param node: input node for Fake Quantize
    :param min_level:
    :param max_level:
    :param fq_config: for checking special Fake Quantize
    :return tuple of reshaped min and max values"""

    min_level = np.array(min_level)
    max_level = np.array(max_level)

    if not min_level.shape and not max_level.shape:
        return min_level, max_level

    # get input shape from data node
    input_shape = get_input_shape(fq, 0)
    bounds_shape = np.ones(len(input_shape), dtype=np.int32)

    if node.type == 'Const':
        output_node = get_fake_quantize_first_output(fq)
        if output_node.type in [op['type'] for op in TRANSPOSED_OPERATIONS]:
            bounds_shape[1] = input_shape[1]
        else:
            bounds_shape[0] = input_shape[0]
    else:
        if fq_config[fq.name]['granularity'] == 'perchannel':
            bounds_shape[1] = input_shape[1]

    min_level = min_level.reshape(bounds_shape)
    max_level = max_level.reshape(bounds_shape)

    return min_level, max_level


def set_rescaling_factors(target_device, model, scaling_factor=2.0):
    """
        Generate a list of weight FQ nodes for input convolutions
        for further rescaling of weights/FQs.
        Skip if target device is not CPU.
        :param target_device: target device name
        :param model: NXModel instance
        :param scaling_factor: rescaling factor for first convolution nodes
    """
    fqs_to_rescale = []

    if target_device not in ['CPU', 'ANY'] or not get_nodes_by_type(model, ['Convolution', ]):
        return {'scaling_factor': 1.0,
                'fqs_to_rescale': fqs_to_rescale}

    input_nodes = get_nodes_by_type(model, ['Parameter'])

    input_convolutions = get_first_convolutions(input_nodes)

    for node in input_convolutions:
        fqs_to_rescale.append(get_node_input(node, 1).name)

    conv_nodes_to_rescale = get_nodes_by_type(model, [op['type'] for op in OPERATIONS_WITH_WEIGHTS])
    conv_fqs_to_rescale = [get_node_input(node, 1).name for node in conv_nodes_to_rescale if
                           'need_rescale' in node and node['need_rescale']]
    fqs_to_rescale.extend(conv_fqs_to_rescale)
    return {'scaling_factor': scaling_factor,
            'fqs_to_rescale': fqs_to_rescale}


def unify_fq_scales(model, config):
    def _custom_broadcast(arrays_list):
        arrays_list = np.broadcast_arrays(*list(arr.T for arr in arrays_list))
        return [arr.T for arr in arrays_list]

    for bridges, fqs in find_fqs_to_unify(model, config):
        min_levels = []
        max_levels = []
        for fq in fqs:
            fq = get_node_by_name(model, fq)
            fq_inputs = get_node_inputs(fq)[1:]
            min_levels.append(get_node_value(fq_inputs[0]))
            max_levels.append(get_node_value(fq_inputs[1]))
        orig_shapes = [s.shape for s in min_levels]
        min_levels = _custom_broadcast(min_levels)
        max_levels = _custom_broadcast(max_levels)
        for i, fq in enumerate(fqs):
            fq = get_node_by_name(model, fq)
            if 'Concat' in [get_node_by_name(model, bridge).type for bridge in bridges]:
                min_level = np.mean(min_levels, axis=0).reshape(orig_shapes[i])
                max_level = np.mean(max_levels, axis=0).reshape(orig_shapes[i])
            else:
                min_level = np.min(min_levels, axis=0).reshape(orig_shapes[i])
                max_level = np.max(max_levels, axis=0).reshape(orig_shapes[i])

            fill_fake_quantize_node(fq, min_level, max_level)
