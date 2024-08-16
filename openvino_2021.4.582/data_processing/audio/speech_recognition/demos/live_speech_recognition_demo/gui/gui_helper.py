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
"""Helper module with shared GUI functions"""
import functools
import os

import wx

BORDER = 3


def call_after(function):
    """Decorator for convenient usage of wx.CallAfter() function
    :param function: Wrapped function
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return wx.CallAfter(function, *args, **kwargs)
    return wrapper


@call_after
def show_warning_message(message):
    """Show warning message box on the screen
    :param message: Message text to display
    """
    wx.MessageBox(message, "Warning", wx.OK | wx.ICON_WARNING)


def fix_frame_height(frame: wx.Frame, flex_rows=0):
    """Fix frame height on Ubuntu
    :param frame: Frame to be fixed
    :param flex_rows: Number of FLex Grid Sizer rows in the frame
    """
    height = frame.GetSizer().GetMinSize()[1] + (0 if os.name == 'nt' else flex_rows * BORDER)
    frame.SetClientSize((frame.GetSize()[0], height))

def is_ascii(text):
    """Determine whether a string contains only ASCII characters
    :param text: Character string to check
    """
    return all(ord(character) < 128 and ord(character) > 0 for character in text)
