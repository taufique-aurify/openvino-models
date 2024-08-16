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
"""Device Panel Controller module"""
import logging
import os
from threading import Thread, Event

from wx.lib.pubsub import pub

from audio import audio_helper
from gui.caption_controller import CaptionController
from gui.caption_frame import CaptionFrame, CaptionTopic
from gui.device_panel import DevicePanel, ButtonState, Topic
from gui.gui_helper import show_warning_message
from speech_library.speech_manager import SpeechManager
from speech_library.speech_proxy import SPEECH_CONFIG

LOG_DIR = os.path.join(os.path.pardir, 'log')
MODELS_DIR = os.path.join(os.path.pardir, 'models')

_logger = logging.getLogger()


class DeviceController:
    """Controller for Device Panel"""
    def __init__(self, parent, panel: DevicePanel, title, position=0):
        """
        :param parent: Parent window
        :param panel: Device Panel
        :param title: Title
        :param position: Starting position of the Caption Frame
        """
        self._parent = parent  # not used, but needed to keep the reference
        self._panel = panel
        self._title = title

        self._device_list = []
        self._speech = None
        self._stream_reader = None
        self._init_thread = None
        self._reading_thread = None
        self._clipping_detected = False
        self._volume = 1.0
        self._level_gauge_enabled = True
        self._stop = Event()
        self._clear_caption_flag = Event()

        self._config = ''
        self._engine = ''
        self._batch_size = 0
        self._device = 0

        self._caption = CaptionController(
            CaptionFrame(panel.parent, title=title, position=position)
        )
        pub.subscribe(self._on_caption_hide, self._format_topic(CaptionTopic.HIDE))
        pub.subscribe(self._on_caption_clear, self._format_topic(CaptionTopic.CLEAR))

        pub.subscribe(self._on_device_selection_changed, self._format_topic(Topic.DEVICE_CHANGED))
        pub.subscribe(self._on_checked, self._format_topic(Topic.CAPTION_SHOW))
        pub.subscribe(self._set_volume, self._format_topic(Topic.VOLUME_SET))
        pub.subscribe(self._on_reset_clipping_indicator, self._format_topic(Topic.CLIPPING_RESET))
        pub.subscribe(self._on_recognize_stream, self._format_topic(Topic.RECOGNIZE_STREAM))

        pub.subscribe(self._on_config_selection_changed, Topic.CONFIG_CHANGED)
        pub.subscribe(self._on_engine_selection_changed, Topic.ENGINE_CHANGED)
        pub.subscribe(self._on_batch_size_selection_changed, Topic.BATCH_SIZE_CHANGED)
        pub.subscribe(self._on_close, Topic.CLOSE_WINDOW)

        self._set_clipping_indicator(False, force=True)

    def _format_topic(self, topic):
        """Return PubSub topic specific for this instance
        :param topic: PubSub topic name
        """
        return '{}_{}'.format(topic, self._title)

    def _on_config_selection_changed(self, value):
        """Handle configuration selection change
        :param value: Configuration name
        """
        self._config = value

    def _on_engine_selection_changed(self, value):
        """Handle inference engine selection change
        :param value: Inference engine name
        """
        self._engine = value

    def _on_batch_size_selection_changed(self, value):
        """Handle inference batch size selection change
        :param value: Inference batch size
        """
        self._batch_size = value

    def _on_device_selection_changed(self, value):
        """Handle device selection change
        :param value: Device index
        """
        self._device = value

    def reload_device_list(self, device_list, selection):
        """Update device list
        :param device_list: List of audio devices (tuples of SoundCard Device instance and name)
        :param selection: List index to select
        """
        self._device_list = device_list
        self._panel.set_device_choice([name for device, name in device_list], selection)
        self._panel.enable_recognize_stream_button(bool(device_list and self._config))

    def enable_recognizing(self, enable):
        """Enable recognition Button (if there are audio devices available)
        :param enable: Enable if True, disable otherwise
        """
        self._panel.enable_recognize_stream_button(bool(enable and self._device_list))

    def asr_on_result(self, utt_text, is_final):
        """Send utterance text from ASR engine to Caption Frame
        :param utt_text: Current utterance text
        :param is_final: It's the final form of current utterance if True
        """
        rh_result = utt_text.decode("utf-8").strip().lower()
        _logger.debug("Entered asr_on_result, rh_result: %s, is_final: %s", rh_result, is_final)
        self._caption.set_text(rh_result, is_final)

    def _on_recognize_stream(self, value):
        """Handle stream recognition start
        :param value: Start if True, stop otherwise
        """
        if value:
            if not self._init_thread or not self._init_thread.is_alive():
                _logger.debug("Starting initialization thread")
                self._init_thread = Thread(target=self._recognize_stream_start, daemon=True)
                self._init_thread.start()
        else:
            self._recognize_stream_stop()

    def _recognize_stream_start(self):
        """Initialize and start stream recognition"""
        self._stop.clear()
        self._panel.set_recognize_stream_button_state(ButtonState.INITIALIZING)
        self._enable_controls(False)

        self.show_caption(True)
        self._set_clipping_indicator(False)
        self._level_gauge_enabled = True
        self._clear_caption_flag.clear()

        self._speech = SpeechManager()
        if not self._speech.initialize(
                os.path.join(MODELS_DIR, self._config, SPEECH_CONFIG),
                infer_device=self._engine,
                batch_size=self._batch_size):
            _logger.error("Failed to initialize ASR recognizer")
            show_warning_message("Failed to initialize ASR recognizer")
            self._speech.close()
            self._speech = None
            self._panel.set_recognize_stream_button_state(ButtonState.IDLE)
            self._enable_controls(True)
            return

        if self._stop.is_set():
            return

        self._stream_reader = audio_helper.StreamReader(
            self._device_list[self._device][0], self._received_frames, self._on_clipping,
            self._set_level, self._get_volume)
        if not self._stream_reader.initialize():
            _logger.error("Failed to initialize Stream Reader")
            show_warning_message("Failed to initialize Stream Reader")
            self._speech.close()
            self._speech = None
            self._panel.set_recognize_stream_button_state(ButtonState.IDLE)
            self._enable_controls(True)
            return

        if self._stop.is_set():
            return

        self._caption.clear_text()

        if self._stop.is_set():
            return

        self._reading_thread = Thread(target=self._stream_reader.read_stream, daemon=True)
        self._reading_thread.start()

        self._panel.set_recognize_stream_button_state(ButtonState.RECOGNIZING)

    def _recognize_stream_stop(self):
        """Stop stream recognition"""
        self._stop.set()
        self._level_gauge_enabled = False
        self._panel.set_level_gauge(0)

        if self._stream_reader:
            self._stream_reader.stop_stream()
            self._stream_reader = None
        if self._reading_thread:
            self._reading_thread.join(1)
            self._reading_thread = None
        if self._speech:
            self._speech.push_data(b'', finish_processing=True)
            utt_text, _ = self._speech.get_result()
            self.asr_on_result(utt_text, True)
            self._speech.close()
            self._speech = None

        self._enable_controls(True)
        self._panel.set_recognize_stream_button_state(ButtonState.IDLE)

    def _on_checked(self, value):
        """Handle Caption Frame show
        :param value: Show if True, hide otherwise
        """
        self._caption.show(value)

    def _on_caption_hide(self):
        """Handle Caption Frame hide"""
        self.show_caption(False)

    def _on_caption_clear(self):
        """Handle Caption Frame text clear"""
        self.clear_caption()

    def clear_caption(self):
        """Clear Caption Frame text"""
        if self._speech:
            self._clear_caption_flag.set()
        else:
            self._caption.clear_text()

    def show_caption(self, show):
        """Show Caption Frame
        :param show: Show if True, hide otherwise
        """
        self._panel.set_show_caption_checkbox(show)
        self._caption.show(show)

    def _received_frames(self, frames):
        """Handle audio frames received from Stream Reader
        :param frames: Chunk of audio data (bytes)
        """
        if self._speech:
            clear_caption = self._clear_caption_flag.is_set()
            self._speech.push_data(frames, finish_processing=clear_caption)
            utt_text, is_stable = self._speech.get_result()
            self.asr_on_result(utt_text, is_stable)
            if clear_caption:
                self._caption.clear_text()
                self._clear_caption_flag.clear()

    def _on_clipping(self):
        """Handle clipping detected by Stream Reader"""
        self._set_clipping_indicator(True)

    def _set_clipping_indicator(self, enabled, force=False):
        """Set clipping indicator
        :param enabled: Enabled if True, disabled otherwise
        :param force: Ignore previous state of indicator if True
        """
        if self._clipping_detected != enabled or force:
            self._clipping_detected = enabled
            self._panel.set_clipping_indicator(enabled)
            self._caption.show_clipping_indicator(enabled)

    def _on_reset_clipping_indicator(self):
        """Handle clipping indicator reset"""
        self._set_clipping_indicator(False)

    def _get_volume(self):
        """Return current volume scaling factor (float [0, 2])"""
        return self._volume

    def _set_volume(self, value):
        """Set volume scaling factor from slider
        :param value: Volume (float [0, 2]: 0-200% of audio scaling factor)
        """
        self._volume = value
        self._set_clipping_indicator(False)

    def _set_level(self, level):
        """Handle audio level calculated by Stream Reader after scaling
        :param level: Current audio level (float [0, 1])
        """
        if self._level_gauge_enabled:
            self._panel.set_level_gauge(level * 100)

    def _enable_controls(self, enable):
        """Enable device controls
        :param enable: Enable if True, disable otherwise
        """
        self._panel.enable_device_controls(enable)
        pub.sendMessage(Topic.RECOGNITION_ACTIVE, sender=self, active=not enable)

    def _on_close(self):
        """Handle window closing"""
        self._recognize_stream_stop()
