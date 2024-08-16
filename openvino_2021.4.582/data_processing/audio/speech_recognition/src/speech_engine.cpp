// Copyright (C) 2019-2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//
#ifdef __STDC_LIB_EXT1__
#define __STDC_WANT_LIB_EXT1__ 1
#endif


#include "speech_engine.h"

#include <fstream>
#include <iostream>
#include "logger.h"
#include "decoder.h"
#include "feature_extraction.h"
#include "scorer.h"
#include "speech_library.h"


SpeechEngine::SpeechEngine()
{
}

SpeechEngine::~SpeechEngine()
{
}

SpeechLibraryStatus SpeechEngine::Initialize()
{
    feature_extraction_.reset(new FeatureExtraction());
    scorer_.reset(new Scorer());
    decoder_.reset(new Decoder());

    SpeechLibraryStatus status;

    try
    {
        status = feature_extraction_->Initialize(parameters_->feature_extraction_parameters,
                                                 feature_transform_filename_.c_str());
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }

        status = scorer_->Initialize(parameters_->scorer_parameters);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }

        auto score_vector_size = scorer_->output_vector_size();

        status = decoder_->Initialize(score_vector_size, parameters_->decoder_parameters);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }
    }
    catch (const std::exception &error)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to initialize due to: %s", error.what());
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }
    catch (...)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to initialize due to: unknown/internal exception");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    // with regards to feature extraction library output data type (INT16)
    size_t buffer_max_size_in_bytes;
    status = feature_extraction_->GetOutputBufferMaxSizeInBytes(&buffer_max_size_in_bytes);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    // Adjust properly size of feature buffer because this buffer (in SpeechEngine class) is
    // using FLOAT and feature extraction library output datatype is INT16
    size_t float_buffer_max_size_in_bytes = buffer_max_size_in_bytes /
        sizeof(int16_t) * sizeof(float);

    feature_buffer_.reset(new (std::nothrow) int8_t[float_buffer_max_size_in_bytes]);

    processing_chunk_size_in_frames_ = scorer_->batch_size();

    size_t procesing_buffer_size_in_bytes =
        processing_chunk_size_in_frames_ * scorer_->output_vector_size() * sizeof(float);
    processing_buffer_.reset(new (std::nothrow) int8_t[procesing_buffer_size_in_bytes]);

    initialized_ = true;
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechEngine::SetParameter(SpeechLibraryParameter parameter,
    const void* value, size_t size)
{
    if (!initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to set parameter. Speech library instance is not initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    bool value_changed = false;

    switch (parameter)
    {
    case SpeechLibraryParameter::SPEECH_LIBRARY_PARAMETER_INFERENCE_BATCH_SIZE:
    {
        if (size != sizeof(int))
        {
            Logger::Print(LOG_LEVEL_ERROR,
                "Failed to set parameter. Invalid size for parameter 'batch_size'. Expected: %zu", sizeof(int));
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        auto old_value = parameters_->scorer_parameters.batch_size;
        parameters_->scorer_parameters.batch_size = *(reinterpret_cast<const int*>(value));

        value_changed = (old_value != parameters_->scorer_parameters.batch_size);
        break;
    }
    case SpeechLibraryParameter::SPEECH_LIBRARY_PARAMETER_INFERENCE_DEVICE:
    {
        if (size < 1 || size > 64)
        {
            Logger::Print(LOG_LEVEL_ERROR,
                "Failed to set parameter. Invalid size for parameter 'inference_engine'. Expected maximum 64.");
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        const char* char_value = reinterpret_cast<const char*>(value);
        if (char_value[size - 1] != '\0')
        {
            Logger::Print(LOG_LEVEL_ERROR, "Inference device name must be null-terminated ('\0')");
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        auto old_value = parameters_->scorer_parameters.infer_device;
        parameters_->scorer_parameters.infer_device =
            std::string(char_value, char_value + size - 1);  // minus one to not include null-termination char

        value_changed = (old_value != parameters_->scorer_parameters.infer_device);
        break;
    }

    default:
        Logger::Print(LOG_LEVEL_ERROR, "Unsupported parameter.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    return value_changed ? Initialize() : SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechEngine::PushData(const void* data, size_t elements_count,
    SpeechLibraryProcessingInfo* info)
{
    if (!initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to push data. Speech library instance is not initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    if (data == nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to push data. Data parameter is null.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    if (info == nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to push data. Processing info parameter is null.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    size_t frame_index = 0;
    size_t frames_computed = 0;

    try
    {
        auto status = feature_extraction_->ProcessData(
            data, elements_count, feature_buffer_.get(), &frames_computed);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }

        size_t chunk_size_in_this_iteration_in_frames = ((std::min)(
            processing_chunk_size_in_frames_, frames_computed));

        // if subsampling requested bypass batching
        if (parameters_->scorer_parameters.subsampling_factor > 0 || parameters_->decoder_parameters.subsampling_factor > 0)
        {
            chunk_size_in_this_iteration_in_frames = 1;
        }
        const float* data_index = reinterpret_cast<const float*>(feature_buffer_.get());

        while (frame_index < frames_computed)
        {
            if (frame_index + chunk_size_in_this_iteration_in_frames > frames_computed)
            {
                chunk_size_in_this_iteration_in_frames = frames_computed - frame_index;
            }

            if ((parameters_->scorer_parameters.subsampling_factor > 0) &&
                (0 == (frame_index % parameters_->scorer_parameters.subsampling_factor)) ||
                (parameters_->scorer_parameters.subsampling_factor == 0))
            {
                status = scorer_->ProcessData(data_index, reinterpret_cast<float*>(processing_buffer_.get()),
                    chunk_size_in_this_iteration_in_frames);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }

            if ((parameters_->decoder_parameters.subsampling_factor > 0) &&
                (0 == (frame_index % parameters_->decoder_parameters.subsampling_factor)) ||
                (parameters_->decoder_parameters.subsampling_factor == 0))
            {
                status = decoder_->ProcessData(reinterpret_cast<float*>(processing_buffer_.get()),
                    chunk_size_in_this_iteration_in_frames, info);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }

            frame_index += chunk_size_in_this_iteration_in_frames;
            data_index += chunk_size_in_this_iteration_in_frames * scorer_->input_vector_size();
        }
    }
    catch (const std::exception &error)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to push data due to: %s", error.what());
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }
    catch (...)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to push data due to: unknown/internal exception");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechEngine::ProcessResidueData(SpeechLibraryProcessingInfo* info)
{
    if (!initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to process residue data. Speech library instance is not initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    if (info == nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to process residue data. Processing info parameter is null.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    size_t frame_index = 0;
    size_t frames_computed = 0;

    try
    {
        auto status = feature_extraction_->GetResidueData(feature_buffer_.get(), &frames_computed);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            return status;
        }

        size_t chunk_size_in_this_iteration_in_frames = ((std::min)(
            processing_chunk_size_in_frames_, frames_computed));
        if (parameters_->scorer_parameters.subsampling_factor > 0 || parameters_->decoder_parameters.subsampling_factor > 0)
        {
            chunk_size_in_this_iteration_in_frames = 1;
        }

        const float* data_index = reinterpret_cast<const float*>(feature_buffer_.get());

        while (frame_index < frames_computed)
        {
            if (frame_index + chunk_size_in_this_iteration_in_frames > frames_computed)
            {
                chunk_size_in_this_iteration_in_frames = frames_computed - frame_index;
            }

            if ((parameters_->scorer_parameters.subsampling_factor > 0) &&
                (0 == (frame_index % parameters_->scorer_parameters.subsampling_factor)) ||
                (parameters_->scorer_parameters.subsampling_factor == 0))
            {
                status = scorer_->ProcessData(data_index, reinterpret_cast<float*>(processing_buffer_.get()),
                    chunk_size_in_this_iteration_in_frames);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }

            if ((parameters_->decoder_parameters.subsampling_factor > 0) &&
                (0 == (frame_index % parameters_->decoder_parameters.subsampling_factor)) ||
                (parameters_->decoder_parameters.subsampling_factor == 0))
            {
                status = decoder_->ProcessData(reinterpret_cast<float*>(processing_buffer_.get()),
                    chunk_size_in_this_iteration_in_frames, info);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }

            frame_index += chunk_size_in_this_iteration_in_frames;
            data_index += chunk_size_in_this_iteration_in_frames * scorer_->input_vector_size();
        }
    }
    catch (const std::exception &error)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to process residue data due to: %s", error.what());
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }
    catch (...)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to process residue data due to: unknown/internal exception");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechEngine::GetResult(SpeechLibraryResultType result_type,
    char* buffer, size_t buffer_size)
{
    if (!initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to get result. Speech library instance is not initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    if (buffer == nullptr)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to get result. Buffer parameter is null.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    return decoder_->GetResult(result_type, buffer, buffer_size);
}

SpeechLibraryStatus SpeechEngine::Reset()
{
    if (!initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to reset. Speech library instance is not initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    auto status = feature_extraction_->Reset();
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    status = scorer_->Reset();
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    return decoder_->Reset();
}

// Returns true if an UTF-8 string only consists of ASCII characters
static bool IsASCII(std::string text)
{
    for (std::string::const_iterator it = text.cbegin(); it != text.cend(); ++it)
    {
        const unsigned char kMinASCII = 1;
        const unsigned char kMaxASCII = 127;

        unsigned char character = static_cast<unsigned char>(*it);
        if (character < kMinASCII || character > kMaxASCII)
        {
            return false;
        }
    }

    return true;
}

SpeechLibraryStatus SpeechEngine::CheckInferenceParameters()
{
    const unsigned int kMaxBatchSize = 256;
    if (parameters_->scorer_parameters.batch_size > kMaxBatchSize)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Invalid inference batch size (maximum %u): %u",
                      kMaxBatchSize, parameters_->scorer_parameters.batch_size);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    const unsigned int kMaxContextWindowLeft = 256;
    if (parameters_->scorer_parameters.context_window_left > kMaxContextWindowLeft)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Invalid inference left context (maximum %u): %u",
                      kMaxContextWindowLeft, parameters_->scorer_parameters.context_window_left);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    const unsigned int kMaxContextWindowRight = 256;
    if (parameters_->scorer_parameters.context_window_right > kMaxContextWindowRight)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Invalid inference right context (maximum %u): %u",
                      kMaxContextWindowRight, parameters_->scorer_parameters.context_window_right);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    const unsigned int kMaxNumThreads = 4096;
    const unsigned int kMinNumThreads = 1;
    if (parameters_->scorer_parameters.infer_num_threads > kMaxNumThreads ||
        parameters_->scorer_parameters.infer_num_threads < kMinNumThreads)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Invalid inference number of threads (valid range %u..%u): %u",
                      kMinNumThreads, kMaxNumThreads, parameters_->scorer_parameters.infer_num_threads);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechEngine::ParseConfiguration(const char* configuration_filename)
{
    if (initialized_)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Speech library instance is already initialized.");
        return SPEECH_LIBRARY_ERROR_INVALID_STATE;
    }

    std::ifstream file(configuration_filename);

    if (!file.is_open())
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to open configuration file: %s", configuration_filename);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    parameters_.reset(new SpeechLibraryParameters());

    std::string line;

    while (std::getline(file, line))
    {
        std::istringstream line_stream(line);
        line.erase(std::find_if(line.rbegin(), line.rend(), [](int ch) {
            return !std::isspace(ch);
        }).base(), line.end());

        // empty line and comment is a valid case
        if (line.empty() || line.rfind("#", 0) == 0)
        {
            continue;
        }

        if (!IsASCII(line))
        {
            Logger::Print(LOG_LEVEL_ERROR, "Non-ASCII character found in configuration file %s: '%s'",
                          configuration_filename, line.c_str());
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        const char COLUMN_SEPARATOR = ' ';

        if (line.find(COLUMN_SEPARATOR) == std::string::npos)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Invalid format of configuration file: %s", configuration_filename);
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        std::string param_name, param_value;
        std::getline(line_stream, param_name, COLUMN_SEPARATOR);
        std::getline(line_stream, param_value, COLUMN_SEPARATOR);
        param_value.erase(std::find_if(param_value.rbegin(), param_value.rend(), [](int ch) {
            return !std::isspace(ch);
        }).base(), param_value.end());

        if (param_name.empty())
        {
            Logger::Print(LOG_LEVEL_ERROR, "Invalid format of configuration file: %s", configuration_filename);
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }

        try
        {
            if (param_name == "-dec:wfst:hmmModelFName")
            {
                auto status = ReadBinaryFile(param_value,
                    &parameters_->decoder_parameters.hmm_model_size,
                    parameters_->decoder_parameters.hmm_model_data);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }
            else if (param_name == "-dec:wfst:fsmFName")
            {
                auto status = ReadBinaryFile(param_value,
                    &parameters_->decoder_parameters.pronunciation_model_size,
                    parameters_->decoder_parameters.pronunciation_model_data);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }
            else if (param_name == "-dec:wfstotf:gramFsmFName")
            {
                auto status = ReadBinaryFile(param_value,
                    &parameters_->decoder_parameters.language_model_size,
                    parameters_->decoder_parameters.language_model_data);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }
            else if (param_name == "-dec:wfst:outSymsFName")
            {
                auto status = ReadBinaryFile(param_value,
                    &parameters_->decoder_parameters.labels_size,
                    parameters_->decoder_parameters.labels_data);
                if (status != SPEECH_LIBRARY_SUCCESS)
                {
                    return status;
                }
            }
            else if (param_name == "-dec:wfst:acousticScaleFactor")
            {
                parameters_->decoder_parameters.acoustic_scale_factor = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:beamWidth")
            {
                parameters_->decoder_parameters.beam_width = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:latticeWidth")
            {
                parameters_->decoder_parameters.lattice_beam_width = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:nbest")
            {
                parameters_->decoder_parameters.n_best = std::stoi(param_value);
            }
            else if (param_name == "-dec:wfst:confidenceAcousticScaleFactor")
            {
                parameters_->decoder_parameters.confidence_acoustic_scale_factor = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:confidenceLMScaleFactor")
            {
                parameters_->decoder_parameters.confidence_lm_scale_factor = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:tokenBufferSize")
            {
                parameters_->decoder_parameters.token_buffer_size = std::stoi(param_value);
            }
            else if (param_name == "-dec:wfstotf:traceBackLogSize")
            {
                parameters_->decoder_parameters.trace_back_log_size = std::stoi(param_value);
            }
            else if (param_name == "-dec:wfstotf:minStableFrames")
            {
                parameters_->decoder_parameters.min_stable_frames = std::stoi(param_value);
            }
            else if (param_name == "-dec:wfst:maxCumulativeTokenSize")
            {
                parameters_->decoder_parameters.token_buffer_fill_threshold = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:maxTokenBufferFill")
            {
                parameters_->decoder_parameters.token_buffer_max_fill = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:maxAvgTokenBufferFill")
            {
                parameters_->decoder_parameters.token_buffer_max_avg_fill = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:tokenBufferMinFill")
            {
                parameters_->decoder_parameters.token_buffer_min_fill = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:pruningTighteningDelta")  // not existing in 'big' RH params
            {
                parameters_->decoder_parameters.pruning_tightening_delta = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:pruningRelaxationDelta")  // not existing in 'big' RH params
            {
                parameters_->decoder_parameters.pruning_relaxation_delta = std::stof(param_value);
            }
            else if (param_name == "-dec:wfst:useScoreTrendForEndpointing")
            {
                parameters_->decoder_parameters.use_score_trend_for_endpointing =
                    ParseBooleanParameter(param_value);
            }
            else if (param_name == "-dec:wfstotf:cacheLogSize")
            {
                parameters_->decoder_parameters.g_cache_log_size = std::stoi(param_value);
            }
            else if (param_name == "-dec:subsampling")
            {
                parameters_->decoder_parameters.subsampling_factor = std::stoi(param_value);
            }
            else if (param_name == "-eng:output:format")
            {
                if (param_value == "text")
                {
                    parameters_->decoder_parameters.result_format_type =
                        SpeechLibraryResultFormatType::SPEECH_LIBRARY_RESULT_FORMAT_TYPE_TEXT;
                }
                else
                {
                    throw std::invalid_argument("Invalid result format value.");
                }
            }
            // Feature Extraction
            else if (param_name == "-fe:rt:numCeps")
            {
                parameters_->feature_extraction_parameters.number_of_cepstrums = std::stoi(param_value);
            }
            else if (param_name == "-fe:rt:contextLeft")
            {
                parameters_->feature_extraction_parameters.context_left = std::stoi(param_value);
            }
            else if (param_name == "-fe:rt:contextRight")
            {
                parameters_->feature_extraction_parameters.context_right = std::stoi(param_value);
            }
            else if (param_name == "-fe:rt:featureTransform")
            {
                feature_transform_filename_ = param_value;
            }
            else if (param_name == "-fe:rt:hpfBeta")
            {
                parameters_->feature_extraction_parameters.hpf_beta = std::stof(param_value);
            }
            else if (param_name == "-fe:rt:noDct")
            {
                parameters_->feature_extraction_parameters.no_dct =
                    ParseBooleanParameter(param_value);
            }
            else if (param_name == "-fe:rt:cepstralLifter")
            {
                parameters_->feature_extraction_parameters.cepstral_lifter = std::stof(param_value);
            }
            else if (param_name == "-fe:rt:maxChunkSize")
            {
                parameters_->feature_extraction_parameters.max_chunk_size_in_samples = std::stoi(param_value);
            }
            else if (param_name == "-fe:rt:inputDataType")
            {
                // one way to specify the value is the descriptive one, the other one is the enum value
                if (param_value == "INT16_16KHZ" || param_value == "0")
                {
                    parameters_->feature_extraction_parameters.input_data_type =
                        SpeechLibraryInputDataType::SPEECH_LIBRARY_INPUT_DATA_TYPE_SAMPLE_INT_16_SR_16_KHZ;
                }
                else
                {
                    throw std::invalid_argument("Invalid input data type value.");
                }
            }
            // Scorer
            else if (param_name == "-dec:wfst:acousticModelFName")
            {
                parameters_->scorer_parameters.model_network_path = param_value + ".xml";
                parameters_->scorer_parameters.model_weights_path = param_value + ".bin";
            }
            else if (param_name == "-inference:batchSize")
            {
                parameters_->scorer_parameters.batch_size = std::stoi(param_value);
            }
            else if (param_name == "-inference:subsampling")
            {
                parameters_->scorer_parameters.subsampling_factor = std::stoi(param_value);
            }
            else if (param_name == "-inference:contextLeft")
            {
                parameters_->scorer_parameters.context_window_left = std::stoi(param_value);
            }
            else if (param_name == "-inference:contextRight")
            {
                parameters_->scorer_parameters.context_window_right = std::stoi(param_value);
            }
            else if (param_name == "-inference:device")
            {
                parameters_->scorer_parameters.infer_device = param_value;
            }
            else if (param_name == "-inference:numThreads")
            {
                parameters_->scorer_parameters.infer_num_threads = std::stoi(param_value);
            }
            else if (param_name == "-inference:scaleFactor")
            {
                parameters_->scorer_parameters.scale_factor = std::stof(param_value);
            }
            else if (param_name == "-inference:quantizationBits")
            {
                parameters_->scorer_parameters.quantization_bits = std::stoi(param_value);
            }
        }
        catch (const std::invalid_argument &)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Invalid value of parameter: %s", param_name.c_str());
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }
        catch (const std::out_of_range &)
        {
            Logger::Print(LOG_LEVEL_ERROR, "Value of parameter %s out of range", param_name.c_str());
            return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
        }
    }

    file.close();
    return CheckInferenceParameters();
}

int SpeechEngine::ParseBooleanParameter(std::string value)
{
    if (value == "yes" || value == "true" || value == "True" || value == "1")
    {
        return 1;
    }
    else if (value == "no" || value == "false" || value == "False" || value == "0")
    {
        return 0;
    }
    else
    {
        throw std::invalid_argument("Invalid bool value");
    }
}

SpeechLibraryStatus SpeechEngine::ReadBinaryFile(std::string filename, size_t* size,
    std::unique_ptr<uint8_t[]>& data)
{
    filename.erase(std::find_if(filename.rbegin(), filename.rend(), [](int ch) {
        return !std::isspace(ch);
    }).base(), filename.end());

    if (filename.empty()) {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to read file. Filename is empty.");
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    if (nullptr == size) {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to read: %s. Size parameter is null", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

#if defined(__STDC_LIB_EXT1__) || defined(_MSC_VER)
    FILE* f = nullptr; // file pointer
    if( 0 != fopen_s(&f, filename.c_str(), "rb") )
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to open binary file: %s!", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }
#else
    FILE* f = fopen(filename.c_str(), "rb");
    if( f == nullptr )
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to open binary file: %s!", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }

#endif

    int32_t res = fseek(f, 0, SEEK_END);
    if (res != 0) {
        fclose(f);
        Logger::Print(LOG_LEVEL_ERROR, "Error occured while loading (fseek) file: %s", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }

    size_t file_size = ftell(f);
    if (file_size < 0) {
        fclose(f);
        Logger::Print(LOG_LEVEL_ERROR, "Error occured while loading (ftell) file: %s", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }

    res = fseek(f, 0, SEEK_SET);
    data.reset(new (std::nothrow) uint8_t[file_size]);
    if (data.get() == nullptr) {
        fclose(f);
        Logger::Print(LOG_LEVEL_ERROR, "Not enough memory to load file: %s", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }

    *size = fread(data.get(), 1, file_size, f);
    fclose(f);

    if (*size != file_size) {
        Logger::Print(LOG_LEVEL_ERROR, "Could not read all the data from file: %s", filename.c_str());
        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
    }

    return SPEECH_LIBRARY_SUCCESS;
}
