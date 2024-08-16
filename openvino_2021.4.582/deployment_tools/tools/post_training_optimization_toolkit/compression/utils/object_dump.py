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
import builtins
import collections
import datetime
import pickle

import io
import numpy
import numpy.core.multiarray
import hyperopt.base
import hyperopt.pyll.base


def object_dump(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

def object_dumps(obj):
    return pickle.dumps(obj)

def object_load(filename):
    with open(filename, 'rb') as f:
        return _SafeUnpickler(f).load()

def object_loads(obj):
    f = io.BytesIO(obj)
    return _SafeUnpickler(f).load()

class _SafeUnpickler(pickle.Unpickler):
    """Safe unpickler forbidding globals functions and classess
        """

    def find_class(self, module, name):
        secure_class = None
        # Only allow secure classes
        if module == 'builtins' and name == 'set':
            secure_class = getattr(builtins, name)
        if module == 'collections':
            secure_class = getattr(collections, name)
        if module == 'datetime':
            secure_class = getattr(datetime, name)
        if module == 'numpy' and name in ['dtype', 'ndarray']:
            secure_class = getattr(numpy, name)
        if module == 'numpy.core.multiarray' and name in ['scalar', '_reconstruct']:
            secure_class = getattr(numpy.core.multiarray, name)
        if module == 'hyperopt.base' and name == 'Trials':
            secure_class = getattr(hyperopt.base, name)
        if module == 'hyperopt.pyll.base' and name in ['Apply', 'Literal']:
            secure_class = getattr(hyperopt.pyll.base, name)
        if secure_class:
            return secure_class
        raise pickle.UnpicklingError(
            'global "%s.%s" is forbidden' % (module, name))
