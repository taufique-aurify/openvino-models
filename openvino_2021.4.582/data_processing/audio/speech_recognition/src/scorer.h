// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <inference_engine.hpp>
#include <stdint.h>
#include <string>
#include <vector>

#include "speech_library.h"

struct ScorerParameters;

class Scorer
{
public:
    SpeechLibraryStatus Initialize(const ScorerParameters& parameters);
    SpeechLibraryStatus ProcessData(const float* input, float* output, size_t number_of_frames);
    SpeechLibraryStatus Reset();

    size_t input_vector_size()
    {
        return input_vector_size_;
    }

    size_t output_vector_size()
    {
        return output_vector_size_;
    }

    uint32_t batch_size()
    {
        return batch_size_;
    }

    uint32_t subsampling_factor()
    {
        return subsampling_factor_;
    }

private:
    struct InferRequestStruct {
        InferenceEngine::InferRequest infer_request;
        int frame_index;
        uint32_t frames_to_compute_in_this_batch;
    };

    SpeechLibraryStatus LoadInferenceEngine(const std::string& device_name);

    InferenceEngine::Core inference_engine_;
    InferenceEngine::ExecutableNetwork executable_network_;
    InferenceEngine::ConstInputsDataMap c_input_info_;
    InferenceEngine::ConstOutputsDataMap c_output_info_;

    std::vector<InferRequestStruct> infer_requests_;

    std::string device_name_;

    uint32_t batch_size_{ 0 };
    uint32_t context_window_left_{ 0 };
    uint32_t context_window_right_{ 0 };
    size_t input_vector_size_{ 0 };
    size_t output_vector_size_{ 0 };
    uint32_t subsampling_factor_{ 0 };
    bool use_gna_;
    bool use_hetero_;
};
