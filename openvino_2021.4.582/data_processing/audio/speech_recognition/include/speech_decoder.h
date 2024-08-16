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

#ifndef __SPEECH_DECODER_H__
#define __SPEECH_DECODER_H__

#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

#include "rh_common.h"
#include "logger_api.h"

#ifdef RH_DECODER_LIBRARY_STATIC
#   define RH_DECODER_API_EXPORT
#else
#   ifdef _WIN32
#       if defined(RH_DECODER_EXPORT) /* Visual Studio */
#           define RH_DECODER_API_EXPORT __declspec(dllexport)
#       elif defined(__CYGWIN__) /* Disable this on Cygwin, it doesn't work */
#           define RH_DECODER_API_EXPORT
#       else
#           define RH_DECODER_API_EXPORT __declspec(dllimport)
#       endif
#   else
#       if defined(RH_DECODER_EXPORT)
#           define RH_DECODER_API_EXPORT __attribute__((visibility("default")))
#       else
#           define RH_DECODER_API_EXPORT
#       endif
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct
{
    uint32_t class_extension_count;
    struct {
        int32_t        class_id;
        const uint8_t* pronunciation_model_ptr;
        size_t         pronunciation_model_size;
        const uint8_t* labels_ptr;
        size_t         labels_size;
    } class_extension[1];
} RhClassExtentionBundle;

enum RhResourceType
{
    HMM = 1,
    PRONUNCIATION_MODEL,
    LANGUAGE_MODEL,
    LABELS,
    CLASS_EXTENTION_BUNDLE
};

enum RhDecoderResultFormat
{
    RH_DECODER_RESULT_FORMAT_TEXT = 0
};

typedef void* RhDecoderInstanceHandle; /* Intel(R) Speech Decoder handle */

typedef enum {
    /**
    * Number of acoustic scores. In case of a DNN this value is
    * equal to the number of output nodes.
    * Type of parameter: int32_t
    */
    RH_DECODER_ACOUSTIC_SCORE_VECTOR_SIZE = 0,

    /**
    * Acoustic scaling factor suitable for the given
    * acoustic and language model.
    * Type of parameter: float
    */
    RH_DECODER_ACOUSTIC_SCALE_FACTOR,

    /**
    * Width of the acoustic beam.
    * The beam width has an impact on recognition accuracy and decoding
    * speed.
    * Type of parameter: float
    */
    RH_DECODER_BEAM_WIDTH,

    /**
    * Width of the lattice beam, can be 0 for first best search.
    * The beam width has an impact on recognition accuracy and decoding
    * speed.
    * Type of parameter: int32_t
    */
    RH_DECODER_LATTICE_BEAM_WIDTH,

    /**
    * Number of best results outputted in recognition result
    * Type of parameter: float
    */
    RH_DECODER_NBEST,

    /**
    * The "impact" scale of acoustic scores on confidence
    * Type of parameter: int32_t
    */
    RH_DECODER_CONFIDENCE_ACOUSTIC_SCALE_FACTOR,

    /**
    * The "impact" scale of language model on confidence
    * Type of parameter: float
    */
    RH_DECODER_CONFIDENCE_LM_SCALE_FACTOR,

    /**
    * Size of the token buffer. This size does not directly relate
    * to the number of bytes used, but a larger value of token_buffer_size
    * results in more memory used.
    * The token buffer size has an impact on recognition accuracy and
    * decoding speed.
    * Type of parameter: float
    */
    RH_DECODER_TOKEN_BUFFER_SIZE,

    /**
    * Size of the trace back array. This size foes not directly relate
    * to the number of bytes used, but a larger value of
    * trace_back_log_size results in more memory used.
    * This value is too small if trace back array overflows appear
    * regularly (can be seen in logging messages).
    * Type of parameter: int32_t
    */
    RH_DECODER_TRACE_BACK_LOG_SIZE,

    /**
    * The number of acoustic frames that a recognition result may not change
    * until it is considered stable by the decoder.
    * Larger values lead to higher latencies whereas smaller values
    * may lead to recognition errors during short pauses.
    * Type of parameter: int32_t
    */
    RH_DECODER_MIN_STABLE_FRAMES,

    /**
    * Token buffer fill threshold that triggers inner frame beam tightening.
    * Type of parameter: float
    */
    RH_DECODER_TOKEN_BUFFER_FILL_THRESHOLD,

    /**
    * Maximum fill rate of token buffer before histogram pruning
    * starts.
    * Type of parameter: float
    */
    RH_DECODER_TOKEN_BUFFER_MAX_FILL,

    /**
    * Maximum sustained fill rate of the token buffer before histogram
    * pruning starts. If this value is larger than token_buffer_max_fill
    * it has no effect on decoding.
    * Type of parameter: float
    */
    RH_DECODER_TOKEN_BUFFER_MAX_AVG_FILL,

    /**
    * Minimum fill rate of token buffer before the pruning threshold
    * is increased compared to the default value beam_width.
    * Type of parameter: float
    */
    RH_DECODER_TOKEN_BUFFER_MIN_FILL,

    /**
    * Tighting of the beam if a token buffer or trace back array
    * overflow happened.
    * Type of parameter: float
    */
    RH_DECODER_PRUNING_TIGHTENING_DELTA,

    /**
    * Relaxation of beam width towards default value each frame after
    * the beam width was tightened due to histogram pruning.
    * Type of parameter: float
    */
    RH_DECODER_PRUNING_RELAXATION_DELTA,

    /**
    * Use acoustic score trend for end of utternace detection
    * 0: no
    * 1: yes
    * Type of parameter: int32_t
    */
    RH_DECODER_USE_SCORE_TREND_FOR_ENDPOINTING,

    /**
    * The size of grammar model cache expressed as Log2(entries count)
    * Type of parameter: int32_t
    */
    RH_DECODER_G_CACHE_LOG_SIZE,

    /**
    * The result format
    * Type of parameter: int32_t
    */
    RH_DECODER_RESULT_FORMAT,

    RH_DECODER_LAST_PARAM = RH_DECODER_RESULT_FORMAT
} RhDecoderParameter;

