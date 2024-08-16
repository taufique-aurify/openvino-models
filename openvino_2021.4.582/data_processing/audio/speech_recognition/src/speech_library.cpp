// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "speech_library.h"

#include "speech_engine.h"
#include "decoder.h"
#include "feature_extraction.h"
#include "scorer.h"

const uint32_t SPPECH_LIBRARY_MAGIC_NUMBER = 0x00BEAF00;

#define GET_SPEECH_ENGINE(handle) \
    SpeechEngine* engine; \
    if ((nullptr != handle) && \
        (SPPECH_LIBRARY_MAGIC_NUMBER == reinterpret_cast<SpeechLibraryInstance*>(handle)->magic_number)) \
        engine = reinterpret_cast<SpeechLibraryInstance*>(handle)->engine; \
    else \
        return SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;

struct SpeechLibraryInstance
{
    uint32_t        magic_number;
    SpeechEngine*   engine;
};

SpeechLibraryStatus SpeechLibraryCreate(SpeechLibraryHandle* handle)
{
    if (nullptr == handle)
    {
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    if (nullptr != *handle)
    {
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    SpeechLibraryInstance* instance = new (std::nothrow) SpeechLibraryInstance;
    if (nullptr == instance)
    {
        return SPEECH_LIBRARY_ERROR_OUT_OF_MEMORY;
    }

    instance->magic_number = SPPECH_LIBRARY_MAGIC_NUMBER;
    instance->engine = new SpeechEngine();

    *handle = instance;
    return SPEECH_LIBRARY_SUCCESS;
}

SpeechLibraryStatus SpeechLibraryInitialize(SpeechLibraryHandle handle,
    const char* configuration_filename)
{
    GET_SPEECH_ENGINE(handle);

    SpeechLibraryStatus status = engine->ParseConfiguration(configuration_filename);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        return status;
    }

    return engine->Initialize();
}

SpeechLibraryStatus SpeechLibrarySetParameter(SpeechLibraryHandle handle,
    SpeechLibraryParameter parameter, const void* value, size_t size)
{
    GET_SPEECH_ENGINE(handle);
    return engine->SetParameter(parameter, value, size);
}

SpeechLibraryStatus SpeechLibraryPushData(SpeechLibraryHandle handle,
    const void* data, size_t elements_count, SpeechLibraryProcessingInfo* info)
{
    GET_SPEECH_ENGINE(handle);
    return engine->PushData(data, elements_count, info);
}

SpeechLibraryStatus SpeechLibraryProcessResidueData(SpeechLibraryHandle handle,
    SpeechLibraryProcessingInfo* info)
{
    GET_SPEECH_ENGINE(handle);
    return engine->ProcessResidueData(info);
}

SpeechLibraryStatus SpeechLibraryGetResult(SpeechLibraryHandle handle,
    SpeechLibraryResultType result_type, char* buffer, size_t buffer_size)
{
    GET_SPEECH_ENGINE(handle);
    return engine->GetResult(result_type, buffer, buffer_size);
}

SpeechLibraryStatus SpeechLibraryReset(SpeechLibraryHandle handle)
{
    GET_SPEECH_ENGINE(handle);
    return engine->Reset();
}

SpeechLibraryStatus SpeechLibraryRelease(SpeechLibraryHandle* handle)
{
    if (nullptr == handle || nullptr == *handle)
    {
        return SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;
    }

    SpeechLibraryInstance* instance = static_cast<SpeechLibraryInstance*>(*handle);
    if (SPPECH_LIBRARY_MAGIC_NUMBER != instance->magic_number)
    {
        return SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;
    }

    if (nullptr == instance->engine)
    {
        return SPEECH_LIBRARY_ERROR_INVALID_HANDLE_VALUE;
    }

    delete instance->engine;
    instance->engine = nullptr;

    instance->magic_number = 0;
    delete instance;

    *handle = nullptr;

    return SPEECH_LIBRARY_SUCCESS;
}
