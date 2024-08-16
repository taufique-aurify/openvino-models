# Copyright (C) 2019 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

set (MY_TARGET offline_speech_recognition_app)

set (MY_SOURCES src/speech_library_app.cpp)

add_executable(${MY_TARGET} ${MY_SOURCES})

if (${APPLE})
    # iOS target is not supported
    return()
endif ()

find_package(InferenceEngine 2.0 REQUIRED)
find_package(Threads REQUIRED)
target_link_libraries(${MY_TARGET}
    ${SPEECH_LIBRARY_TARGET_NAME}
    ${CMAKE_THREAD_LIBS_INIT}
    ${InferenceEngine_LIBRARIES})

if (NOT WIN32)
    target_compile_features(${MY_TARGET} PRIVATE cxx_auto_type cxx_nullptr cxx_deleted_functions)
endif ()

install(TARGETS ${MY_TARGET} DESTINATION bin)