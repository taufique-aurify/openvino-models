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
"""Caption Frame module"""
import wx
import wx.lib.buttons as buttons
import wx.lib.resizewidget as rw
from wx.lib.pubsub import pub

from gui.gui_helper import call_after, fix_frame_height

TEXT_CTRL_SIZE = (700, 100)
FONT_SIZE = 18
BUTTON_HEIGHT = 20
BACKGROUND_COLOR = 'gray'
FOREGROUND_COLOR = 'white'
BUTTON_COLOR = wx.Colour(100, 100, 100)
CLIPPING_COLOR = wx.Colour(255, 107, 104)


class CaptionTopic:
    """Caption Frame topic for PubSub"""
    HIDE = "caption_hide"
    CLEAR = "caption_clear"


class CaptionFrame(wx.Frame):
    """Caption Frame"""
    def __init__(self, parent, id_=wx.ID_ANY, title="", position=0):
        """
        :param parent: Parent window
        :param id_: Frame ID
        :param title: Title
        :param position: Starting position of the frame (0: base, -1: above the base)
        """
        super().__init__(parent, id_, title,
                         style=wx.STAY_ON_TOP | wx.FRAME_TOOL_WINDOW | wx.FRAME_NO_TASKBAR)
        self._title = title

        self._start_pos = None
        self._window_pos = None

        self._base_font = wx.Font(FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                                  wx.FONTWEIGHT_NORMAL)

        if self.CanSetTransparent:
            self.SetTransparent(230)

        self.SetBackgroundColour(BACKGROUND_COLOR)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self._create_button("×", "Hide Caption Frame", self._on_hide))
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self._create_button("clear", "Clear text", self._on_clear, 12))
        header_sizer.Add(button_sizer, 0, wx.EXPAND)

        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_text = wx.StaticText(self, wx.ID_ANY, title)
        title_text.SetFont(self._base_font)
        title_text.SetForegroundColour(FOREGROUND_COLOR)
        self._bind_mouse_events(title_text)
        title_sizer.Add(title_text, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)
        header_sizer.Add(title_sizer, 1, wx.EXPAND)

        clipping_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._clipping_text = wx.StaticText(self, wx.ID_ANY, "Clipping!")
        self._clipping_text.SetFont(self._create_font(12, wx.FONTWEIGHT_BOLD))
        self._clipping_text.SetForegroundColour(CLIPPING_COLOR)
        self._bind_mouse_events(self._clipping_text)
        clipping_sizer.Add(self._clipping_text)
        clipping_sizer.Add(0, BUTTON_HEIGHT)
        self._clipping_text.Show(False)
        header_sizer.Add(clipping_sizer, 0, wx.ALIGN_CENTER)
        sizer.Add(header_sizer, 0, wx.EXPAND)

        text_panel = wx.Panel(self)
        text_panel.SetDoubleBuffered(True)
        text_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._text_ctrl = wx.TextCtrl(text_panel, wx.ID_ANY, "", size=TEXT_CTRL_SIZE,
                                      style=wx.TE_READONLY | wx.TE_MULTILINE | wx.SUNKEN_BORDER)
        self._text_ctrl.SetFont(self._base_font)
        self._text_ctrl.SetBackgroundColour(BACKGROUND_COLOR)
        self._text_ctrl.SetForegroundColour(FOREGROUND_COLOR)

        resize = rw.ResizeWidget(self)
        resize.SetManagedChild(text_panel)
        text_panel.SetMinSize((60, 60))
        self.Bind(rw.EVT_RW_LAYOUT_NEEDED, self._on_layout_needed)

        text_panel_sizer.Add(self._text_ctrl, 1, wx.EXPAND)
        text_panel.SetSizer(text_panel_sizer)
        sizer.Add(resize, 1, wx.EXPAND)

        self._bind_mouse_events(self)
        self.SetSizer(sizer)
        self.Fit()
        fix_frame_height(self)

        display_size = wx.GetDisplaySize()
        self.SetPosition((display_size[0]/2 - self.GetSize()[0] + TEXT_CTRL_SIZE[0]/2,
                          display_size[1]*7/8 - self.GetSize()[1]/2 + position * TEXT_CTRL_SIZE[1]))

    @call_after
    def show(self, show):
        """Show Caption Frame
        :param show: Show if True, hide otherwise
        """
        self.Show(show)

    @call_after
    def clear_text(self):
        """Clear caption text"""
        self._text_ctrl.SetValue("")

    @call_after
    def set_text(self, text):
        """Set caption text
        :param text: Full text to set
        """
        self._text_ctrl.Freeze()
        self._text_ctrl.ChangeValue(text.strip())
        self._text_ctrl.ShowPosition(self._text_ctrl.GetLastPosition())
        self._text_ctrl.Thaw()

    @call_after
    def show_clipping_indicator(self, show):
        """Show clipping indicator on the frame
        :param show: Show if True, hide otherwise
        """
        self._clipping_text.Show(show)
        self.Layout()

    def get_line_length(self, line_no):
        """Return length of the specified line
        :param line_no: Line number
        """
        return self._text_ctrl.GetLineLength(line_no)

    def _bind_mouse_events(self, control: wx.Window):
        """Bind mouse drag&drop events to given window element
        :param control: Window element
        """
        control.Bind(wx.EVT_LEFT_DOWN, self._on_mouse_left_down)
        control.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        control.Bind(wx.EVT_LEFT_UP, self._on_mouse_left_up)

    def _on_mouse_left_down(self, evt):
        """Save starting position of drag&drop
        :param evt: Event
        """
        self.Refresh()
        self._start_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self._window_pos = self.ClientToScreen((0, 0))
        self.CaptureMouse()

    def _on_mouse_motion(self, evt):
        """Move frame during drag&drop
        :param evt: Event
        """
        if evt.Dragging() and evt.LeftIsDown() and self.HasCapture():
            drag_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            new_pos = (self._window_pos.x + (drag_pos.x - self._start_pos.x),
                       self._window_pos.y + (drag_pos.y - self._start_pos.y))
            self.Move(new_pos)

    def _on_mouse_left_up(self, _):
        """Finish drag&drop"""
        if self.HasCapture():
            self.ReleaseMouse()

    def _on_layout_needed(self, _):
        """Fit frame elements after resizing"""
        self.Fit()

    def _on_hide(self, _):
        """Send PubSub message on Caption Frame hide"""
        pub.sendMessage(self._format_topic(CaptionTopic.HIDE))

    def _on_clear(self, _):
        """Send PubSub message on Caption Frame clear"""
        pub.sendMessage(self._format_topic(CaptionTopic.CLEAR))

    def _format_topic(self, topic):
        """Return PubSub topic specific for this instance
        :param topic: PubSub topic name
        """
        return '{}_{}'.format(topic, self._title)

    def _create_button(self, label, tooltip, event_handler, font_size=FONT_SIZE):
        """Return generic button with given properties
        :param label: Button's label text
        :param tooltip: Tooltip text
        :param event_handler: On-click event handler
        :param font_size: Label text font size
        """
        button = buttons.GenButton(self, wx.ID_ANY, label, style=wx.BORDER_NONE | wx.BU_EXACTFIT)
        button.SetMaxSize((-1, BUTTON_HEIGHT))
        button.SetFont(self._create_font(font_size))
        button.SetBackgroundColour(BUTTON_COLOR)
        button.SetForegroundColour(FOREGROUND_COLOR)
        button.SetToolTip(wx.ToolTip(tooltip))
        button.Bind(wx.EVT_BUTTON, event_handler)
        return button

    def _create_font(self, size=FONT_SIZE, weight=wx.FONTWEIGHT_NORMAL):
        """Return font with given properties
        :param size: Font size
        :param weight: Font weight
        """
        font = wx.Font(self._base_font)
        font.SetPointSize(size)
        font.SetWeight(weight)
        return font
