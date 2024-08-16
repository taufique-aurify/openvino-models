# *****************************************************************************
# Copyright (C) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions
# and limitations under the License.
#
#
# SPDX-License-Identifier: Apache-2.0
# *****************************************************************************
"""Main Frame Controller module"""
import logging
import os
from threading import Thread, Event

from wx.lib.pubsub import pub

from audio import audio_helper
from audio.wave_data_generator import data_generator, check_wave_format
from gui.device_controller import DeviceController
from gui.gui_helper import show_warning_message
from gui.gui_helper import is_ascii
from gui.main_frame import MainFrame, ButtonState, Topic
from speech_library.speech_manager import SpeechManager
from speech_library.speech_proxy import SPEECH_CONFIG

MODELS_DIR = os.path.join(os.path.pardir, 'models')

DEVICE_COUNT = 2

_logger = logging.getLogger()


class MainController:
    """Controller for Main Frame"""
    def __init__(self):
        self._frame = MainFrame(None, title="Live Speech Recognition Demo")

        self._config = ''
        self._engine = ''
        self._batch_size = 0
        self._wave_path = ''

        self._speech = None
        self._wave_stop_flag = Event()
        self._wave_thread = None
        self._active_recognitions = {}

        self._device_controls = []
        for i in range(DEVICE_COUNT):
            title = "Source {}".format(i+1)
            panel = self._frame.add_device_panel(title)
            controller = DeviceController(self, panel, title, -DEVICE_COUNT+i+1)
            self._device_controls.append(controller)
        self._device_controls[0].show_caption(True)

        pub.subscribe(self._on_config_changed, Topic.CONFIG_CHANGED)
        pub.subscribe(self._on_reload_lists, Topic.RELOAD_CONFIG)
        pub.subscribe(self._on_engine_changed, Topic.ENGINE_CHANGED)
        pub.subscribe(self._on_batch_size_changed, Topic.BATCH_SIZE_CHANGED)
        pub.subscribe(self._on_wave_path_changed, Topic.WAVE_PATH_CHANGED)
        pub.subscribe(self._on_recognize_wave, Topic.RECOGNIZE_WAVE)
        pub.subscribe(self._on_close_window, Topic.CLOSE_WINDOW)

        pub.subscribe(self._on_recognition_active, Topic.RECOGNITION_ACTIVE)

        self._frame.set_engine_choice(["CPU", "GNA", "GPU"], 0)
        self._frame.set_batch_size_choice(["1", "2", "4", "8"], 3)

        self._reload_config_list()
        self._reload_device_list()

        self._frame.Show(True)

    def _on_config_changed(self, value):
        """Handle configuration selection change
        :param value: Configuration name
        """
        self._config = value

    def _on_engine_changed(self, value):
        """Handle inference engine selection change
        :param value: Inference engine name
        """
        self._engine = value

    def _on_batch_size_changed(self, value):
        """Handle inference batch size selection change
        :param value: Inference batch size
        """
        self._batch_size = value

    def _on_wave_path_changed(self, value):
        """Handle WAVE path change
        :param value: New WAVE path
        """
        self._wave_path = value

    def _on_recognition_active(self, sender, active):
        """Handle recognition activations from Device Controllers and disable controls accordingly
        :param sender: Controller that activated the recognition
        :param active: Recognition activated if True, deactivated otherwise
        """
        self._active_recognitions[sender] = active
        self._enable_controls(not any(d for d in self._active_recognitions.values()))

    def _enable_controls(self, enable=True):
        """Enable configuration controls and WAVE recognition
        :param enable: Enable if True, disable otherwise
        """
        self._frame.enable_config_controls(enable)
        self._frame.enable_recognize_wave_button(enable)

    def _enable_wave_controls(self, enable=True):
        """Enable WAVE controls and stream recognition
        :param enable: Enable if True, disable otherwise
        """
        self._on_recognition_active(self, not enable)
        self._frame.enable_wave_path_controls(enable)
        for controller in self._device_controls:
            controller.enable_recognizing(enable)

    def _on_reload_lists(self):
        """Handle configuration and device list reload"""
        self._reload_config_list()
        self._reload_device_list()

    def _reload_config_list(self):
        """Reload configuration list based on config files found in models directory"""
        config_list = [os.path.relpath(dirpath, MODELS_DIR) for dirpath, _, files
                       in os.walk(MODELS_DIR) if SPEECH_CONFIG in files]
        config_list.sort()
        config_index = next((i for i, e in enumerate(config_list) if 'en-US' in e), 0)\
            if config_list else -1

        self._frame.set_config_choice(config_list, config_index)
        self._frame.enable_recognize_wave_button(bool(config_list))
        if not config_list:
            _logger.warning("No configuration files found in models directory")
            show_warning_message("No configuration files found in models directory")

    def _reload_device_list(self):
        """Reload audio device list"""
        device_list, default_input_index, loopback_index = audio_helper.get_input_device_list()
        indices = [loopback_index, default_input_index] + [0] * (len(self._device_controls)-2)
        for i, controller in enumerate(self._device_controls):
            controller.reload_device_list(device_list, indices[i])
        if not device_list:
            _logger.warning("No audio devices available")
            show_warning_message("No audio devices available")

    def _on_recognize_wave(self, value):
        """Handle WAVE recognition start
        :param value: Start if True, stop otherwise
        """
        if value:
            Thread(target=self._recognize_wave_start, daemon=True).start()
        else:
            self._recognize_wave_stop()

    def _recognize_wave_start(self):
        """Initialize and start WAVE recognition"""
        if not is_ascii(self._wave_path):
            show_warning_message("File contains non-ASCII characters")
            self._frame.set_recognize_wave_button_state(ButtonState.IDLE)
            return
        if not os.path.isfile(self._wave_path):
            show_warning_message("File does not exist")
            self._frame.set_recognize_wave_button_state(ButtonState.IDLE)
            return
        if not check_wave_format(self._wave_path):
            show_warning_message("Wrong file format. Only 16-bit WAVE files are supported")
            self._frame.set_recognize_wave_button_state(ButtonState.IDLE)
            return

        self._device_controls[0].show_caption(True)
        self._device_controls[0].clear_caption()

        self._frame.set_recognize_wave_button_state(ButtonState.INITIALIZING)
        self._enable_wave_controls(False)
        self._wave_stop_flag.clear()
        self._speech = SpeechManager()
        if not self._speech.initialize(
                os.path.join(MODELS_DIR, self._config, SPEECH_CONFIG),
                infer_device=self._engine, batch_size=self._batch_size):
            _logger.error("Failed to initialize ASR recognizer")
            show_warning_message("Failed to initialize ASR recognizer")
            self._frame.set_recognize_wave_button_state(ButtonState.IDLE)
            self._enable_wave_controls(True)
            return

        if self._wave_stop_flag.is_set():
            return

        self._wave_thread = Thread(target=self._push_wave_data, daemon=True)
        self._wave_thread.start()
        self._frame.set_recognize_wave_button_state(ButtonState.RECOGNIZING)

    def _recognize_wave_stop(self):
        """Stop WAVE recognition"""
        self._wave_stop_flag.set()
        if self._speech:
            self._speech.close()
            self._speech = None
        self._frame.set_recognize_wave_button_state(ButtonState.IDLE)
        self._enable_wave_controls(True)

    def _push_wave_data(self):
        """Push WAVE data to ASR and handle result"""
        try:
            for wave_data in data_generator(self._wave_path):
                self._speech.push_data(wave_data)
                utt_text, is_stable = self._speech.get_result()
                self._device_controls[0].asr_on_result(utt_text, is_stable)
                if self._wave_stop_flag.is_set():
                    break
        except OSError:
            _logger.error("Failed to read WAVE data")
            show_warning_message("Failed to read WAVE data")
        self._speech.push_data(b'', finish_processing=True)
        utt_text, _ = self._speech.get_result()
        self._device_controls[0].asr_on_result(utt_text, True)
        self._recognize_wave_stop()

    def _on_close_window(self):
        """Handle window closing"""
        self._recognize_wave_stop()
