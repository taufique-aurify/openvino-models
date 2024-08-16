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

try:
    import jstyleson as json
except ImportError:
    import json
from pathlib import Path
import yaml


def read_config_from_file(path):
    path = Path(path)
    extension = path.suffix.lower()
    with path.open() as f:
        if extension in ('.yaml', '.yml'):
            return yaml.load(f, Loader=yaml.SafeLoader)
        if extension in ('.json',):
            return json.load(f)
        raise RuntimeError('Unknown file extension for the file "{}"'.format(path))


def write_config_to_file(data, path):
    path = Path(path)
    extension = path.suffix.lower()
    with path.open('w') as f:
        if extension in ('.yaml', '.yml'):
            yaml.dump(data, f)
        elif extension in ('.json',):
            json.dump(data, f)
        else:
            raise RuntimeError('Unknown file extension for the file "{}"'.format(path))
