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

import os
from copy import deepcopy
from addict import Dict
import networkx as nx

from compression.graph.graph_utils import load_graph, save_graph
from compression.graph import editor as ge
from compression.graph.utils import is_ignored, preprocess_ignored_params
from compression.utils.logger import get_logger, stdout_redirect

logger = get_logger(__name__)


class NXModel:
    """
    Class encapsulating the logic of graph operations handling
    for multiple NetworkX models (Model Optimizer representation).
    Created to provide seamless processing of cascaded (composite) models.
    """
    def __init__(self, **kwargs):
        """ Constructor. Should take either model config, or NetworkX graph.
        :param config: model config to init from
        :param graph: NetworkX instance to init from
        """
        self._models = []
        self._prefix_is_applied = False
        self._cache = Dict()
        if len(kwargs) != 1:
            raise TypeError('Unable to load model. Invalid keyword arguments number. Expected 1, got {}.'
                            'Either model config (config=) or NetworkX graph (graph=) is expected.'
                            .format(len(kwargs)))
        if 'config' in kwargs:
            self._from_config(kwargs['config'])
        elif 'graph' in kwargs:
            self._from_graph(kwargs['graph'])
        else:
            raise TypeError('Unable to load models. Invalid keyword argument.'
                            'Either model config (config=) or NetworkX graph (graph=) is expected.')

    def _from_config(self, model_config):
        if not isinstance(model_config, Dict):
            model_config = Dict(model_config)
        if model_config.cascade:
            for model_dict in model_config.cascade:
                model_config_ = model_config.deepcopy()
                model_config_.update(model_dict)
                self._models.append({'model': load_graph(model_config_)})
                if len(model_config.cascade) > 1:
                    self._models[-1]['name'] = model_dict.name
        else:
            self._models.append({'model': load_graph(model_config)})

        self.name = model_config.model_name
        self._is_cascade = len(self._models) > 1
        if self._is_cascade:
            self._add_models_prefix()

    def _from_graph(self, graph):
        self._models.append({'model': graph})
        self._is_cascade = False

    @property
    def models(self):
        return self._models

    @property
    def is_cascade(self):
        return self._is_cascade

    def save(self, save_path, model_name=None, for_stat_collection=False):
        """ Save model as IR in specified path
        :param save_path: path to save the model
        :param model_name: name under which the model will be saved
        :param for_stat_collection: whether model is saved to be used
        for statistic collection or for normal inference (affects only cascaded models).
        If set to False, removes model prefixes from node names.
        :return model_paths: list of dictionaries:
        'name': model name (for cascade models only)
        'model': path to xml
        'weights': path to bin
         """
        if not for_stat_collection:
            self._remove_models_prefix()
        name = model_name
        model_paths = []
        for model_dict in self._models:
            model_path = {}
            if self._is_cascade:
                m_name = model_dict['name']
                name = '{}_{}'.format(model_name, m_name) if model_name else m_name
                model_path['name'] = m_name
            if not name:
                name = model_dict['model'].name
            model_path['model'] = os.path.join(save_path, name + '.xml')
            model_path['weights'] = os.path.join(save_path, name + '.bin')
            model_paths.append(model_path)
            stdout_redirect(save_graph, model_dict['model'], save_path, name)

        if not for_stat_collection:
            self._restore_models_prefix()

        return model_paths

    def pseudo_topological_sort(self):
        return [node for model_dict in self._models
                for node in model_dict['model'].pseudo_topological_sort()]

    def is_node_ignored(self, ignored_params, node, skipped=True):
        """ Return whether node should be ignored by algo or not
        :param ignored_params: ignored parameters
        :param node: node to check
        :param skipped: boolean value - whether to take into account skipped or not
        """
        cache_is_valid = self._cache.raw_ignored_params == ignored_params
        if not cache_is_valid:
            self._cache.raw_ignored_params = deepcopy(ignored_params)
            self._cache.ignored_params = preprocess_ignored_params(ignored_params, self)

        for model_dict in self._models:
            if self._is_cascade and not node.name.startswith(model_dict['name']):
                continue
            ignored_params_ = self._cache.ignored_params[model_dict['name']] if self._is_cascade \
                else self._cache.ignored_params

            return is_ignored(ignored_params_, node, skipped=skipped)

        raise RuntimeError('Node {} not found'.format(node.name))

    def get_final_output_nodes(self):
        """Returns list of Result nodes from the last model of cascade"""
        last_model = self._models[-1]['model']
        return ge.get_nodes_by_type(last_model, ['Result'])

    def clean_up(self):
        for model_dict in self._models:
            model_dict['model'].clean_up()

    @property
    def meta_data(self):
        return [model_dict['model'].meta_data
                for model_dict in self._models]

    @meta_data.setter
    def meta_data(self, meta_data):
        for model_dict, meta_data_ in zip(self.models, meta_data):
            model_dict['model'].meta_data = meta_data_

    def number_of_nodes(self):
        """Returns total number of nodes of all models"""
        return sum([model_dict['model'].number_of_nodes()
                    for model_dict in self._models])

    def relabel_nodes(self, mapping):
        """" Relabel (inplace) the nodes of all models
        :param mapping: dictionary with old labels as keys and new ones as values
        """
        for model_dict in self._models:
            model = model_dict['model']
            mapping_ = {key: value for key, value in mapping.items()
                        if key in model.nodes()}
            nx.relabel_nodes(model, mapping_, False)

    def node_labels(self):
        """ Returns list of labels of all models"""
        nodes = []
        for model_dict in self._models:
            nodes.extend(list(model_dict['model'].nodes()))
        return nodes

    def _add_models_prefix(self):
        """Adds model name prefix to node names"""
        if not self._prefix_is_applied:
            self._prefix_is_applied = True
            for model_dict in self._models:
                model_name, model = model_dict['name'], model_dict['model']
                for node in ge.get_all_operation_nodes(model):
                    node.name = '{}_{}'.format(model_name, node.name)

    def _remove_models_prefix(self):
        """Removes model name prefix from node names"""
        if self._prefix_is_applied:
            self._prefix_is_applied = False
            for model_dict in self._models:
                model_name, model = model_dict['name'], model_dict['model']
                self._cache.node_names[model_name] = []
                for node in ge.get_all_operation_nodes(model):
                    if node.name.startswith(model_name):
                        node.name = node.name.replace(model_name + '_', '', 1)
                        self._cache.node_names[model_name].append(node.name)

    def _restore_models_prefix(self):
        """Restores removed model name prefix in node name"""
        if self._cache.node_names:
            self._prefix_is_applied = True
            for model_dict in self._models:
                model_name, model = model_dict['name'], model_dict['model']
                for node in ge.get_all_operation_nodes(model):
                    if node.name in self._cache.node_names[model_name]:
                        node.name = '{}_{}'.format(model_name, node.name)
            self._cache.pop('node_names')
