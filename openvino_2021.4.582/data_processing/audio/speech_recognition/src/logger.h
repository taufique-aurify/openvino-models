// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#ifndef __LOGGER_H__
#define __LOGGER_H__
#include <stdarg.h>

enum LogLevel
{
    LOG_LEVEL_INFO,
    LOG_LEVEL_ERROR
};

class Logger
{
public:
    static void Print(LogLevel level, const char *msg, ...);
};

#endif // __LOGGER_H__