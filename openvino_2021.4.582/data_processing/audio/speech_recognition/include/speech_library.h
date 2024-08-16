// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#ifndef __SPEECH_LIBRARY_H__
#define __SPEECH_LIBRARY_H__

#include <stddef.h>
#include <stdint.h>


#ifdef _WIN32
#   if defined(SPEECH_LIBRARY_EXPORT) /* Visual Studio */
#       define SPEECH_LIBRARY_API_EXPORT __declspec(dllexport)
#   elif defined(__CYGWIN__) /* Disable this on Cygwin, it doesn't work */
#       define SPEECH_LIBRARY_API_EXPORT
#   else
#       define SPEECH_LIBRARY_API_EXPORT __declspec(dllimport)
#   endif
#else
#   if defined(SPEECH_LIBRARY_EXPORT)
#       define SPEECH_LIBRARY_API_EXPORT __attribute__((visibility("default")))
#   else
#       define SPEECH_LIBRARY_API_EXPORT
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

    typedef void* SpeechLibraryHandle; /* Speech Library handle */
                                       /// @brief message for RH HMM model argument

                                       /// @brief message for images argument
                                       /// \brief Define parameter for set image file <br>
                                       /// It is a required parameter

    typedef enum SpeechLibraryStatus {
        SPEECH_LIBRARY_SUCCESS = 0,
        SPEECH_LIBRARY_ERROR_GENERIC = -1,
        SPEECH_LIBRARY_ERROR_OUT_OF_MEMORY = -2,
        SPEECH_LIBRARY_ERROR_INVALID_RESOURCE = -4,
        SPEECH_LIBRARY_ERROR_INVALID_PARAM = -5,
        SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE = -6,
        SPEECH_LIBRARY_ERROR_INVALID_STATE = -9,
    } SpeechLibraryStatus;

    typedef enum SpeechLibraryResultType {
        SPEECH_LIBRARY_RESULT_TYPE_PARTIAL,
        SPEECH_LIBRARY_RESULT_TYPE_PREVIEW,
        SPEECH_LIBRARY_RESULT_TYPE_FINAL
    } SpeechLibraryResultType;

    typedef enum SpeechLibraryParameter
    {
        /**
        * Inference batch size.
        * Type of parameter: int32_t
        * Size in bytes: 4
        */
        SPEECH_LIBRARY_PARAMETER_INFERENCE_BATCH_SIZE,

        /**
        * Name of the inference engine, e.g.: CPU or GNA_AUTO
        * Type of parameter: const char*
        * Size in bytes: number of characters (including null-termination character),
        *                e.g. CPU has size of 4 bytes ("CPU\0")
        */
        SPEECH_LIBRARY_PARAMETER_INFERENCE_DEVICE
    } SpeechLibraryParameter;

    typedef struct SpeechLibraryProcessingInfo {
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
    } SpeechLibraryProcessingInfo;

    /**
    * Routine creates speech library instance and returns back handle to it.
    *
    * @param [out] handle - The speech library handle.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryCreate(SpeechLibraryHandle* handle);

    /**
    * Routine initializes speech library instance created using SpeechLibraryCreate.
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    * @param configuration_filename - Path to text file with configuration parameters needed to
                                      initialize the speech library.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryInitialize(SpeechLibraryHandle handle,
        const char* configuration_filename);

    /**
    * Routine sets given parameter value.
    * Note: Speech library instance must be initialized (call to SpeechLibraryInitialize).
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    * @param parameter - The parameter ID (from SpeechLibraryParameter enum)
    * @param value - The buffer holding value of proper type.
    * @param size - The size of the value: INT32: 4 or in case of
                    const char* number of characters (including null-termination character)
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibrarySetParameter(SpeechLibraryHandle handle,
        SpeechLibraryParameter parameter, const void* value, size_t size);

    /**
    * Routine processes audio samples.
    * Note: Speech library instance must be initialized (call to SpeechLibraryInitialize).
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    * @param data -   Pointer to the array with audio samples (in format as specified in
                      configuration file parameter '-fe:rt:inputDataType', e.g. INT16, 16 kHz sampling rate)
    * @param elements_count - Number of audio samples in 'input_samples'.
                              Its value must not exceed the value provided in
                              configuration file parameter '-fe:rt:maxChunkSize'.
    * @param [out] info - Status information of the decoder (component of speech library) after
                          processing the frame. The status includes a flag whether the decoder
                          detected the end of the utterance <=> stable result. Based on that
                          information the user may call SpeechLibraryGetResult routine.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryPushData(SpeechLibraryHandle handle,
        const void* data, size_t elements_count, SpeechLibraryProcessingInfo* info);

    /**
    * Routine processes any outstanding audio samples that were not yet processed
    * (due to possible latencies in the processing pipeline).
    * Usual use case for this routine is processing an audio file,
    * when the user wants the complete file to be processed.
    * Note: Speech library instance must be initialized (call to SpeechLibraryInitialize).
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    * @param [out] info - Status information of the decoder (component of speech library) after
                          processing the frame. The status includes a flag whether the decoder
                          detected the end of the utterance <=> stable result. Based on that
                          information the user may call SpeechLibraryGetResult routine.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryProcessResidueData(SpeechLibraryHandle handle,
        SpeechLibraryProcessingInfo* info);

    /**
    * Routine returns recognition result (in a format requested in configuration file
    * parameter '-eng:output:format') in buffer allocated by the user.
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
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
    * @param [inout] result - The buffer for result allocated by the user.
    * @param buffer_size - The size of result buffer.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryGetResult(SpeechLibraryHandle handle,
        SpeechLibraryResultType result_type, char* buffer, size_t buffer_size);

    /**
    * Routine resets the state of speech library and makes engine ready for recognition of next utterance.
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryReset(SpeechLibraryHandle handle);

    /**
    * Routine frees all resources allocated by speech library and destroys handle.
    *
    * @param handle - Handle to the speech library instance from SpeechLibraryCreate.
    */
    SPEECH_LIBRARY_API_EXPORT SpeechLibraryStatus SpeechLibraryRelease(SpeechLibraryHandle* handle);

#ifdef __cplusplus
}
#endif

#endif // __SPEECH_LIBRARY_H__
