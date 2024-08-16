//*****************************************************************************
// Copyright (C) 2019 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions
// and limitations under the License.
//
//
// SPDX-License-Identifier: Apache-2.0
//*****************************************************************************

#ifndef __SPEECH_FEATURE_EXTRACTION_H__
#define __SPEECH_FEATURE_EXTRACTION_H__

#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

#include "rh_common.h"
#include "logger_api.h"

#ifdef SPEECH_FEATURE_EXTRACTION_LIBRARY_STATIC
#   define SPEECH_FEATURE_EXTRACTION_API_EXPORT
#else
#   ifdef _WIN32
#       if defined(SPEECH_FEATURE_EXTRACTION_EXPORT) /* Visual Studio */
#           define SPEECH_FEATURE_EXTRACTION_API_EXPORT __declspec(dllexport)
#       elif defined(__CYGWIN__) /* Disable this on Cygwin, it doesn't work */
#           define SPEECH_FEATURE_EXTRACTION_API_EXPORT
#       else
#           define SPEECH_FEATURE_EXTRACTION_API_EXPORT __declspec(dllimport)
#       endif
#   else
#       if defined(SPEECH_FEATURE_EXTRACTION_EXPORT)
#           define SPEECH_FEATURE_EXTRACTION_API_EXPORT __attribute__((visibility("default")))
#       else
#           define SPEECH_FEATURE_EXTRACTION_API_EXPORT
#       endif
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef enum RhFeatureExtractionInputDataType
{
    RH_FEATURE_EXTRACTION_INPUT_DATA_TYPE_SAMPLE_INT_16_SR_16_KHZ  // sampling rate: 16 kHz, 16-bit integer
} RhFeatureExtractionInputDataType;

typedef enum RhFeatureExtractionOutputDataType
{
    RH_FEATURE_EXTRACTION_OUTPUT_DATA_TYPE_FLOAT_32
} RhFeatureExtractionOutputDataType;

/* Intel(R) Feature Extraction module handle */
typedef void* RhFeatureExtractionInstanceHandle;

typedef enum RhFeatureExtractionParameter
{
    /**
    * Number of cepstrums.
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_NUMBER_OF_CEPSTRUMS = 0,

    /**
    * Left context.
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_LEFT,

    /**
    * Right context.
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_RIGHT,

    /**
    * HPF beta.
    * Type of parameter: float
    */
    RH_FEATURE_EXTRACTION_PARAMETER_HPF_BETA,

    /**
    * Cepstral lifter.
    * Type of parameter: float
    */
    RH_FEATURE_EXTRACTION_PARAMETER_CEPSTRAL_LIFTER,

    /**
    * Flag signaling if DCT is disabled.
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_NO_DCT,

    /**
    * Maximum chunk size (in samples) of data provided in one
    * RhFeatureExtractionProcessData call.
    * Type of parameter: uint32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_MAX_CHUNK_SIZE_IN_SAMPLES,

    /**
    * Input data type (see enum RhFeatureExtractionInputDataType)
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_INPUT_DATA_TYPE,

    /**
    * Input data type (see enum RhFeatureExtractionOutputDataType)
    * Type of parameter: int32_t
    */
    RH_FEATURE_EXTRACTION_PARAMETER_OUTPUT_DATA_TYPE,

    RH_FEATURE_EXTRACTION_LAST_PARAMETER = RH_FEATURE_EXTRACTION_PARAMETER_OUTPUT_DATA_TYPE
} RhFeatureExtractionParameter;

enum RhFeatureExtractionStatus {
    RH_FEATURE_EXTRACTION_SUCCESS = 0,
    RH_FEATURE_EXTRACTION_ERROR_GENERIC = -1,
    RH_FEATURE_EXTRACTION_ERROR_OUT_OF_MEMORY = -2,
    RH_FEATURE_EXTRACTION_ERROR_INVALID_RESOURCE = -4,
    RH_FEATURE_EXTRACTION_ERROR_INVALID_PARAM = -5,
    RH_FEATURE_EXTRACTION_ERROR_INVALID_HANDLE_VALUE = -6,
    RH_FEATURE_EXTRACTION_ERROR_INVALID_STATE = -9,
    RH_FEATURE_EXTRACTION_ERROR_MODULE_INIT_FAILED = -10,
    RH_FEATURE_EXTRACTION_ERROR_NOT_INITIALIZED = -31,
    RH_FEATURE_EXTRACTION_ERROR_BUFFER_TOO_SMALL = -35,
    RH_FEATURE_EXTRACTION_ERROR_NOT_SUPPORTED = -37,
};

/**
 * Routine returns version string.
 *
 * @param [inout] version_string - The reference to a pointer the version string will be assigned to.
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionGetVersion(
    const char** version_string);

/**
 * Routine creates feature extraction instance and returns back handle to it.
 * All the parameters are set to default values for RH_ACOUSTIC_MODEL_TYPE_GENERIC_CHAIN.
 *
 * @param [out] handle - The feature extraction handle
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionCreateInstance(
    RhFeatureExtractionInstanceHandle* handle);

/**
 * Routine initializes feature extraction instance created using RhFeatureExtractionCreateInstance.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionInitInstance(
    RhFeatureExtractionInstanceHandle handle);

/**
 * Routine frees all resources allocated by feature extraction and destroys handle.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionFreeInstance(
    RhFeatureExtractionInstanceHandle handle);

/**
 * Routine resets the state of feature extraction and makes engine ready for recognition of next utterance.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionReset(
    RhFeatureExtractionInstanceHandle handle);

/**
 * Routine returns size of feature vector: number of features per frame.
 * Feature extraction needs to be initialized (using RhFeatureExtractionInitInstance)
 * before calling this function.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param [out] vector_size - Output parameter with feature vector size value
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionGetVectorSize(
    RhFeatureExtractionInstanceHandle handle, size_t* vector_size);

/**
* Routine returns maximal size (in bytes) of output buffer for features that is passed to:
* - RhFeatureExtractionProcessData
* - RhFeatureExtractionGetResidueData
*
* @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
* @param [out] max_buffer_size_in_bytes - Output parameter with buffer maximal size in bytes
*/
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionGetOutputBufferMaxSizeInBytes(
    RhFeatureExtractionInstanceHandle handle, size_t* max_buffer_size_in_bytes);

