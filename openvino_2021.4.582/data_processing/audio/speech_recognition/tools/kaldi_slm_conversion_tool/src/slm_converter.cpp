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

#include <fstream>
#include <stdio.h>
#include <string>
#include <unordered_set>

#include "speech_decoder.h"

static void LogRoutine(const ILoggerHandle /*logger*/, AvsLoggerLogLevel level, const char* log_message)
{
    if (level != AvsLoggerLogLevel::AVSLOGGER_LEVEL_WARNING &&
        level != AvsLoggerLogLevel::AVSLOGGER_LEVEL_ERROR)
    {
        return;
    }

    switch (level)
    {
    case AvsLoggerLogLevel::AVSLOGGER_LEVEL_WARNING:
        fprintf(stderr, "WARNING: ");
        break;
    case AvsLoggerLogLevel::AVSLOGGER_LEVEL_ERROR:
        fprintf(stderr, "ERROR: ");
        break;
    default:
        fprintf(stderr, "OTHER: ");
        break;
    }
    fprintf(stderr, "%s\n", log_message);
}

static bool CheckIfFileExists(const char *filename)
{
    std::ifstream file(filename);
    return file.good();
}

static bool CheckIfPathIsWhitelisted(const char *filename)
{
    std::string allowed_characters =
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_.";
    std::unordered_set<char> s_allowed;

    try
    {
        for(size_t i = 0; i < allowed_characters.size(); i++)
        {
            s_allowed.insert(allowed_characters[i]);
        }
        size_t i = 0;
        while (filename[i] != '\0')
        {
            if (s_allowed.find(filename[i]) == s_allowed.end())
            {
                return false;
            }
            i += 1;
        }
    }
    catch (std::exception exception)
    {
        fprintf(stderr, "Could not whitelist filename '%s': %s\n",
                filename, exception.what());
        return false;
    }

    return true;
}

int32_t main(int32_t argc, char* argv[])
{
    const char *wfst_input_filename;
    const char *transitions_filename;
    const char *wfst_output_filename;
    const char *words_txt_input_filename;
    const char *labels_bin_output_filename;
    const int kNumParameters = 5;
    RhDecoderStatus status;

    if (argc != kNumParameters + 1)
    {
        fprintf(stderr, "Error parsing command line\n");
        fprintf(stderr, "  usage: slm_converter <input WFST file> <show-transitions file> "
                "<word ids file> <output WFST file> <output labels file>\n");
        fprintf(stderr, "  example: slm_converter HCLG.fst transitions.txt words.txt hclg.bin labels.bin\n");
        fprintf(stderr, "  note: path traversal characters are prohibited. Only alphanumeric, underscores ");
        fprintf(stderr, "and dots are allowed in pathnames. \n");
        return 1;
    }

    wfst_input_filename = argv[1];
    if (!CheckIfFileExists(wfst_input_filename))
    {
        fprintf(stderr, "Error: WFST input file '%s' can not be read\n",
                wfst_input_filename);
        return 1;
    }
    if(!CheckIfPathIsWhitelisted(wfst_input_filename))
    {
        fprintf(stderr, "Error: WFST input filepath '%s' contains non-whitelisted character(-s)\n",
                wfst_input_filename);
        return 1;
    }

    transitions_filename = argv[2];
    if (!CheckIfFileExists(transitions_filename))
    {
        fprintf(stderr, "Error: Transitions file '%s' can not be read\n",
                transitions_filename);
        return 1;
    }
    if(!CheckIfPathIsWhitelisted(transitions_filename))
    {
        fprintf(stderr, "Error: Transitions filepath '%s' contains non-whitelisted character(-s)\n",
                transitions_filename);
        return 1;
    }

    words_txt_input_filename = argv[3];
    if (!CheckIfFileExists(words_txt_input_filename))
    {
        fprintf(stderr, "Error: Kaldi words.txt input file '%s' can not be read\n",
                words_txt_input_filename);
        return 1;
    }
    if(!CheckIfPathIsWhitelisted(words_txt_input_filename))
    {
        fprintf(stderr, "Error: Kaldi words.txt input filepath '%s' contains non-whitelisted character(-s)\n",
                words_txt_input_filename);
        return 1;
    }

    wfst_output_filename = argv[4];
    if (CheckIfFileExists(wfst_output_filename))
    {
        fprintf(stderr, "Error: WFST output file '%s' already exists and would be overwritten\n",
                wfst_output_filename);
        return 1;
    }
    if(!CheckIfPathIsWhitelisted(wfst_output_filename))
    {
        fprintf(stderr, "Error: WFST output filepath '%s' contains non-whitelisted character(-s)\n",
                wfst_output_filename);
        return 1;
    }

    labels_bin_output_filename = argv[5];
    if (CheckIfFileExists(labels_bin_output_filename))
    {
        fprintf(stderr, "Error: Labels output file '%s' already exists and would be overwritten\n",
                labels_bin_output_filename);
        return 1;
    }
    if(!CheckIfPathIsWhitelisted(labels_bin_output_filename))
    {
        fprintf(stderr, "Error: Labels output filepath '%s' contains non-whitelisted character(-s)\n",
                labels_bin_output_filename);
        return 1;
    }

    RhDecoderSetLogger(LogRoutine, nullptr);

    status = RhDecoderConvertWFST(wfst_input_filename, transitions_filename, wfst_output_filename);
    if (status != RH_DECODER_SUCCESS)
    {
        fprintf(stderr, "Could not convert WFST '%s' to '%s'\n",
                wfst_input_filename, wfst_output_filename);
        return 1;
    }
    fprintf(stderr, "Converted '%s' to '%s'\n", wfst_input_filename, wfst_output_filename);

    status = RhDecoderConvertLabels(words_txt_input_filename, labels_bin_output_filename);
    if (status != RH_DECODER_SUCCESS)
    {
        fprintf(stderr, "Could not convert labels '%s' to '%s'\n",
                words_txt_input_filename, labels_bin_output_filename);
        return 1;
    }
    fprintf(stderr, "Converted '%s' to '%s'\n", words_txt_input_filename, labels_bin_output_filename);

    return 0;
}
