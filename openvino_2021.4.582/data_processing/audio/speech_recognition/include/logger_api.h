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

#ifndef __LOGGER_API_H__
#define __LOGGER_API_H__

#include <stdint.h>
#include <stdarg.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum AvsLoggerLogLevel
{
    AVSLOGGER_LEVEL_NONE,         //!< No logging.
    AVSLOGGER_LEVEL_ERROR,        //!< Only error level messages will be logged.
    AVSLOGGER_LEVEL_WARNING,      //!< Only warning and error level messages will be logged.
    AVSLOGGER_LEVEL_INFO,         //!< Logging including info level messages
    AVSLOGGER_LEVEL_DEBUG,        //!< Most verbose logging for debugging purposes, not intended for production.

    //
    AVSLOGGER_LEVEL_MAX_LEVEL = AVSLOGGER_LEVEL_DEBUG, //!< Alias for most verbose logging level.
} AvsLoggerLogLevel;

typedef void* ILoggerHandle;
typedef void(*ICLoggerWriteMessage)(const ILoggerHandle logger, AvsLoggerLogLevel level, const char* log_message);

#ifdef __cplusplus
}
#endif
#endif // __LOGGER_API_H__
