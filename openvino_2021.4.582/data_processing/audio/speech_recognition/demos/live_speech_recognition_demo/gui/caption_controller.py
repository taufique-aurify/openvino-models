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
"""Caption Frame Controller module"""
import os.path

from gui.caption_frame import CaptionFrame

LOG_DIR = os.path.join(os.path.pardir, 'log')
CHARACTER_LIMIT = 1000


class CaptionController:
    """Controller for Caption Frame"""
    def __init__(self, frame: CaptionFrame):
        """
        :param frame: Caption Frame
        """
        self._frame = frame

        self._saved_text = ""
        self._spare_length = 0

    def show(self, show):
        """Show Caption Frame
        :param show: Show if True, hide otherwise
        """
        self._frame.show(show)

    def clear_text(self):
        """Clear caption text"""
        self._frame.clear_text()
        self._saved_text = ""
        self._spare_length = 0

    def set_text(self, text, is_final=False):
        """Set caption text
        :param text: Current utterance text
        :param is_final: It's the final form of current utterance if True
        """
        if not text:
            return
        output_text = (self._saved_text + text)[self._spare_length:]
        if len(output_text) > CHARACTER_LIMIT:
            first_line_length = self._frame.get_line_length(0)
            if output_text[first_line_length] == "\n":
                first_line_length += 1
            self._spare_length += first_line_length
            output_text = output_text[first_line_length:]

        self._frame.set_text(output_text.strip())
        if is_final:
            self._saved_text = output_text + "\n"
            self._spare_length = 0

    def show_clipping_indicator(self, show):
        """Show clipping indicator on the frame
        :param show: Show if True, hide otherwise
        """
        self._frame.show_clipping_indicator(show)
