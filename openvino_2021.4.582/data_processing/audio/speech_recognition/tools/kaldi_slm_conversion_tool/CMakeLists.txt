# Copyright (C) 2019 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

set (TARGET_NAME "kaldi_slm_conversion_tool")

add_executable(${TARGET_NAME} src/slm_converter.cpp)
target_link_libraries(${TARGET_NAME} PRIVATE ${SpeechDecoder_LIBRARIES})
target_include_directories(${TARGET_NAME} PUBLIC ../../include)
