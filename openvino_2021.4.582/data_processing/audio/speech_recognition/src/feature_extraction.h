// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <memory>
#include <stdint.h>
#include <speech_feature_extraction.h>
#include <vector>

#include "speech_library.h"

struct FeatureExtractionParameters;

class FeatureExtraction
{
public:
    FeatureExtraction();
    virtual ~FeatureExtraction();

    SpeechLibraryStatus Initialize(const FeatureExtractionParameters& parameters,
        const char *feature_transform_filename);
    SpeechLibraryStatus ProcessData(const void* input_samples, size_t input_samples_count,
        void* output_features, size_t* output_frames_count);
    SpeechLibraryStatus GetResidueData(void* output_features, size_t* output_frames_count);
    SpeechLibraryStatus Reset();
    SpeechLibraryStatus GetFeatureVectorSize(size_t* vector_size);
    SpeechLibraryStatus GetOutputBufferMaxSizeInBytes(size_t* max_buffer_size_in_bytes);

private:
    // W/A - currently the feature transform is done programatically, plus int16 -> float conversion
    void FeatureTransform(void* output_features, size_t output_frames_count);
    RhFeatureExtractionStatus SetRhParameters(const FeatureExtractionParameters& input_parameters);
    void Free();

    SpeechLibraryStatus MapRhStatusToSpeechLibraryStatus(RhFeatureExtractionStatus rh_status);

    RhFeatureExtractionInstanceHandle handle_ = nullptr;
    std::unique_ptr<float[]> float_feature_buffer_;
    size_t feature_vector_size_{ 0 };

    // Optional feature transformation
    bool use_feature_transformation_ = false;
    std::vector<float> add_shift_vector_;
    std::vector<float> rescale_vector_;
};