/**
 * Structure that holds decoder information after a frame is processed.
 * This structure is filled by RhDecoderProcessFrame().
 */
typedef struct _RhDecoderInfo {
    /**
     * Flag that determines whether the decoder has detected the end
     * of an utterance. 0 if no utterance end was detected, 1 if
     * it was detected.
     */
    int32_t is_result_stable;

    /**
     * Flag whether the user started speaking.
     */
    int32_t has_speech_started;
} RhDecoderInfo;

enum RhDecoderStatus {
    RH_DECODER_SUCCESS = 0,
    RH_DECODER_ERROR_GENERIC = -1,
    RH_DECODER_ERROR_OUT_OF_MEMORY = -2,
    RH_DECODER_ERROR_INVALID_RESOURCE = -4,
    RH_DECODER_ERROR_INVALID_PARAM = -5,
    RH_DECODER_ERROR_INVALID_HANDLE_VALUE = -6,
    RH_DECODER_ERROR_INVALID_STATE = -9,
    RH_DECODER_ERROR_MODULE_INIT_FAILED = -10,
    RH_DECODER_ERROR_NOT_INITIALIZED = -31,
    RH_DECODER_ERROR_BUFFER_TOO_SMALL = -35,
    RH_DECODER_ERROR_NOT_SUPPORTED = -37,
};

