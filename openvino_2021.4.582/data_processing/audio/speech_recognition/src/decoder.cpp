// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "decoder.h"

#include <iostream>

#include "logger.h"
#include "speech_parameters.h"


#define RETURN_ON_FAILURE(routine, parameter_name) \
    rh_status = routine; \
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status) { \
        Logger::Print(LOG_LEVEL_ERROR, "Failed to set '%s'. RH decoder status: %d", parameter_name, rh_status); \
        return rh_status; \
    }

Decoder::Decoder()
{
}

Decoder::~Decoder()
{
    Free();
}

SpeechLibraryStatus Decoder::Initialize(size_t score_vector_size, const DecoderParameters& parameters)
{
    if (handle_ != nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to initialize decoder instance, invalid state - the handle is not null");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    score_vector_size_ = score_vector_size;

    RhDecoderStatus rh_status = RhDecoderCreateInstance(&handle_);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to create decoder instance. RH decoder status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    rh_status = SetRhParameters(parameters);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    if (parameters.hmm_model_data != nullptr)
    {
        rh_status = RhDecoderSetupResource(handle_, RhResourceType::HMM,
            static_cast<const uint8_t*>(parameters.hmm_model_data.get()),
            parameters.hmm_model_size);
        if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Failed to load HMM model");
            Free();
            return MapRhStatusToSpeechLibraryStatus(rh_status);
        }
    }

    rh_status = RhDecoderSetupResource(handle_, RhResourceType::PRONUNCIATION_MODEL,
        static_cast<const uint8_t*>(parameters.pronunciation_model_data.get()),
        parameters.pronunciation_model_size);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to load pronunciation model");
        Free();
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    if (parameters.language_model_data != nullptr)
    {
        rh_status = RhDecoderSetupResource(handle_, RhResourceType::LANGUAGE_MODEL,
            static_cast<const uint8_t*>(parameters.language_model_data.get()),
            parameters.language_model_size);
        if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Failed to load language model");
            Free();
            return MapRhStatusToSpeechLibraryStatus(rh_status);
        }
    }

    rh_status = RhDecoderSetupResource(handle_, RhResourceType::LABELS,
        static_cast<const uint8_t*>(parameters.labels_data.get()),
        parameters.labels_size);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to load labels");
        Free();
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    rh_status = RhDecoderInitInstance(handle_);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to initialize decoder. RH decoder status: %d", rh_status);
        Free();
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus Decoder::ProcessData(const float* acoustic_score_vector,
    size_t number_of_frames, SpeechLibraryProcessingInfo* info)
{
    const float* score_vector_index = acoustic_score_vector;

    for (size_t i = 0; i < number_of_frames; ++i)
    {
        RhDecoderInfo rh_info;
        auto status = DecodeFrame(score_vector_index, rh_info);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }

        score_vector_index += score_vector_size_;

        info->has_speech_started = rh_info.has_speech_started;
        info->is_result_stable = rh_info.is_result_stable;
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus Decoder::DecodeFrame(const float* acoustic_score_vector,
    RhDecoderInfo& rh_info)
{
    RhDecoderStatus rh_status = RhDecoderProcessFrame(handle_,
        acoustic_score_vector, score_vector_size_, &rh_info);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Decoder failed to process frame. RH decoder status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus Decoder::GetResult(SpeechLibraryResultType result_type,
    char* result, size_t size)
{
    RhDecoderStatus rh_status = RhDecoderGetResult(handle_,
        MapSpeechLibraryResultTypeToRhResultType(result_type), result, size);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to get speech recognition result. RH decoder status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }
    return SPEECH_LIBRARY_SUCCESS;
}

void Decoder::Free()
{
    if (handle_ != nullptr)
    {
        RhDecoderStatus rh_status = RhDecoderFreeInstance(handle_);
        if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
        {
            Logger::Print(LOG_LEVEL_ERROR,
                "Failed to free decoder. RH decoder status: %d", rh_status);
        }
    }
}

RhDecoderStatus Decoder::SetRhParameters(const DecoderParameters& input_parameters)
{
    RhDecoderStatus rh_status;

    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_ACOUSTIC_SCORE_VECTOR_SIZE,
        &score_vector_size_, sizeof(int)), "score_vector_size");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_ACOUSTIC_SCALE_FACTOR,
        &input_parameters.acoustic_scale_factor, sizeof(float)), "acoustic_scale_factor");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_BEAM_WIDTH,
        &input_parameters.beam_width, sizeof(float)), "beam_width");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_LATTICE_BEAM_WIDTH,
        &input_parameters.lattice_beam_width, sizeof(float)), "lattice_beam_width");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_NBEST,
        &input_parameters.n_best, sizeof(int)), "n_best");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_CONFIDENCE_ACOUSTIC_SCALE_FACTOR,
        &input_parameters.confidence_acoustic_scale_factor, sizeof(float)), "confidence_acoustic_scale_factor");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_CONFIDENCE_LM_SCALE_FACTOR,
        &input_parameters.confidence_lm_scale_factor, sizeof(float)), "confidence_lm_scale_factor");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TOKEN_BUFFER_SIZE,
        &input_parameters.token_buffer_size, sizeof(int)), "token_buffer_size");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TRACE_BACK_LOG_SIZE,
        &input_parameters.trace_back_log_size, sizeof(int)), "trace_back_log_size");

    auto min_stable_frames = input_parameters.min_stable_frames;
    if (input_parameters.subsampling_factor > 1)
    {
        min_stable_frames /= input_parameters.subsampling_factor;
    }
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_MIN_STABLE_FRAMES,
        &min_stable_frames, sizeof(int)), "min_stable_frames");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TOKEN_BUFFER_FILL_THRESHOLD,
        &input_parameters.token_buffer_fill_threshold, sizeof(float)), "token_buffer_fill_threshold");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TOKEN_BUFFER_MAX_FILL,
        &input_parameters.token_buffer_max_fill, sizeof(float)), "token_buffer_max_fill");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TOKEN_BUFFER_MAX_AVG_FILL,
        &input_parameters.token_buffer_max_avg_fill, sizeof(float)), "token_buffer_max_avg_fill");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_TOKEN_BUFFER_MIN_FILL,
        &input_parameters.token_buffer_min_fill, sizeof(float)), "token_buffer_min_fill");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_PRUNING_TIGHTENING_DELTA,
        &input_parameters.pruning_tightening_delta, sizeof(float)), "pruning_tightening_delta");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_PRUNING_RELAXATION_DELTA,
        &input_parameters.pruning_relaxation_delta, sizeof(float)), "pruning_relaxation_delta");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_USE_SCORE_TREND_FOR_ENDPOINTING,
        &input_parameters.use_score_trend_for_endpointing, sizeof(int)), "use_score_trend_for_endpointing");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_G_CACHE_LOG_SIZE,
        &input_parameters.g_cache_log_size, sizeof(int)), "g_cache_log_size");
    RETURN_ON_FAILURE(RhDecoderSetParameterValue(handle_, RH_DECODER_RESULT_FORMAT,
        &input_parameters.result_format_type, sizeof(int)), "result_format");

    return RhDecoderStatus::RH_DECODER_SUCCESS;
}

