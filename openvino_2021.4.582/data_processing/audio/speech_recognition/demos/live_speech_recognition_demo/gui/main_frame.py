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
"""Main Frame module"""
import os

import wx
from wx.lib.pubsub import pub

from gui.device_panel import DevicePanel, Topic, ButtonState, set_choice, set_button_state
from gui.gui_helper import call_after, fix_frame_height, BORDER


class StaticBoxBorder(wx.StaticBoxSizer):
    """Static Box Sizer with inner border"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inner_sizer = wx.BoxSizer(self.GetOrientation())
        box_border = 0 if os.name == 'nt' else BORDER + self.GetStaticBox().GetBordersForSizer()[1]
        super().Add(self._inner_sizer, 1, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, box_border)

    def Add(self, *args, **kwargs):
        """Append a child to the inner sizer (override method in wx.Sizer)"""
        self._inner_sizer.Add(*args, **kwargs)


class MainFrame(wx.Frame):
    """Main Frame"""
    def __init__(self, parent, id_=wx.ID_ANY, title=""):
        """
        :param parent: Parent window
        :param id_: Frame ID
        :param title: Title
        """
        super().__init__(parent, id_, title)
        self.Bind(wx.EVT_CLOSE, self._on_close_window)

        outer_sizer = wx.BoxSizer(wx.VERTICAL)
        config_sizer = wx.BoxSizer(wx.HORIZONTAL)

        trail_box = StaticBoxBorder(wx.HORIZONTAL, self, "Speech Recognition")
        config_label = wx.StaticText(trail_box.GetStaticBox(), wx.ID_ANY, "Configuration:")
        trail_box.Add(config_label, 0, wx.ALIGN_CENTER)
        self._config_choice = wx.Choice(trail_box.GetStaticBox())
        self._config_choice.Bind(wx.EVT_CHOICE, self._on_config_changed)
        trail_box.Add(self._config_choice, 1, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._reload_config_button = wx.Button(trail_box.GetStaticBox(), label="Reload")
        self._reload_config_button.Bind(wx.EVT_BUTTON, self._on_reload_config)
        trail_box.Add(self._reload_config_button, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)
        config_sizer.Add(trail_box, 1, wx.EXPAND)

        inference_box = StaticBoxBorder(wx.HORIZONTAL, self, "OpenVINO Inference")
        engine_label = wx.StaticText(inference_box.GetStaticBox(), wx.ID_ANY, "Engine:")
        inference_box.Add(engine_label, 0, wx.ALIGN_CENTER)
        self._engine_choice = wx.Choice(inference_box.GetStaticBox())
        self._engine_choice.Bind(wx.EVT_CHOICE, self._on_engine_changed)
        inference_box.Add(self._engine_choice, 1, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        batch_label = wx.StaticText(inference_box.GetStaticBox(), wx.ID_ANY, "Batch Size:")
        inference_box.Add(batch_label, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)
        self._batch_choice = wx.Choice(inference_box.GetStaticBox())
        self._batch_choice.Bind(wx.EVT_CHOICE, self._on_batch_size_changed)
        inference_box.Add(self._batch_choice, 1, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        config_sizer.Add(inference_box, 1, wx.EXPAND | wx.LEFT, BORDER)
        outer_sizer.Add(config_sizer, 0, wx.EXPAND | wx.ALL, BORDER)

        self._stream_box = StaticBoxBorder(wx.HORIZONTAL, self, "Recognize Stream")
        self._stream_box.GetStaticBox().SetBackgroundColour(self.GetBackgroundColour())
        self._stream_sizer = wx.FlexGridSizer(2, BORDER, BORDER)
        self._stream_sizer.AddGrowableCol(1)
        self._stream_box.Add(self._stream_sizer, 1, wx.EXPAND)
        outer_sizer.Add(self._stream_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, BORDER)

        recognize_wave_box = StaticBoxBorder(wx.HORIZONTAL, self, "Recognize WAVE")
        recognize_wave_label = wx.StaticText(recognize_wave_box.GetStaticBox(),
                                             wx.ID_ANY, "File Path:")
        recognize_wave_box.Add(recognize_wave_label, 0, wx.ALIGN_CENTER)
        self._wave_path_text_ctrl = wx.TextCtrl(recognize_wave_box.GetStaticBox(),
                                                style=wx.SUNKEN_BORDER)
        self._wave_path_text_ctrl.SetMaxLength(4096)
        self._wave_path_text_ctrl.Bind(wx.EVT_CONTEXT_MENU, lambda evt: None)
        self._wave_path_text_ctrl.Bind(wx.EVT_TEXT, self._on_wave_path_changed)
        recognize_wave_box.Add(self._wave_path_text_ctrl, 1, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._select_wave_button = wx.Button(recognize_wave_box.GetStaticBox(),
                                             label="Select File")
        self._select_wave_button.Bind(wx.EVT_BUTTON, self._on_select_wave)
        recognize_wave_box.Add(self._select_wave_button, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        self._recognize_wave_button = wx.ToggleButton(recognize_wave_box.GetStaticBox(),
                                                      label="Recognize")
        self._recognize_wave_button.Bind(wx.EVT_TOGGLEBUTTON, self._on_recognize_wave)
        recognize_wave_box.Add(self._recognize_wave_button, 0, wx.ALIGN_CENTER | wx.LEFT, BORDER)

        outer_sizer.Add(recognize_wave_box, 0, wx.EXPAND | wx.ALL, BORDER)
        self.SetSizer(outer_sizer)

        self._aligned_labels = [config_label, engine_label, batch_label, recognize_wave_label]
        self._fit_frame()

    def add_device_panel(self, title):
        """Create and add new Device Panel to self
        :param title: Title for the new panel and label text
        :return: Created Device Panel
        """
        source_label = wx.StaticText(
            self._stream_box.GetStaticBox(), wx.ID_ANY, "{}:".format(title))
        self._stream_sizer.Add(source_label, 0, wx.ALIGN_CENTER)
        self._aligned_labels.append(source_label)

        device_panel = DevicePanel(self._stream_box.GetStaticBox(), title)
        self._stream_sizer.Add(device_panel, 0, wx.EXPAND)
        self._fit_frame()
        return device_panel

    def set_config_choice(self, options, selection):
        """Set configuration choice options and selection
        :param options: List of configurations
        :param selection: List index to select
        """
        set_choice(self._config_choice, options, selection)
        self._on_config_changed()

    def set_engine_choice(self, options, selection):
        """Set inference engine choice options and selection
        :param options: List of inference engines
        :param selection: List index to select
        """
        set_choice(self._engine_choice, options, selection)
        self._on_engine_changed()

    def set_batch_size_choice(self, options, selection):
        """Set batch size choice options and selection
        :param options: List of batch sizes
        :param selection: List index to select
        """
        set_choice(self._batch_choice, options, selection)
        self._on_batch_size_changed()

    @call_after
    def set_wave_path(self, path):
        """Set WAVE file path
        :param path: New path to WAVE file
        """
        self._wave_path_text_ctrl.SetValue(path)

    @call_after
    def enable_config_controls(self, enable=True):
        """Enable configuration controls
        :param enable: Enable if True, disable otherwise
        """
        self._reload_config_button.Enable(enable)
        self._config_choice.Enable(enable)
        self._engine_choice.Enable(enable)
        self._batch_choice.Enable(enable)

    @call_after
    def enable_wave_path_controls(self, enable=True):
        """Enable WAVE path controls
        :param enable: Enable if True, disable otherwise
        """
        self._wave_path_text_ctrl.Enable(enable)
        self._select_wave_button.Enable(enable)

    @call_after
    def enable_recognize_wave_button(self, enable=True):
        """Enable recognize WAVE button
        :param enable: Enable if True, disable otherwise
        """
        self._recognize_wave_button.Enable(enable)

    def set_recognize_wave_button_state(self, state: ButtonState):
        """Set recognize WAVE button state
        :param state: Button state (Enum)
        """
        set_button_state(self._recognize_wave_button, state)

    def _fit_frame(self):
        """Fit items inside the frame, align label widths and set size range"""
        self.SetMaxSize((-1, -1))
        _align_width(self._aligned_labels)
        self.Fit()
        fix_frame_height(self, self._stream_sizer.GetEffectiveRowsCount())
        self.SetMinSize((600, self.GetSize()[1]))
        self.SetMaxSize((-1, self.GetSize()[1]))

    def _on_config_changed(self, _=None):
        """Send PubSub message on config changed"""
        pub.sendMessage(Topic.CONFIG_CHANGED, value=self._config_choice.GetStringSelection())

    @staticmethod
    def _on_reload_config(_):
        """Send PubSub message on reload config"""
        pub.sendMessage(Topic.RELOAD_CONFIG)

    def _on_engine_changed(self, _=None):
        """Send PubSub message on engine changed"""
        pub.sendMessage(Topic.ENGINE_CHANGED, value=self._engine_choice.GetStringSelection())

    def _on_batch_size_changed(self, _=None):
        """Send PubSub message on batch size changed"""
        pub.sendMessage(Topic.BATCH_SIZE_CHANGED,
                        value=int(self._batch_choice.GetStringSelection()))

    def _on_wave_path_changed(self, _):
        """Send PubSub message on WAVE path changed"""
        pub.sendMessage(Topic.WAVE_PATH_CHANGED, value=self._wave_path_text_ctrl.GetValue())

    def _on_select_wave(self, _):
        """Open File Dialog to select WAVE path"""
        wave_path = self._wave_path_text_ctrl.GetValue()
        dialog = wx.FileDialog(self, "Open", os.path.dirname(wave_path),
                               os.path.basename(wave_path), "WAVE files (*.wav)|*.wav",
                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        dialog.ShowModal()
        if dialog.GetPath():
            self._wave_path_text_ctrl.SetValue(dialog.GetPath())
        dialog.Destroy()

    def _on_recognize_wave(self, _):
        """Send PubSub message on recognize WAVE"""
        pub.sendMessage(Topic.RECOGNIZE_WAVE, value=self._recognize_wave_button.GetValue())

    @staticmethod
    def _on_close_window(event):
        """Send PubSub message on close window"""
        pub.sendMessage(Topic.CLOSE_WINDOW)
        event.Skip()


def _align_width(controls):
    """Align widths of given controls
    :param controls: List of controls
    """
    max_width = max(x.GetSize()[0] for x in controls)
    for control in controls:
        control.SetMinSize((max_width, -1))
