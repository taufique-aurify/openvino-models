// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "kaldi_component_reader.h"

#include <fstream>
#include <iostream>
#include <sstream>

#include "logger.h"

SpeechLibraryStatus ReadKaldiVectorComponent(const char *filename,
                                             const char *component_name,
                                             std::vector<float> *result,
                                             float min_value,
                                             float max_value)
{
    if (nullptr == result)
    {
        Logger::Print(LOG_LEVEL_ERROR, "Kaldi return vector not specified");
        return SPEECH_LIBRARY_ERROR_GENERIC;
    }

    std::ifstream file(filename);

    if (!file.is_open())
    {
        Logger::Print(LOG_LEVEL_ERROR, "Failed to open Kaldi file: %s", filename);
        return SPEECH_LIBRARY_ERROR_INVALID_PARAM;
    }

    std::string line;

    // Try to find component
    bool found_component = false;
    bool start_values = false;
    bool is_done = false;
    while (std::getline(file, line) && !is_done)
    {
        if (!found_component)
        {
            if (line.find(component_name) != std::string::npos)
            {
                found_component = true;
            }
        }
        else
        {
            const char FIELD_SEPARATOR = ' ';
            std::istringstream line_stream(line);
            std::string value;

            while (std::getline(line_stream, value, FIELD_SEPARATOR))
            {
                if (!start_values)
                {
                    const char *VALUES_START_SYMBOL = "[";
                    if (value.compare(VALUES_START_SYMBOL) == 0)
                    {
                        start_values = true;
                    }
                }
                else
                {
                    const char *VALUES_END_SYMBOL = "]";
                    if (value.compare(VALUES_END_SYMBOL) == 0)
                    {
                        is_done = true;
                        break;
                    }
                    size_t processed_characters = 0;
                    float float_value = std::stof(value, &processed_characters);

                    // Check if read was successful
                    if (processed_characters < value.size())
                    {
                        Logger::Print(LOG_LEVEL_ERROR, "Could not parse number '%s' in %s",
                                      value.c_str(), filename);
                        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
                    }
                    if (float_value < min_value)
                    {
                        Logger::Print(LOG_LEVEL_ERROR, "Value in file %s too small (%f < %f)",
                                      filename, float_value, min_value);
                        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
                    }
                    if (float_value > max_value)
                    {
                        Logger::Print(LOG_LEVEL_ERROR, "Value in file %s too large (%f > %f)",
                                      filename, float_value, max_value);
                        return SPEECH_LIBRARY_ERROR_INVALID_RESOURCE;
                    }
                    result->push_back(float_value);
                }
            }
        }
    }

    return SPEECH_LIBRARY_SUCCESS;
}
