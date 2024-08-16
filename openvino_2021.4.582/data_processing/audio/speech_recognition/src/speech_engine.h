// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <atomic>
#include <memory>
#include <string>

#include "speech_library.h"
#include "speech_parameters.h"

class FeatureExtraction;
class Scorer;
class Decoder;

class SpeechEngine
{
public:
    SpeechEngine();
    ~SpeechEngine();

    SpeechLibraryStatus Initialize();

    SpeechLibraryStatus SetParameter(SpeechLibraryParameter parameter,
        const void* value, size_t size);
    SpeechLibraryStatus PushData(const void* data, size_t elements_count,
        SpeechLibraryProcessingInfo* info);
    SpeechLibraryStatus ProcessResidueData(SpeechLibraryProcessingInfo* info);
    SpeechLibraryStatus GetResult(SpeechLibraryResultType result_type,
        char* buffer, size_t buffer_size);
    SpeechLibraryStatus Reset();
    SpeechLibraryStatus ParseConfiguration(const char* configuration_filename);

private:
    static SpeechLibraryStatus ReadBinaryFile(std::string filename, size_t* size,
        std::unique_ptr<uint8_t[]>& data);
    static int ParseBooleanParameter(std::string value);
    SpeechLibraryStatus CheckInferenceParameters();

    std::unique_ptr<SpeechLibraryParameters> parameters_;
    std::string feature_transform_filename_ = "";

    std::unique_ptr<FeatureExtraction> feature_extraction_{ nullptr };
    std::unique_ptr<Scorer> scorer_{ nullptr };
    std::unique_ptr<Decoder> decoder_{ nullptr };

    std::unique_ptr<int8_t[]> feature_buffer_;
    std::unique_ptr<int8_t[]> processing_buffer_;

    std::atomic_bool initialized_{ false };

    size_t processing_chunk_size_in_frames_{ 0 };
};