SpeechLibraryStatus Decoder::Reset()
{
    RhDecoderStatus rh_status = RhDecoderReset(handle_);
    if (RhDecoderStatus::RH_DECODER_SUCCESS != rh_status)
    {
        Logger::Print(LOG_LEVEL_ERROR,
            "Failed to reset decoder. RH decoder status: %d", rh_status);
        return MapRhStatusToSpeechLibraryStatus(rh_status);
    }
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus Decoder::MapRhStatusToSpeechLibraryStatus(RhDecoderStatus rh_status)
{
    switch (rh_status)
    {
    case RhDecoderStatus::RH_DECODER_SUCCESS:
        return SpeechLibraryStatus::SPEECH_LIBRARY_SUCCESS;
    case RhDecoderStatus::RH_DECODER_ERROR_GENERIC:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_GENERIC;
    case RhDecoderStatus::RH_DECODER_ERROR_OUT_OF_MEMORY:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_OUT_OF_MEMORY;
    case RhDecoderStatus::RH_DECODER_ERROR_INVALID_RESOURCE:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    case RhDecoderStatus::RH_DECODER_ERROR_INVALID_PARAM:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    case RhDecoderStatus::RH_DECODER_ERROR_INVALID_HANDLE_VALUE:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;
    default:
        return SpeechLibraryStatus::SPEECH_LIBRARY_ERROR_GENERIC;
    }
}

RhDecoderResultType Decoder::MapSpeechLibraryResultTypeToRhResultType(
    SpeechLibraryResultType type)
{
    switch (type)
    {
    case SpeechLibraryResultType::SPEECH_LIBRARY_RESULT_TYPE_PARTIAL:
        return RhDecoderResultType::RH_DECODER_PARTIAL_RESULT;
    case SpeechLibraryResultType::SPEECH_LIBRARY_RESULT_TYPE_PREVIEW:
        return RhDecoderResultType::RH_DECODER_PREVIEW_RESULT;
    case SpeechLibraryResultType::SPEECH_LIBRARY_RESULT_TYPE_FINAL:
        return RhDecoderResultType::RH_DECODER_FINAL_RESULT;
    default:
        return RhDecoderResultType::RH_DECODER_FINAL_RESULT;
    }
}
