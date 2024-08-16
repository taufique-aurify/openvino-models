// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <stdint.h>
#include <string>
#include <speech_decoder.h>

#include "speech_library.h"

struct DecoderParameters;

class Decoder
{
public:
    Decoder();
    virtual ~Decoder();

    SpeechLibraryStatus Initialize(size_t score_vector_size, const DecoderParameters& parameters);
    SpeechLibraryStatus ProcessData(const float* acoustic_score_vector,
        size_t number_of_frames, SpeechLibraryProcessingInfo* info);
    SpeechLibraryStatus GetResult(SpeechLibraryResultType result_type, char* result, size_t size);
    SpeechLibraryStatus Reset();

    uint32_t subsampling_factor()
    {
        return subsampling_factor_;
    }
private:
    RhDecoderStatus SetRhParameters(const DecoderParameters& input_parameters);
    SpeechLibraryStatus DecodeFrame(const float* acoustic_score_vector, RhDecoderInfo& rh_info);
    void Free();

    SpeechLibraryStatus MapRhStatusToSpeechLibraryStatus(RhDecoderStatus rh_status);
    RhDecoderResultType MapSpeechLibraryResultTypeToRhResultType(SpeechLibraryResultType type);

    RhDecoderInstanceHandle handle_ = nullptr;
    size_t score_vector_size_{ 0 };
    uint32_t subsampling_factor_{ 0 };
};
