// Copyright (C) 2019-2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//
#ifdef __STDC_LIB_EXT1__
#define __STDC_WANT_LIB_EXT1__ 1
#endif

#include "speech_library.h"
#include "command_line_parser.h"
#include <memory>
#include <vector>

const int SUCCESS_STATUS = 0;
const int ERROR_STATUS = -1;

typedef struct _RiffWaveHeader
{
    unsigned int riff_tag;       /* "RIFF" string */
    int riff_length;             /* Total length */
    unsigned int  wave_tag;      /* "WAVE" */
    unsigned int  fmt_tag;       /* "fmt " string (note space after 't') */
    int  fmt_length;             /* Remaining length */
    short data_format;           /* Data format tag, 1 = PCM */
    short num_of_channels;       /* Number of channels in file */
    int sampling_freq;           /* Sampling frequency */
    int bytes_per_sec;           /* Average bytes/sec */
    short block_align;           /* Block align */
    short bits_per_sample;
    unsigned int data_tag;       /* "data" string */
    int data_length;             /* Raw data length */
} RiffWaveHeader;

uint8_t* ReadBinaryFile(const char* filename, unsigned int* size) {
    if(nullptr == filename)
    {
        fprintf(stderr, "Filename is NULL\n");
        return nullptr;
    }
#if defined(__STDC_LIB_EXT1__) || defined(_MSC_VER)
    FILE* f = nullptr; // file pointer
    if( 0 == fopen_s(&f, filename, "rb") ) {
#else
    FILE* f = fopen(filename, "rb");
    if( f != nullptr ) {
#endif
        int32_t res = fseek(f, 0, SEEK_END);
        if (res != 0)
        {
            fprintf(stderr, "Error occured while loading file %s\n", filename);
            fclose(f);
            return nullptr;
        }
        long int file_size = ftell(f);
        if (file_size < 0)
        {
            fprintf(stderr, "Error occured while loading file %s\n", filename);
            fclose(f);
            return nullptr;
        }

        res = fseek(f, 0, SEEK_SET);
        if (res != 0)
        {
            fprintf(stderr, "Error occured while loading file %s\n", filename);
            fclose(f);
            return nullptr;
        }
        uint8_t* data = new (std::nothrow)uint8_t[file_size];
        if (data) {
            *size = fread(data, 1, file_size, f);
        }
        else
        {
            fprintf(stderr, "Not enough memory to load file %s\n", filename);
            fclose(f);
            return nullptr;
        }
        fclose(f);
        if (*size != file_size)
        {
            delete[]data;
            fprintf(stderr, "Could not read all the data from file %s\n", filename);
            return nullptr;
        }
        return data;
    }
    fprintf(stderr, "Could not open file %s\n", filename);

    return nullptr;
}

int PushWaveData(SpeechLibraryHandle handle, const char* wave_file_name)
{
    const unsigned int kSubHeaderSize = 8;
    const unsigned int kFormatSize = 16;
    const short kPCMFormat = 1;
    const short kMonoStreamChannelsCount = 1;
    const int k16KHzSamplingFrequency = 16000;
    const int kBandwidthOfMono16KHz16bitStream = kMonoStreamChannelsCount *
        k16KHzSamplingFrequency * sizeof(short);
    const short k16bitSampleContainer = kMonoStreamChannelsCount * sizeof(short);
    const short kNumBitsPerByte = 8;
    const short kBitsPer16bitSample = sizeof(short) * kNumBitsPerByte;

    unsigned int size = 0;
    uint8_t* wave_data = ReadBinaryFile(wave_file_name, &size);
    if (wave_data)
    {
        short* samples = nullptr;
        int    data_length = 0;
        RiffWaveHeader* wave_header = reinterpret_cast<RiffWaveHeader*>(wave_data);
        if (size < sizeof(RiffWaveHeader))
        {
            fprintf(stderr, "Unrecognized WAVE file format - header size does not match\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        // make sure it is actually a RIFF file
        if (0 != memcmp(&wave_header->riff_tag, "RIFF", 4))
        {
            fprintf(stderr, "The %s file is not a valid RIFF file\n", wave_file_name);
            delete []wave_data;
            return ERROR_STATUS;
        }
        if (0 != memcmp(&wave_header->wave_tag, "WAVE", 4))
        {
            fprintf(stderr, "Unrecognized WAVE file format - required RIFF WAVE\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        if(0 != memcmp(&wave_header->fmt_tag, "fmt ", 4))
        {
            fprintf(stderr, "Audio file format tag is incorrect\n");
            delete []wave_data;
            return ERROR_STATUS;
        }

        // only PCM
        if (wave_header->data_format != kPCMFormat)
        {
            fprintf(stderr, "Unrecognized WAVE file format - required PCM encoding\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        // only mono
        if (wave_header->num_of_channels != kMonoStreamChannelsCount)
        {
            fprintf(stderr, "Invalid channel count - required mono PCM\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        // only 16 bit
        if (wave_header->bits_per_sample != kBitsPer16bitSample)
        {
            fprintf(stderr, "Incorrect sampling resolution - required PCM 16bit sample resolution\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        // only 16KHz
        if (wave_header->sampling_freq != k16KHzSamplingFrequency)
        {
            fprintf(stderr, "Incorrect sampling rate - required 16KHz sampling rate\n");
            delete []wave_data;
            return ERROR_STATUS;
        }
        if (wave_header->bytes_per_sec != kBandwidthOfMono16KHz16bitStream)
        {
            fprintf(stderr, "Wave file doesn't have desired bytes per second (%d != %d)\n",
               wave_header->bytes_per_sec, kBandwidthOfMono16KHz16bitStream);
            delete []wave_data;
            return ERROR_STATUS;
        }
        if (wave_header->block_align != k16bitSampleContainer)
        {
            fprintf(stderr, "Wave file has unsupported block align %d required %d bits sample container\n",
               static_cast<int>(wave_header->block_align), static_cast<int>(k16bitSampleContainer));
            delete []wave_data;
            return ERROR_STATUS;
        }
        // make sure that data chunk follows file header
        if (0 == memcmp(&wave_header->data_tag, "data", 4))
        {
            samples = reinterpret_cast<short*>(wave_data + sizeof(RiffWaveHeader));
            data_length = wave_header->data_length;
            if (data_length < 0 || sizeof(RiffWaveHeader) + data_length != size)
            {
                fprintf(stderr, "Audio file data length is incorrect\n");
                delete []wave_data;
                return ERROR_STATUS;
            }
        }
        else if ((wave_header->fmt_length >= 0)
                 && (wave_header->fmt_length < size - sizeof(RiffWaveHeader))
                 && (0 == memcmp(&wave_header->data_tag + (wave_header->fmt_length - kFormatSize), "data", 4)))
        {
            samples = reinterpret_cast<short*>(wave_data + sizeof(RiffWaveHeader) + (wave_header->fmt_length - kFormatSize));
            data_length = *(reinterpret_cast<int*>(wave_data + sizeof(RiffWaveHeader) + (wave_header->fmt_length - kFormatSize) - 4));
            if (data_length < 0 || sizeof(RiffWaveHeader) + (wave_header->fmt_length - kFormatSize) + data_length != size)
            {
                fprintf(stderr, "Audio file data length is incorrect\n");
                delete []wave_data;
                return ERROR_STATUS;
            }
        }
        else
        {
            fprintf(stderr, "Unrecognized WAVE file format - header size does not match\n");
            delete []wave_data;
            return ERROR_STATUS;
        }


        // bits per sample already checked - no div by zero
        int number_of_samples_read = data_length / (wave_header->bits_per_sample / 8);

        const int CHUNK_SIZE = 4000;
        int samples_pushed = 0;
        for (samples_pushed = 0; samples_pushed < number_of_samples_read;)
        {
            int current_chunk_size = CHUNK_SIZE <= number_of_samples_read - samples_pushed ?
                CHUNK_SIZE : number_of_samples_read - samples_pushed;

            SpeechLibraryProcessingInfo info = { 0 };
            int result = SpeechLibraryPushData(handle, samples + samples_pushed, current_chunk_size, &info);
            // if result < 0 it means error occurred
            if (result < 0)
            {
                break;
            }

            samples_pushed += current_chunk_size;
        }
        delete []wave_data;
        SpeechLibraryProcessingInfo info = { 0 };
        SpeechLibraryProcessResidueData(handle, &info);
        return SUCCESS_STATUS;
    }
    return ERROR_STATUS;
}

int ProcessSpeechLibrary(std::string wave_path, std::string config_path)
{
    std::vector<char> rh_utterance_transcription(1024 * 1024);

    SpeechLibraryHandle handle = nullptr;
    auto status = SpeechLibraryCreate(&handle);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        fprintf(stderr, "Failed to create speech library instance. Status: %d\n", status);
        return ERROR_STATUS;
    }

    status = SpeechLibraryInitialize(handle, config_path.c_str());
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        fprintf(stderr, "Failed to initialize speech library. Status: %d\n", status);
        status = SpeechLibraryRelease(&handle);
        if (status != SPEECH_LIBRARY_SUCCESS)
        {
            fprintf(stderr, "Failed to release speech library. Status: %d\n", status);
        }
        return ERROR_STATUS;
    }

    PushWaveData(handle, wave_path.c_str());

    if (rh_utterance_transcription.size() > 0)
    {
        SpeechLibraryGetResult(handle, SPEECH_LIBRARY_RESULT_TYPE_FINAL,
            rh_utterance_transcription.data(), rh_utterance_transcription.size());
        fprintf(stdout, "Recognition result:\n%s\n", rh_utterance_transcription.data());
    }
    else
    {
        fprintf(stderr, "ERROR: Failed to allocate buffer for transcription result\n");
    }

    status = SpeechLibraryRelease(&handle);
    if (status != SPEECH_LIBRARY_SUCCESS)
    {
        fprintf(stderr, "Failed to release speech library. Status: %d\n", status);
        return ERROR_STATUS;
    }

    return SUCCESS_STATUS;
}

// Returns true if an UTF-8 string only consists of ASCII characters
static bool IsASCII(std::string text)
{
    for (std::string::const_iterator it = text.cbegin(); it != text.cend(); ++it)
    {
        const unsigned char kMinASCII = 1;
        const unsigned char kMaxASCII = 127;

        unsigned char character = static_cast<unsigned char>(*it);
        if (character < kMinASCII || character > kMaxASCII)
        {
            return false;
        }
    }

    return true;
}
int main(int argc, char *argv[])
{
    std::string wave_filename;
    std::string config_filename;

    CommandLineParser cmd;
    cmd.Add("-wave", "", &wave_filename, "", "Filepath to input WAV to be processed");
    cmd.Add("-c", "--config", &config_filename, "", "Filepath to configuration file with SpeechLibrary parameters");

    if (cmd.Parse(argc, argv)) {
        fprintf(stderr, "ERROR parsing command line\n");
        fprintf(stderr, "    usage: speech_library_app [OPTIONS]\n");
        fprintf(stderr, "    supported options (incl. parsed values):\n");
        cmd.PrintDescription(std::cerr);
        exit(ERROR_STATUS);
    }

    if (!IsASCII(wave_filename))
    {
        fprintf(stderr, "Error: Wave filename contains non-ASCII characters\n");
        return 1;
    }
    if (!IsASCII(config_filename))
    {
        fprintf(stderr, "Error: Configuration filename contains non-ASCII characters\n");
        return 1;
    }
    return ProcessSpeechLibrary(wave_filename, config_filename);
}
