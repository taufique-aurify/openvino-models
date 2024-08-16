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

class Telemetry():
    """
    Stab file for the Telemetry class which is used when Telemetry class is not available.
    """

    def __init__(self, *arg, **kwargs):
        pass

    def send_event(self, *arg, **kwargs):
        pass

    def send_error(self, *arg, **kwargs):
        pass

    def start_session(self, *arg, **kwargs):
        pass

    def end_session(self, *arg, **kwargs):
        pass

    def force_shutdown(self, *arg, **kwargs):
        pass

    def send_stack_trace(self, *arg, **kwargs):
        pass