/**
 * Routine returns formatted version string.
 *
 * @param [inoutptr] version_string - The reference to a pointer the version string will be assigned to.
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_PARAM
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderGetVersion(const char** version_string);

/**
 * Routine creates decoder instance and returns back handle to it.
 *
 * @param [outptr] handle - The decoder handle
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderCreateInstance(
    RhDecoderInstanceHandle* handle);

/**
 * Routine provides pointer to parameters & resources in memory or memory mapped files of resources.
 * Intel(R) Speech Decoder requires at least:
 *   - HMM
 *   - PRONUNCIATION_MODEL
 *   - LANGUAGE_MODEL
 *   - LABELS
 * Routine can be called after RhDecoderCreateInstance() and before RhDecoderInitInstance()
 * The decoding parameters are provided also using the RhDecoderSetupResource routine.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 * @param resource_type - The decoder resource type
 * @param data - The pointer to model in memory (or memory mapped file)
 * @param size - The size of a resource in bytes
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_OUT_OF_MEMORY
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_INVALID_STATE
 *         - RH_DECODER_ERROR_INVALID_RESOURCE
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderSetupResource(
    RhDecoderInstanceHandle handle, RhResourceType resource_type, const uint8_t* data, size_t size);

/**
 * Routine binds all uploaded models with decoder, allocates decoder caches & buffers.
 * based on requested sizes in decoding parameters.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_OUT_OF_MEMORY
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_INVALID_STATE
 *         - RH_DECODER_ERROR_INVALID_RESOURCE
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 *         - RH_DECODER_ERROR_GENERIC
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderInitInstance(
    RhDecoderInstanceHandle handle);

/**
 * Routine free all resources allocated by decoder and destroys handle.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderFreeInstance(
    RhDecoderInstanceHandle handle);

typedef enum {
    RH_DECODER_PREVIEW_RESULT = 0,
    RH_DECODER_PARTIAL_RESULT = 1,
    RH_DECODER_FINAL_RESULT = 2
} RhDecoderResultType;

/**
 * Routine prints recognition result in a format requested in decoding parameters.
 * The result is placed in memory area allocated by external entity.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 * @param result_type - Flag selecting the type of result:
 *      The final result:
 *        - nBest/lattices available
 *        - Contains all information like confidences
 *        - Destroys the content used for result generation
 *        - Restarts decoder
 *      The partial result:
 *        - Provides results that are stable but not yet final
 *        - Allows decoding to continue
 *      The preview result:
 *        - The current 1st best hypothesis (intermediate result)
 *        - May be different from final result
 *          because it does not take end of utterance probability into account
 *        - No word level confidences
 *        - Allows decoding to continue
 * @param [inoutptr] result - The buffer for result allocated by external entity
 * @param size - The size of result buffer
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_NOT_INITIALIZED
 *         - RH_DECODER_ERROR_INVALID_PARAM
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderGetResult(RhDecoderInstanceHandle handle,
    RhDecoderResultType result_type, char* result, size_t size);

/**
 * Resets the state of decoder and makes engine ready for recognition of next utterance.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_NOT_INITIALIZED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderReset(RhDecoderInstanceHandle handle);

/**
 * Process all tokens for one frame and determine whether the end of the
 * utterance was detected. If this function fails, subsequent calls will
 * also fail until RhResetDecoder() is called.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 * @param acoustic_score_vector - Pointer to the array of acoustic scores
 * @param score_vector_size - Number of entries in acoustic_score_vector
 * @param [outptr] info - Status information of the decoder after processing the frame
 *                          The status includes a flag whether the decoder
 *                          detected the end of the utterance <=> stable result
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_HANDLE_VALUE
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_NOT_INITIALIZED
 *         - RH_DECODER_ERROR_GENERIC
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderProcessFrame(RhDecoderInstanceHandle handle,
    const float* acoustic_score_vector, size_t score_vector_size, RhDecoderInfo* info);

/**
 * Routine sets default parameter values for given acoustic model.
 * Must be called before call to RhDecoderInitInstance().
 * Notice: instance created using RhDecoderCreateInstance() has already
 * the parameters set to default values for RH_ACOUSTIC_MODEL_TYPE_GENERIC_CHAIN.
 *
 * @param handle - Handle to the feature extraction instance from RhDecoderCreateInstance()
 * @param model_type - The type of the acoustic model
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderSetDefaultParameterValues(
    RhDecoderInstanceHandle handle, RhAcousticModelType model_type);

/**
 * Routine sets given parameter value.
 * Must be called before call to RhDecoderInitInstance().
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 * @param parameter - The parameter ID
 * @param value - The buffer holding value of proper type
 * @param size - The size of the value: INT32: 4, FLOAT: 4
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderSetParameterValue(
    RhDecoderInstanceHandle handle, RhDecoderParameter parameter, const void* value, size_t size);

/**
 * Routine gets given parameter value.
 *
 * @param handle - Handle to the decoder from RhDecoderCreateInstance()
 * @param parameter - The parameter ID
 * @param [outptr] value - Output parameter with value of requested parameter
 * @param size - The size of the value: INT32: 4, FLOAT: 4
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_NOT_SUPPORTED
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderGetParameterValue(
    RhDecoderInstanceHandle handle, RhDecoderParameter parameter, void* value, size_t size);

/**
 * Sets the logger callback.
 *
 * @param logger_routine - thread safe function that logs messages
 * @param handle - Handle to the logger that will be passed in logger routine
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_GENERIC
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderSetLogger(
    ICLoggerWriteMessage logger_routine, ILoggerHandle handle);

/**
 * Converts a Kaldi HCLG WFST resource in OpenFST const format to
 * Intel(R) Speech Decoder format.
 * For conversions of Kaldi transition-IDs to PDF IDs,
 * the output of Kaldi's show-transitions is needed in addition to the HCLG
 * WFST converted to --fst_type=const
 *
 * @param input_wfst_filename - File name of Kaldi WFST in const format
 * @param transitions_filename - File name of output of Kaldi's show-transitions
 * @param output_wfst_filename - File name of WFST resource
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_INVALID_RESOURCE
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderConvertWFST(
    const char* input_wfst_filename, const char* transitions_filename,
    const char* output_wfst_filename);

/**
 * Converts a Kaldi words.txt output labels resource to
 * Intel(R) Speech Decoder format.
 *
 * @param input_words_txt - File name of Kaldi words.txt file
 * @param output_labels_bin - File name of output labels resource
 *
 * @return One of:
 *         - RH_DECODER_SUCCESS
 *         - RH_DECODER_ERROR_INVALID_PARAM
 *         - RH_DECODER_ERROR_OUT_OF_MEMORY
 *         - RH_DECODER_ERROR_INVALID_RESOURCE
 */
RH_DECODER_API_EXPORT RhDecoderStatus RhDecoderConvertLabels(
    const char* input_words_txt_filename, const char* output_labels_bin_filename);

#ifdef __cplusplus
}
#endif
#endif // __SPEECH_DECODER_H__
