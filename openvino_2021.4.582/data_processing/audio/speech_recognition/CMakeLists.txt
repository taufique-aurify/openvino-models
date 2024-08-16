# Copyright (C) 2019-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
cmake_minimum_required(VERSION 3.5)
project(SpeechRecognitionDemo_n_Tools)

if (CMAKE_BUILD_TYPE STREQUAL "")
    message(STATUS "CMAKE_BUILD_TYPE not defined, 'Release' will be used")
    set (CMAKE_BUILD_TYPE "Release")
endif()

if (NOT(BIN_FOLDER))
    string(TOLOWER ${CMAKE_SYSTEM_PROCESSOR} ARCH)
    if(ARCH STREQUAL "x86_64" OR ARCH STREQUAL "amd64") # Windows detects Intel's 64-bit CPU as AMD64
        set(ARCH intel64)
        set(LIBRARY_FOLDER lib/x64)
    elseif(ARCH STREQUAL "i386")
        set(ARCH ia32)
        set(LIBRARY_FOLDER lib/x86)
    endif()

    set (BIN_FOLDER ${ARCH})
endif()

set (CMAKE_CXX_STANDARD 11)
set (CXX_STANDARD_REQUIRED true)

set (DATA_PROCESSING_MAIN_DEMOS_DIR ${CMAKE_CURRENT_BINARY_DIR})

if(NOT(UNIX))
    set (CMAKE_LIBRARY_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (CMAKE_LIBRARY_PATH ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (CMAKE_COMPILE_PDB_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (CMAKE_PDB_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (CMAKE_RUNTIME_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (LIBRARY_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER})
    set (LIBRARY_OUTPUT_PATH ${LIBRARY_OUTPUT_DIRECTORY}) # compatibility issue: linux uses LIBRARY_OUTPUT_PATH, windows uses LIBRARY_OUTPUT_DIRECTORY
else ()
    set (CMAKE_LIBRARY_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE}/lib)
    set (CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE}/lib)
    set (CMAKE_COMPILE_PDB_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE})
    set (CMAKE_PDB_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE})
    set (CMAKE_RUNTIME_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE})
    set (LIBRARY_OUTPUT_DIRECTORY ${DATA_PROCESSING_MAIN_DEMOS_DIR}/${BIN_FOLDER}/${CMAKE_BUILD_TYPE}/lib)
    set (LIBRARY_OUTPUT_PATH ${LIBRARY_OUTPUT_DIRECTORY}/lib)
endif()

if (WIN32)
    if (NOT "${CMAKE_SIZEOF_VOID_P}" EQUAL "8")
        message(FATAL_ERROR "Only 64-bit supported on Windows")
    endif()

    set_property (DIRECTORY APPEND PROPERTY COMPILE_DEFINITIONS _CRT_SECURE_NO_WARNINGS)
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_SCL_SECURE_NO_WARNINGS -DNOMINMAX")
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc") #no asynchronous structured exception handling
    set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} /LARGEADDRESSAWARE")

    if (TREAT_WARNING_AS_ERROR)
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /WX") #treating warnings as errors
    endif ()

    if (${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /wd4251 /wd4275 /wd4267") #disable some warnings
    endif()
else()
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Werror") #treating warnings as errors
    if (APPLE)
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-error=unused-command-line-argument")
    elseif(UNIX)
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wuninitialized -Winit-self")
        if(NOT ${CMAKE_CXX_COMPILER_ID} STREQUAL Clang)
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wmaybe-uninitialized")
        endif()
    endif()
endif()

set (SPEECH_LIBRARY_TARGET_NAME speech_library)

find_library(SPEECH_DECODER_LIBRARY_FILENAME
        decoder_library
        ${LIBRARY_FOLDER}
        NO_DEFAULT_PATH)
find_library(FEATURE_EXTRACTION_LIBRARY_FILENAME
        feature_extraction_library
        ${LIBRARY_FOLDER}
        NO_DEFAULT_PATH)
message("${CMAKE_GENERATOR_PLATFORM}")
message("${FEATURE_EXTRACTION_LIBRARY_FILENAME}")
message("${LIBRARY_FOLDER}")


set (SpeechFeatureExtraction_LIBRARIES ${FEATURE_EXTRACTION_LIBRARY_FILENAME})
set (SpeechDecoder_LIBRARIES ${SPEECH_DECODER_LIBRARY_FILENAME})
set (SpeechFeatureExtraction_INCLUDES include)
set (SpeechDecoder_INCLUDES include)

set (SPEECH_LIBRARY_HEADERS
    src/logger.h
    src/kaldi_component_reader.h
    src/scorer.h
    src/decoder.h
    src/feature_extraction.h
    src/speech_engine.h
    src/speech_parameters.h
    include/speech_library.h
    )

set (SPEECH_LIBRARY_SOURCES
    src/logger.cpp
    src/kaldi_component_reader.cpp
    src/scorer.cpp
    src/decoder.cpp
    src/feature_extraction.cpp
    src/speech_engine.cpp
    src/speech_library.cpp
    )

add_library(${SPEECH_LIBRARY_TARGET_NAME} SHARED ${SPEECH_LIBRARY_SOURCES} ${SPEECH_LIBRARY_HEADERS})

find_package(InferenceEngine 2.0 REQUIRED)

target_link_libraries(${SPEECH_LIBRARY_TARGET_NAME} PRIVATE ${InferenceEngine_LIBRARIES}
                                                            ${SpeechFeatureExtraction_LIBRARIES}
                                                            ${SpeechDecoder_LIBRARIES})

target_compile_definitions(${SPEECH_LIBRARY_TARGET_NAME} PRIVATE SPEECH_LIBRARY_EXPORT)

target_include_directories(${SPEECH_LIBRARY_TARGET_NAME} PUBLIC include)  # speech_library.h
target_include_directories(${SPEECH_LIBRARY_TARGET_NAME} PRIVATE ${SpeechFeatureExtraction_INCLUDES})
target_include_directories(${SPEECH_LIBRARY_TARGET_NAME} PRIVATE ${SpeechDecoder_INCLUDES})
target_include_directories(${SPEECH_LIBRARY_TARGET_NAME} PRIVATE src)


add_subdirectory(tools)
add_subdirectory(demos)
