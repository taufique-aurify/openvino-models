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

import multiprocessing
from math import ceil
from time import time, sleep

import numpy as np
from openvino.inference_engine import IECore

from .utils import append_stats, process_accumulated_stats
from ..api.engine import Engine
from ..graph.model_utils import save_model
from ..samplers.batch_sampler import BatchSampler
from ..utils.logger import get_logger
from ..utils.utils import create_tmp_dir, convert_output_key

logger = get_logger(__name__)


class IEEngine(Engine):

    def __init__(self, config, data_loader=None, metric=None):
        super().__init__(config, data_loader, metric)
        self._ie = IECore()
        self._model = None
        self._output_layers = None
        self._accumulated_layer_stats = dict()
        self._per_sample_metrics = []
        self._tmp_dir = create_tmp_dir()

    def set_model(self, model):
        """ Loads NetworkX model into InferenceEngine and stores it in Engine class
        :param model: NXModel instance
        """
        if model.is_cascade:
            raise Exception('Cascade models are not supported in current engine')

        # save NetworkX graph to IR and use it to initialize IE Network
        self._model = self._set_model(model)[0]['model']
        self._output_layers = list(self._model.outputs.keys())

    def _set_model(self, model):
        """Creates IENetwork instances from NetworkX models in NXModel.
        :param: model: NXModel instance
        :return: list of dictionaries:
                 [
                    {
                        'name': model name (if model.is_cascaded),
                        'model': IENetwork instance
                    },
                ]
        """
        paths = save_model(model, self._tmp_dir.name, 'tmp_model', for_stat_collection=True)
        ie_networks = []
        for path_dict in paths:
            ie_net = {'model': self._ie.read_network(model=path_dict['model'],
                                                     weights=path_dict['weights'])}
            if 'name' in path_dict:
                ie_net.update(name=path_dict['name'])
            ie_networks.append(ie_net)
        return ie_networks

    def predict(self, stats_layout=None, sampler=None, metric_per_sample=False, print_progress=False):
        """ Performs model inference on specified dataset subset
         :param stats_layout: dict of stats collection functions {node_name: {stat_name: fn}} (optional)
         :param sampler: sampling dataset to make inference
         :param metric_per_sample: if Metric is specified and the value is True,
                then the metric value will be calculated for each data sample, otherwise for the whole dataset
         :param print_progress: whether to print inference progress
         :returns a tuple of dictionaries of persample and overall metric values if 'metric_per_sample' is True
                  ({sample_id: sample index, 'metric_name': metric name, 'result': metric value},
                   {metric_name: metric value}), otherwise, a dictionary of overall metrics
                   {metric_name: metric value}
                  a dictionary of collected statistics {node_name: {stat_name: [statistics]}}
        """

        if self._model is None:
            raise Exception('Model was not set in Engine class')

        # If sampler is not specified, make a prediction on the whole dataset
        if sampler is None:
            sampler = BatchSampler(self.data_loader)

        stat_names_aliases = None
        if stats_layout:
            # Add outputs to the model for activation statistics collection
            self._add_outputs(stats_layout)
            # Creating statistics layout with IE-like names
            stats_layout, stat_names_aliases = self._convert_stats_names(stats_layout)

        self._predict(stats_layout=stats_layout,
                      sampler=sampler,
                      print_progress=print_progress,
                      need_metrics_per_sample=metric_per_sample)

        # Process accumulated statistics
        # Replace IE-like statistics names with the original ones
        accumulated_stats = \
            process_accumulated_stats(accumulated_stats=self._accumulated_layer_stats,
                                      stat_names_aliases=stat_names_aliases)

        # Calculate metrics of required type. Reset collected statistics
        metrics = None
        if self._metric:
            metrics = self._metric.avg_value
            if metric_per_sample:
                metrics = (sorted(self._per_sample_metrics, key=lambda i: i['sample_id']), metrics)

        self._reset()

        return metrics, accumulated_stats

    @staticmethod
    def postprocess_output(outputs, _metadata):
        """ Processes raw model output using the image metadata obtained during data loading """
        return outputs

    def _reset(self):
        """ Resets collected statistics """
        if self._metric:
            self._metric.reset()
        self._per_sample_metrics = []
        self._accumulated_layer_stats = {}

    def _add_outputs(self, stats_layout):
        self._model.add_outputs(list(stats_layout.keys()))

    def _predict(self, stats_layout, sampler, print_progress=False,
                 need_metrics_per_sample=False):
        """Performs model inference synchronously or asynchronously"""
        requests_number = self._get_requests_number(stats_layout)

        if requests_number == 1:
            self._process_dataset(stats_layout=stats_layout,
                                  sampler=sampler,
                                  print_progress=print_progress,
                                  need_metrics_per_sample=need_metrics_per_sample)
        else:
            self._process_dataset_async(stats_layout=stats_layout,
                                        sampler=sampler,
                                        print_progress=print_progress,
                                        need_metrics_per_sample=need_metrics_per_sample,
                                        requests_num=requests_number)

    def _process_infer_output(self, stats_layout, predictions,
                              batch_annotations, batch_meta, need_metrics_per_sample):
        # Collect statistics
        if stats_layout:
            self._collect_statistics(outputs=predictions,
                                     stats_layout=stats_layout,
                                     annotations=batch_annotations)

        # Postprocess network output
        output = predictions[self._output_layers[0]]
        predictions[self._output_layers[0]] = self.postprocess_output(output, batch_meta)

        # Update metrics
        if batch_annotations:
            # TODO: Create some kind of an order for the correct metric calculation
            logits = [predictions[name] for name in self._output_layers]  # output_layers are in a random order
            self._update_metrics(output=logits, annotations=batch_annotations,
                                 need_metrics_per_sample=need_metrics_per_sample)

    def _collect_statistics(self, outputs, stats_layout, annotations=None):
        """Collects statistics of specified layers.
        :param outputs: layer outputs
        :param stats_layout: dict of stats collection functions {layer_name: [fn]}
        :param annotations: list of annotations [(img_id, annotation)]
        """
        dataset_index = annotations[0][0] if annotations is not None and annotations[0][0] else 0
        append_stats(self._accumulated_layer_stats, stats_layout, outputs, dataset_index)

    def _update_metrics(self, output, annotations, need_metrics_per_sample=False):
        """ Updates metrics.
        :param output: network output
        :param annotations: a list of annotations for metrics collection [(img_id, annotation)]
        :param need_metrics_per_sample: whether to collect metrics for each batch
        """
        _, batch_annotations = map(list, zip(*annotations))
        annotations_are_valid = all(a is not None for a in batch_annotations)

        if self._metric and annotations_are_valid:
            self._metric.update(output, batch_annotations)
            if need_metrics_per_sample:
                batch_metrics = self._metric.value
                for metric_name, metric_value in batch_metrics.items():
                    for i, annotation in enumerate(annotations):
                        self._per_sample_metrics.append({'sample_id': annotation[0],
                                                         'metric_name': metric_name,
                                                         'result': metric_value[i]})

    def _populate_free_requests(self, free_irs, queued_irs, data_iterator):
        """Fills free inference requests with new data batch and start inference
        :param free_irs: list of completed infer requests
        :param queued_irs: list of running infer requests with corresponding image ids
        :param data_iterator: dataset iterator
        """
        for ir in free_irs:
            data_batch = next(data_iterator, None)
            if not data_batch:
                break
            batch_id, batch = data_batch
            image_ids, images, batch_meta = self._process_batch(batch)
            ir.async_infer(inputs=self._fill_input(self._model, images))
            queued_irs.append((batch_id, image_ids, batch_meta, ir))

        free_irs.clear()

    @staticmethod
    def _wait_for_any(irs):
        """Waits for any queued infer requests to finish inference.
        :param irs: list of queued infer requests
        :return list of results of completed infer requests [(batch_id, annotations, layer_outputs, infer_request)]
                list of queued infer requests
        """
        if not irs:
            return [], []

        result = []
        free_indexes = []
        for ir_id, (batch_id, image_annotations, batch_meta, ir) in enumerate(irs):
            if ir.wait(0) == 0:
                outputs = {out_name: out_blob.buffer for out_name, out_blob in ir.output_blobs.items()}
                result.append((batch_id, image_annotations, batch_meta, outputs, ir))
                free_indexes.append(ir_id)
        irs = [ir for ir_id, ir in enumerate(irs) if ir_id not in free_indexes]
        return result, irs

    def _fill_input(self, model, image_batch):
        """Matches network input name with corresponding input batch
        :param model: IENetwork instance
        :param image_batch: list of ndarray images or list with a dictionary of inputs mapping
        """
        if isinstance(image_batch[0], dict):
            return image_batch[0]

        input_info = model.input_info
        if len(input_info) == 1:
            input_blob = next(iter(input_info))
            return {input_blob: np.stack(image_batch, axis=0)}

        if len(input_info) == 2:
            image_info_nodes = list(filter(
                lambda x: len(x[1].input_data.shape) == 2, input_info.items()))

            if len(image_info_nodes) != 1:
                raise Exception('Two inputs networks must contain exactly one ImageInfo node')

            image_info_name, _ = image_info_nodes[0]
            image_tensor_name, _ = next(iter(filter(
                lambda x: x[0] != image_info_name, input_info.items())))

            image_tensor = (image_tensor_name, np.stack(image_batch, axis=0))

            ch, height, width = image_batch[0].shape
            image_info = (image_info_name,
                          np.stack(np.array([(height, width, ch)] * len(image_batch)), axis=0))

            return dict((k, v) for k, v in [image_tensor, image_info])

        raise Exception('Unsupported number of inputs')

    def _get_requests_number(self, stats_layout):
        """Returns number of requests for inference
        :param stats_layout: dict of stats collection functions {layer_name: [fn]} or None
        :return: number of requests
        """
        if stats_layout:
            requests_number = self._stat_requests_number
        else:
            requests_number = self._eval_requests_number

        if requests_number:
            requests_number_clipped = np.clip(requests_number, 1, multiprocessing.cpu_count())
            if requests_number_clipped != requests_number:
                logger.warning('Number of requests {} is out of range [1, {}]. Will be used {}.'
                               .format(requests_number, multiprocessing.cpu_count(), requests_number_clipped))
                requests_number = requests_number_clipped
        else:
            requests_number = 0

        return requests_number

    def _process_dataset_async(self, stats_layout, sampler, print_progress=False,
                               need_metrics_per_sample=False, requests_num=0):
        """Performs model inference on specified dataset subset asynchronously
        :param stats_layout: dict of stats collection functions {node_name: [fn]}(optional)
        :param sampler: sampling dataset to make inference
        :param print_progress: whether to print inference progress
        :param need_metrics_per_sample: whether to collect metrics for each batch
        :param requests_num: number of infer requests
        """

        progress_log_fn = logger.info if print_progress else logger.debug

        # Load model to the plugin
        executable_model = self._ie.load_network(network=self._model,
                                                 device_name=self.config.device,
                                                 num_requests=requests_num)
        free_irs = executable_model.requests
        queued_irs = []
        wait_time = 0.01

        progress_log_fn('Start inference of %d images', len(sampler))

        sampler_iter = iter(enumerate(sampler))
        # Start inference
        start_time = time()
        while free_irs or queued_irs:
            self._populate_free_requests(free_irs, queued_irs, sampler_iter)

            ready_irs, queued_irs = self._wait_for_any(queued_irs)
            if ready_irs:
                wait_time = 0.01
                while ready_irs:
                    batch_id, batch_annotations, batch_meta, predictions, ir = ready_irs.pop(0)
                    free_irs.append(ir)

                    self._process_infer_output(stats_layout, predictions,
                                               batch_annotations, batch_meta,
                                               need_metrics_per_sample)

                    # Print progress
                    if self._print_inference_progress(progress_log_fn,
                                                      batch_id, len(sampler),
                                                      start_time, time()):
                        start_time = time()
            else:
                sleep(wait_time)
                wait_time = max(wait_time * 2, .16)

        progress_log_fn('Inference finished')

    def _process_dataset(self, stats_layout, sampler, print_progress=False,
                         need_metrics_per_sample=False):
        """
        Performs model inference on specified dataset subset synchronously
        :param stats_layout: dict of stats collection functions {node_name: {stat_name: fn}} (optional)
        :param sampler: sampling dataset to make inference
        :param print_progress: whether to print inference progress
        :param need_metrics_per_sample: whether to collect metrics for each batch
        """

        progress_log_fn = logger.info if print_progress else logger.debug

        # Load model to the plugin
        executable_model = self._ie.load_network(network=self._model,
                                                 device_name=self.config.device)

        progress_log_fn('Start inference of %d images', len(sampler))

        # Start inference
        start_time = time()
        for batch_id, batch in iter(enumerate(sampler)):
            batch_annotations, image_batch, batch_meta = self._process_batch(batch)

            # Infer batch of images
            predictions = executable_model.infer(self._fill_input(self._model, image_batch))

            self._process_infer_output(stats_layout, predictions,
                                       batch_annotations, batch_meta,
                                       need_metrics_per_sample)

            # Print progress
            if self._print_inference_progress(progress_log_fn,
                                              batch_id, len(sampler),
                                              start_time, time()):
                start_time = time()

        progress_log_fn('Inference finished')

    @staticmethod
    def _process_batch(batch):
        """ Processes batch data and returns lists of annotations, images and batch meta data
        :param batch: a list with batch data.
                      Possible formats: [((img_id, label), image)]
                                        [({img_id: label}, image)]
        :returns a list with annotations [(img_id, label)]
                 a list with input data  [image]
                 a list with batch meta data
        """
        if not all([isinstance(item, tuple) for item in batch]):
            raise RuntimeError('Inconsistent data in the batch. '
                               'Some items contain annotation, and some do not.')

        if all([len(item) == 2 for item in batch]):
            image_annotation, images = map(list, zip(*batch))
            meta_data = [{}]*len(images)
        elif all([len(item) == 3 for item in batch]):
            image_annotation, images, meta_data = map(list, zip(*batch))
        else:
            raise RuntimeError('Inconsistent data in the batch. '
                               'Some items contain meta data, and some do not.')

        # if image annotations are represented as dictionaries, convert them to tuples
        if image_annotation is not None and all([isinstance(item, dict) for item in image_annotation]):
            image_annotation = [(img_id, label) for sample_annot in image_annotation
                                for img_id, label in sample_annot.items()]

        return image_annotation, images, meta_data

    @staticmethod
    def _print_inference_progress(log_fn, current_id, total_dataset_size,
                                  start_time, finish_time):
        """Prints inference progress. Returns True if timer needs update"""
        if (current_id + 1) % ceil(total_dataset_size / 10) == 0:
            log_fn('%d/%d batches are processed in %.2fs',
                   current_id + 1,
                   total_dataset_size,
                   finish_time - start_time)
            return True
        return False

    @staticmethod
    def _convert_stats_names(stats_layout):
        """Converts statistics names from MO format to IE format"""
        stat_names_aliases = {convert_output_key(key): key for key in stats_layout}
        stats_layout_ie_style = {convert_output_key(key): value
                                 for key, value in stats_layout.items()}
        return stats_layout_ie_style, stat_names_aliases
