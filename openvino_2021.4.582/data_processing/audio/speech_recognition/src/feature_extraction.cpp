// Copyright (C) 2019-2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "feature_extraction.h"

#include <iostream>

#include "logger.h"
#include "speech_parameters.h"
#include "kaldi_component_reader.h"

#define RETURN_ON_FAILURE(routine, parameter_name) \
    rh_status = routine; \
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status) { \
        Logger::Print(LOG_LEVEL_ERROR, "Failed to set '%s'. RH feature extraction status: %d", parameter_name, rh_status); \
        return rh_status; \
    }

FeatureExtraction::FeatureExtraction()
: handle_(nullptr)
, float_feature_buffer_{}
, feature_vector_size_{0}
, use_feature_transformation_(false)
, add_shift_vector_{}
, rescale_vector_{}
{
}

FeatureExtraction::~FeatureExtraction()
{
    Free();
}

SpeechLibraryStatus FeatureExtraction::Initialize(const FeatureExtractionParameters& parameters,
                                                  const char *feature_transform_filename)
{
    if (handle_ != nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to initialize feature extraction instance, invalid state - the handle is not null");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    RhFeatureExtractionStatus rh_status = RhFeatureExtractionCreateInstance(&handle_);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to create feature extraction instance. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    rh_status = SetRhParameters(parameters);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    rh_status = RhFeatureExtractionInitInstance(handle_);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to initialize feature extraction. RH feature extraction status: %d", rh_status);
        Free();
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    SpeechLibraryStatus status = GetFeatureVectorSize(&feature_vector_size_);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    size_t buffer_max_size_in_bytes;
    status = GetOutputBufferMaxSizeInBytes(&buffer_max_size_in_bytes);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    size_t float_feature_buffer_size_in_float_elements =
        buffer_max_size_in_bytes / sizeof(float);
    float_feature_buffer_.reset(new (std::nothrow) float[
        float_feature_buffer_size_in_float_elements]);

    if (nullptr != feature_transform_filename && 0 != feature_transform_filename[0])
    {
        use_feature_transformation_ = true;
        Logger::Print(LOG_LEVEL_INFO, "Using feature transformation %s",
                      feature_transform_filename);

        const char *ADD_SHIFT_COMPONENT_NAME1 = "<AddShift>";
        const char *ADD_SHIFT_COMPONENT_NAME2 = "<addshift>";
        const char *RESCALE_COMPONENT_NAME1 = "<Rescale>";
        const char *RESCALE_COMPONENT_NAME2 = "<rescale>";
        const float kMinFloatValue = -1.0e10;
        const float kMaxFloatValue = 1.0e10;

        status = ReadKaldiVectorComponent(feature_transform_filename,
                                          ADD_SHIFT_COMPONENT_NAME1,
                                          &add_shift_vector_,
                                          kMinFloatValue, kMaxFloatValue);
        if (0 == add_shift_vector_.size())
        {
            status = ReadKaldiVectorComponent(feature_transform_filename,
                                              ADD_SHIFT_COMPONENT_NAME2,
                                              &add_shift_vector_,
                                              kMinFloatValue, kMaxFloatValue);
        }
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }
        if (add_shift_vector_.size() != feature_vector_size_)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Add shift dimension mismatch (%d != %d)",
                          add_shift_vector_.size(), feature_vector_size_);
            return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
        }

        status = ReadKaldiVectorComponent(feature_transform_filename,
                                          RESCALE_COMPONENT_NAME1,
                                          &rescale_vector_,
                                          kMinFloatValue, kMaxFloatValue);
        if (0 == rescale_vector_.size())
        {
            status = ReadKaldiVectorComponent(feature_transform_filename,
                                              RESCALE_COMPONENT_NAME2,
                                              &rescale_vector_,
                                              kMinFloatValue, kMaxFloatValue);
        }
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }
        if (rescale_vector_.size() != feature_vector_size_)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Rescale dimension mismatch (%d != %d)",
                          rescale_vector_.size(), feature_vector_size_);
            return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
        }
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::ProcessData(const void* input_samples,
    size_t input_samples_count, void* output_features, size_t* output_frames_count)
{
    RhFeatureExtractionStatus rh_status = RhFeatureExtractionProcessData(handle_,
        input_samples, input_samples_count, float_feature_buffer_.get(), output_frames_count);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Feature extraction failed to process frame. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    FeatureTransform(output_features, *output_frames_count);
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::GetResidueData(void* output_features,
    size_t* output_frames_count)
{
    RhFeatureExtractionStatus rh_status = RhFeatureExtractionGetResidueData(
        handle_, float_feature_buffer_.get(), output_frames_count);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Feature extraction failed to get residue data. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    FeatureTransform(output_features, *output_frames_count);
    return SPEECH_LIBRARY_SUCCESS;
}

void FeatureExtraction::FeatureTransform(void* output_features, size_t output_frames_count)
{
    float* float_output_features = static_cast<float*>(output_features);

    for (size_t frame_index = 0; frame_index < output_frames_count; ++frame_index)
    {
        for (size_t feature_index = 0; feature_index < feature_vector_size_; ++feature_index)
        {
            // copy float features
            float_output_features[frame_index * feature_vector_size_ + feature_index] =
                float_feature_buffer_[frame_index * feature_vector_size_ + feature_index];
        }
    }

    if (use_feature_transformation_)
    {
        for (size_t frame_index = 0; frame_index < output_frames_count; ++frame_index)
        {
            for (size_t feature_index = 0; feature_index < feature_vector_size_; ++feature_index)
            {
                float_output_features[frame_index * feature_vector_size_ + feature_index] +=
                    add_shift_vector_[feature_index];
                float_output_features[frame_index * feature_vector_size_ + feature_index] *=
                    rescale_vector_[feature_index];
            }
        }
    }
}

void FeatureExtraction::Free()
{
    if (handle_ != nullptr)
    {
        RhFeatureExtractionStatus rh_status = RhFeatureExtractionFreeInstance(handle_);
        if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
        {
            Logger::Print(LOG_LEVEL_ERROR,
                "Failed to free feature extraction. RH feature extraction status: %d", rh_status);
        }
    }
}

RhFeatureExtractionStatus FeatureExtraction::SetRhParameters(
    const FeatureExtractionParameters& input_parameters)
{
    RhFeatureExtractionStatus rh_status;

    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_NUMBER_OF_CEPSTRUMS,
        &input_parameters.number_of_cepstrums, sizeof(int)), "number_of_cepstrums");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_LEFT,
        &input_parameters.context_left, sizeof(int)), "context_left");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_RIGHT,
        &input_parameters.context_right, sizeof(int)), "context_right");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_HPF_BETA,
        &input_parameters.hpf_beta, sizeof(float)), "hpf_beta");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_CEPSTRAL_LIFTER,
        &input_parameters.cepstral_lifter, sizeof(float)), "cepstral_lifter");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_NO_DCT,
        &input_parameters.no_dct, sizeof(int)), "no_dct");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_MAX_CHUNK_SIZE_IN_SAMPLES,
        &input_parameters.max_chunk_size_in_samples, sizeof(int)), "max_chunk_size_in_samples");
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_INPUT_DATA_TYPE,
        &input_parameters.input_data_type, sizeof(int)), "input_data_type");

    // this parameter is not exposed in SpeechLibrary API
    RhFeatureExtractionOutputDataType output_data_type =
        RhFeatureExtractionOutputDataType::RH_FEATURE_EXTRACTION_OUTPUT_DATA_TYPE_FLOAT_32;
    RETURN_ON_FAILURE(RhFeatureExtractionSetParameterValue(handle_, RH_FEATURE_EXTRACTION_PARAMETER_OUTPUT_DATA_TYPE,
        &output_data_type, sizeof(int)), "output_data_type");

    return RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::Reset()
{
    RhFeatureExtractionStatus rh_status = RhFeatureExtractionReset(handle_);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to reset feature extraction. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::GetFeatureVectorSize(size_t* vector_size)
{
    RhFeatureExtractionStatus rh_status = RhFeatureExtractionGetVectorSize(handle_, vector_size);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to get feature vector size. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::GetOutputBufferMaxSizeInBytes(
    size_t* max_buffer_size_in_bytes)
{
    RhFeatureExtractionStatus rh_status = RhFeatureExtractionGetOutputBufferMaxSizeInBytes(
        handle_, max_buffer_size_in_bytes);
    if (RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to get maximum output buffer size. RH feature extraction status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus FeatureExtraction::MapRhStatusToSpeechLibraryStatus(
    RhFeatureExtractionStatus rh_status)
{
    switch (rh_status)
    {
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_SUCCESS:
        return SpeechLibraryStatus::SPEECH_LIBRARY_SUCCESS;
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_ERROR_GENERIC:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_GENERIC;
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_ERROR_OUT_OF_MEMORY:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_OUT_OF_MEMORY;
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_ERROR_INVALID_RESOURCE:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_ERROR_INVALID_PARAM:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    case RhFeatureExtractionStatus::RH_FEATURE_EXTRACTION_ERROR_INVALID_HANDLE_VALUE:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;
    default:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_GENERIC;
    }
}