/**
 * Routine processes audio samples to MFCC features and applies splicing (depending on
 * RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_LEFT and RH_FEATURE_EXTRACTION_PARAMETER_CONTEXT_RIGHT).
 * Window size is 25 ms, window sliding is 10 ms.
 * E.g.:
 * Assume 'context_left' and 'context_right' are set to 5 (frames).
 * Then first call to RhFeatureExtractionProcessData with 1600 samples results in 8 frames
 * (8 * 160 samples + 240 samples) computed but because 'context_right' is 5 then only 3 frames are returned.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param input_samples - Pointer to the array with audio samples (in format as specified in
                          RH_FEATURE_EXTRACTION_PARAMETER_INPUT_DATA_TYPE)
 * @param input_samples_count - Number of audio samples in 'input_samples'.
                                Its value must not exceed the value provided in
                                RH_FEATURE_EXTRACTION_PARAMETER_MAX_CHUNK_SIZE_IN_SAMPLES.
 * @param output_features - Pointer to the array with output features that are computed
                            in this routine call (in format as specified in
                            RH_FEATURE_EXTRACTION_PARAMETER_OUTPUT_DATA_TYPE).
                            This buffer must be allocated by the client.
                            Maximum size of the buffer can be read using
                            RhFeatureExtractionGetOutputBufferMaxSizeInBytes.
 * @param [out] output_frames_count - Output parameter with how many features (in frames = 10 ms)
                                      were computed in this routine call. Number of features per frame
                                      can be read using RhFeatureExtractionGetVectorSize.
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionProcessData(
    RhFeatureExtractionInstanceHandle handle, const void* input_samples, size_t input_samples_count,
    void* output_features, size_t* output_frames_count);

/**
 * Routine returns already processed features (using RhFeatureExtractionProcessData)
 * that were not yet returned due to splicing.
 * E.g.:
 * Assume 'context_left' and 'context_right'are set to 5 (frames).
 * Then first call to RhFeatureExtractionProcessData with 1600 samples results in 8 frames
 * (8 * 160 samples + 240 samples) computed but because 'context_right' is 5 then only 3 frames are returned.
 * Then call to RhFeatureExtractionGetResidueData result in 5 frames
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param output_features - Pointer to the array with output features.
                            This buffer must be allocated by the client.
                            Maximum size of the buffer can be read using
                            RhFeatureExtractionGetOutputBufferMaxSizeInBytes.
 * @param [out] output_frames_count - Output parameter with how many features (in frames = 10 ms)
                                      were computed in this routine call. Number of features per frame
                                      can be read using RhFeatureExtractionGetVectorSize.
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionGetResidueData(
    RhFeatureExtractionInstanceHandle handle, void* output_features, size_t* output_frames_count);

/**
 * Routine sets default parameter values for given acoustic model.
 * Must be called before call to RhFeatureExtractionInitInstance().
 * Notice: instance created using RhFeatureExtractionCreateInstance() has already
 * the parameters set to default values for RH_ACOUSTIC_MODEL_TYPE_GENERIC_CHAIN.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param model_type - The type of the acoustic model
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionSetDefaultParameterValues(
    RhFeatureExtractionInstanceHandle handle, RhAcousticModelType model_type);

/**
 * Routine sets given parameter value.
 * Must be called before call to RhFeatureExtractionInitInstance()
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param parameter - The parameter ID
 * @param value - The buffer holding value of proper type
 * @param size - The size of the value: INT32: 4, FLOAT: 4
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionSetParameterValue(
    RhFeatureExtractionInstanceHandle handle, RhFeatureExtractionParameter parameter, const void* value, size_t size);

/**
 * Routine gets given parameter value.
 *
 * @param handle - Handle to the feature extraction instance from RhFeatureExtractionCreateInstance()
 * @param parameter - The parameter ID
 * @param [out] value - Output parameter with value of requested parameter
 * @param size - The size of the value: INT32: 4, FLOAT: 4
 */
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionGetParameterValue(
    RhFeatureExtractionInstanceHandle handle, RhFeatureExtractionParameter parameter, void *value, size_t size);

/**
* Sets the logger callback.
*
* @param logger_routine - thread safe function that logs messages
* @param handle - Handle to the logger that will be passed in logger routine
*/
SPEECH_FEATURE_EXTRACTION_API_EXPORT RhFeatureExtractionStatus RhFeatureExtractionSetLogger(
    ICLoggerWriteMessage logger_routine, ILoggerHandle handle);

#ifdef __cplusplus
}
#endif
#endif // __SPEECH_FEATURE_EXTRACTION_H__
