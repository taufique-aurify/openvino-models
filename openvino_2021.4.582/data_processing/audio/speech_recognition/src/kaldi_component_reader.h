// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <vector>

#include "speech_library.h"

SpeechLibraryStatus ReadKaldiVectorComponent(const char *filename,
                                             const char *component_name,
                                             std::vector<float> *result,
                                             float min_value,
                                             float max_value);

