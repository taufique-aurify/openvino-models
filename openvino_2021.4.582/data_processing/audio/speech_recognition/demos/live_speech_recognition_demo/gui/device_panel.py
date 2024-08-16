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
"""Device Panel module"""
from enum import Enum

import wx
from wx.lib.agw.gradientbutton import GradientButton
from wx.lib.pubsub import pub

from gui.gui_helper import call_after, BORDER

CONTROL_SIZE = (88, -1)
SLIDER_DEFAULT_VALUE = 20
SLIDER_MAX_VALUE = 40
LED_ON_COLOR = wx.Colour(225, 0, 0)
LED_OFF_COLOR = wx.LIGHT_GREY


class Topic:
    """General topic for PubSub"""
    CONFIG_CHANGED = "config_changed"
    RELOAD_CONFIG = "reload_config"
    ENGINE_CHANGED = "engine_changed"
    BATCH_SIZE_CHANGED = "batch_size_changed"
    WAVE_PATH_CHANGED = "wave_path_changed"
    RECOGNIZE_WAVE = "recognize_wave"

    DEVICE_CHANGED = "device_changed"
    CAPTION_SHOW = "caption_show"
    VOLUME_SET = "volume_set"
    CLIPPING_RESET = "clipping_reset"
    RECOGNIZE_STREAM = "recognize_stream"
    RECOGNITION_ACTIVE = "recognition_active"

    CLOSE_WINDOW = "close_window"


class ButtonState(Enum):
    """State of recognize button"""
    DISABLED = 0
    IDLE = 1
    INITIALIZING = 2
    RECOGNIZING = 3


class DevicePanel(wx.BoxSizer):
    """Device Panel"""
    def __init__(self, parent: wx.Window, title):
        """
        :param parent: Parent window
        :param title: Title
        """
        super().__init__(wx.HORIZONTAL)
        self.parent = parent
        self._title = title

        self._device_choice = wx.Choice(parent)
        self._device_choice.Bind(wx.EVT_CHOICE, self._on_device_changed)
        self.Add(self._device_choice, 1, wx.ALIGN_CENTER)

        self._show_caption_checkbox = wx.CheckBox(parent, wx.ID_ANY, "Show Captions")
        self._show_caption_checkbox.SetToolTip(wx.ToolTip("Show Caption Frame"))
        self._show_caption_checkbox.Bind(wx.EVT_CHECKBOX, self._on_checked)
        self.Add(self._show_caption_checkbox, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._volume_slider = wx.Slider(parent, size=CONTROL_SIZE, style=wx.SL_HORIZONTAL,
                                        value=SLIDER_DEFAULT_VALUE, maxValue=SLIDER_MAX_VALUE)
        self._volume_slider.SetToolTip(wx.ToolTip("Volume Scale"))
        self._volume_slider.Bind(wx.EVT_SLIDER, self._set_volume)
        self.Add(self._volume_slider, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._volume_label = wx.StaticText(parent, wx.ID_ANY, "%.2f" % 1.0)
        self.Add(self._volume_label, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._level_gauge = wx.Gauge(parent, size=CONTROL_SIZE,
                                     style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self._level_gauge.SetToolTip(wx.ToolTip("Audio Level"))
        self.Add(self._level_gauge, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._clipping_indicator = GradientButton(parent, size=(15, 15))
        self._clipping_indicator.Bind(wx.EVT_BUTTON, self._on_reset_clipping_indicator)
        self.Add(self._clipping_indicator, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._recognize_stream_button = wx.ToggleButton(parent, label="Recognize")
        self._recognize_stream_button.Bind(wx.EVT_TOGGLEBUTTON, self._on_recognize_stream)
        self.Add(self._recognize_stream_button, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

    def set_device_choice(self, options, selection):
        """Set device choice options and selection
        :param options: List of device names
        :param selection: List index to select
        """
        set_choice(self._device_choice, options, selection)
        self._on_device_changed()

    def enable_device_controls(self, enable=True):
        """Enable device controls
        :param enable: Enable if True, disable otherwise
        """
        self._device_choice.Enable(enable)

    @call_after
    def set_show_caption_checkbox(self, state):
        """Set state of show caption checkbox
        :param state: Checked if True, unchecked otherwise
        """
        self._show_caption_checkbox.SetValue(state)

    @call_after
    def enable_recognize_stream_button(self, enable=True):
        """Enable recognize stream button
        :param enable: Enable if True, disable otherwise
        """
        self._recognize_stream_button.Enable(enable)

    @call_after
    def set_recognize_stream_button_state(self, state: ButtonState):
        """Set recognize stream button state
        :param state: Button state (Enum)
        """
        set_button_state(self._recognize_stream_button, state)

    @call_after
    def set_level_gauge(self, level):
        """Set audio level gauge
        :param level: Current audio signal level (float [0, 1])
        """
        self._level_gauge.SetValue(level)

    @call_after
    def set_clipping_indicator(self, enabled):
        """Set state of clipping indicator
        :param enabled: Enable if True, disable otherwise
        """
        self._clipping_indicator.SetBaseColours(LED_ON_COLOR if enabled else LED_OFF_COLOR)
        self._clipping_indicator.SetToolTip(
            wx.ToolTip("Clipping detected!" if enabled else "Clipping indicator"))

    def _on_device_changed(self, _=None):
        """Send PubSub message on device changed"""
        pub.sendMessage(self._format_topic(Topic.DEVICE_CHANGED),
                        value=self._device_choice.GetSelection())

    def _on_checked(self, _=None):
        """Send PubSub message on show caption frame"""
        pub.sendMessage(self._format_topic(Topic.CAPTION_SHOW),
                        value=self._show_caption_checkbox.GetValue())

    def _set_volume(self, _=None):
        """Send PubSub message on set volume and update label"""
        volume = self._volume_slider.GetValue() / SLIDER_DEFAULT_VALUE
        self._volume_label.SetLabelText("%.2f" % volume)
        pub.sendMessage(self._format_topic(Topic.VOLUME_SET), value=volume)

    def _on_reset_clipping_indicator(self, _=None):
        """Send PubSub message on reset clipping indicator"""
        pub.sendMessage(self._format_topic(Topic.CLIPPING_RESET))

    def _on_recognize_stream(self, _=None):
        """Send PubSub message on recognize stream start/stop"""
        pub.sendMessage(self._format_topic(Topic.RECOGNIZE_STREAM),
                        value=self._recognize_stream_button.GetValue())

    def _format_topic(self, topic):
        """Return PubSub topic specific for this instance
        :param topic: PubSub topic name
        """
        return '{}_{}'.format(topic, self._title)


def set_choice(choice: wx.Choice, options, selection):
    """Set options and selection of given choice
    :param choice: Choice item
    :param options: List of device names
    :param selection: List index to select
    """
    choice.Set(options)
    choice.SetSelection(selection)


@call_after
def set_button_state(button: wx.ToggleButton, state: ButtonState):
    """Set state of given button
    :param button: ToggleButton item
    :param state: Button state (Enum)
    """
    if state == ButtonState.DISABLED:
        button.Enable(False)
    elif state == ButtonState.IDLE:
        button.Enable(True)
        button.SetValue(False)
        button.SetLabel("Recognize")
    elif state == ButtonState.INITIALIZING:
        button.Enable(False)
        button.SetLabel("Initializing...")
    elif state == ButtonState.RECOGNIZING:
        button.Enable(True)
        button.SetLabel("Recognizing...")
