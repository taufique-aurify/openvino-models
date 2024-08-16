// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "logger.h"

#include <stdio.h>

void Logger::Print(LogLevel level, const char *msg, ...)
{
    FILE* output;
    if (level == LogLevel::LOG_LEVEL_ERROR)
    {
        output = stderr;
        fprintf(output, "[ ERROR ] ");
    }
    else
    {
        output = stdout;
        fprintf(output, "[ INFO ] ");
    }

    {
        va_list args;
        va_start(args, msg);
        vfprintf(output, msg, args);
        va_end(args);
    }

    fprintf(output, "\n");
}
