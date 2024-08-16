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

from .utils import merge_algos_by_samplers, merge_stats_by_algo_names
from ..samplers.sampler import Sampler
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsCollector:

    def __init__(self, engine):
        self._engine = engine
        self._layout_by_algo = {}
        self._accumulated_stats_by_algo = {}
        self._samplers = {}

    def register(self, algo_name, stats_layout, sampler: Sampler):
        """
        Register statistics_layout for algorithm
        :param algo_name: algorithm name
        :param stats_layout: dict of stats collection functions {node_name: {stats_name: fn}}
        :param sampler: instance of Sampler descendant class to draw samples from dataset
        """
        if algo_name in self._layout_by_algo:
            for layer_name in stats_layout:
                for layer_stat in stats_layout[layer_name]:
                    if layer_stat not in self._layout_by_algo[algo_name][layer_name]:
                        self._layout_by_algo[algo_name][layer_name][layer_stat] = stats_layout[layer_name][layer_stat]
        else:
            self._layout_by_algo[algo_name] = stats_layout
        self._samplers[algo_name] = sampler

    def compute_statistics(self, model):
        """
        Compute statistics for registered statistics
        :param model: NXModel instance
        """
        # checks that statistics layouts for registered algorithms are not empty
        if all([not stats_layout for stats_layout in self._layout_by_algo.values()]):
            for algo_name_ in self._layout_by_algo:
                self._add_stats_to_accumulated(algo_name_, {})
            return

        self._engine.set_model(model)

        predict_iterations = merge_algos_by_samplers(self._samplers)

        def return_stat_names(algo_name, stats, stat_aliases):
            algo_stats = {node_name: {} for node_name in stat_aliases[algo_name]}
            for node_name, node_stats in stat_aliases[algo_name].items():
                for fn, stat_names in node_stats.items():
                    for stat_name in stat_names:
                        algo_stats[node_name][stat_name] = stats[node_name][fn]
            return algo_stats

        for algo_names, sampler in predict_iterations:
            combined_stats, stat_aliases_ = merge_stats_by_algo_names(
                algo_names, self._layout_by_algo)
            _, stats_ = self._engine.predict(combined_stats, sampler)

            for name in algo_names:
                self._add_stats_to_accumulated(
                    name, return_stat_names(name, stats_, stat_aliases_))

            logger.update_progress(len(sampler))

    def get_statistics_for_algorithm(self, algo_name):
        """
        Return dict with statistics accordingly with statistics_layout for defined algorithm
        :param algo_name: algorithm name
        :return dictionary of collected statistics {node_name: {stat_name: [statistics]}}
        """
        if algo_name not in self._layout_by_algo:
            raise Exception('Please, registry statistics for {} algorithm and run '
                            'collect statistics before algorithm running'.format(algo_name))

        if algo_name not in self._accumulated_stats_by_algo:
            raise Exception('Please, run compute_statistics method'
                            'before collecting statistics value')

        return self._accumulated_stats_by_algo[algo_name]

    def _add_stats_to_accumulated(self, algo_name, stats):
        """
        Adding new_computed statistics to algorithm with already stored accumulated_stats.
        """
        if algo_name not in self._accumulated_stats_by_algo:
            self._accumulated_stats_by_algo[algo_name] = {}

        accumulated_stats = self._accumulated_stats_by_algo[algo_name]
        for node_name in stats:
            if node_name in accumulated_stats:
                for stats_name, value in stats[node_name].items():
                    if stats_name in accumulated_stats[node_name]:
                        accumulated_stats[node_name][stats_name].extend(value)
                    else:
                        accumulated_stats[node_name][stats_name] = value
            else:
                accumulated_stats[node_name] = stats[node_name]


def collect_statistics(engine, model, algo_seq):
    """
    1. Register all algorithms stats layouts
    2. Run statistics computing
    :param engine: instance of a class inherited from Engine interface
    :param model: NetworkX model
    :param algo_seq: sequence of classes inherited from Algorithm interface
    :return: None
    """
    if not algo_seq:
        return

    logger.info('Start computing statistics for algorithms : {}'.
                format(','.join([algo.name for algo in algo_seq])))
    stats_collector = StatisticsCollector(engine)

    for algo in algo_seq:
        algo.register_statistics(model, stats_collector)

    stats_collector.compute_statistics(model)
    logger.info('Computing statistics finished')
