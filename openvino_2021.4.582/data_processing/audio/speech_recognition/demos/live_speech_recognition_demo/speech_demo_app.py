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
"""Main module"""
import logging
import sys
from multiprocessing import freeze_support

REQUIRED_PYTHON_VERSION = ["3.5", "3.6", "3.7", "3.8"]

if sys.version[0:3] not in REQUIRED_PYTHON_VERSION:
    sys.stdout.write("Error: Detected Python %s which is not supported.\n" % sys.version[0:3])
    sys.stdout.write("   ->  Please install supported version: %s\n" %
                     (", ".join(REQUIRED_PYTHON_VERSION)))
    sys.exit()

import wx

from gui.main_controller import MainController


class SpeechDemoApp(wx.App):
    """Main application class"""
    def OnInit(self):
        """Create application main window"""
        MainController()
        return True


def _initialize_logger():
    """Initialize global logger instance"""
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)-15s [%(levelname)s] %(filename)s::%(funcName)s | "
                                  "%(message)s")

    stdout = logging.StreamHandler(stream=sys.stdout)
    stdout.setLevel(logging.INFO)
    stdout.setFormatter(formatter)

    logger.addHandler(stdout)


if __name__ == '__main__':
    def _run_app():
        freeze_support()

        _initialize_logger()

        app = SpeechDemoApp(0)
        app.MainLoop()

    _run_app()
