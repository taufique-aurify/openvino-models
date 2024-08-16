// Copyright (C) 2019 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#pragma once

#include <memory>
#include <string>


typedef enum SpeechLibraryInputDataType {
    SPEECH_LIBRARY_INPUT_DATA_TYPE_SAMPLE_INT_16_SR_16_KHZ  // sampling rate: 16 kHz, 16-bit integer
} SpeechLibraryInputDataType;

typedef enum SpeechLibraryResultFormatType {
    SPEECH_LIBRARY_RESULT_FORMAT_TYPE_TEXT
} SpeechLibraryResultFormatType;

typedef struct FeatureExtractionParameters {
    int number_of_cepstrums;
    int context_left;
    int context_right;
    float hpf_beta;
    float cepstral_lifter;
    int no_dct;
    size_t max_chunk_size_in_samples;
    SpeechLibraryInputDataType input_data_type;
} FeatureExtractionParameters;

typedef struct ScorerParameters {
    /**
    * Input quantization bits (default 16).
    */
    uint32_t quantization_bits;

    /**
    * Path to .xml file with a trained model.
    */
    std::string model_network_path;

    /**
    * Path toh .bin file with a trained model.
    */
    std::string model_weights_path;

    /**
    * Device to infer on.
    */
    std::string infer_device;

    /**
    * Scale factor for quantization.
    */
    float scale_factor;

    /**
    * Number of threads to use for inference on the CPU (also affects Hetero cases).
    */
    uint32_t infer_num_threads;

    /**
    * Batch size (default 1)
    */
    uint32_t batch_size;

    /*
    * Left context window size (default 0).
    */
    uint32_t context_window_left;

    /*
    * Right context window size (default 0).
    */
    uint32_t context_window_right;

    /**
    * Subsampling factor
    */
    uint32_t subsampling_factor;
} ScorerParameters;

typedef struct DecoderParameters {
    /**
    * Pointer to memory buffer with RH .hmm file.
    */
    std::unique_ptr<uint8_t[]> hmm_model_data;

    /**
    * Size in bytes of memory buffer with RH .hmm file.
    */
    size_t hmm_model_size;

    /**
    * Pointer to memory buffer with RH LM: CL .fst model file.
    */
    std::unique_ptr<uint8_t[]> pronunciation_model_data;

    /**
    * Size in bytes of memory buffer with RH LM: CL .fst model file.
    */
    size_t pronunciation_model_size;

    /**
    * Pointer to memory buffer with RH LM: G .fst model file.
    */
    std::unique_ptr<uint8_t[]> language_model_data;

    /**
    * Size in bytes of memory buffer with RH LM: G .fst model file.
    */
    size_t language_model_size;

    /**
    * Pointer to memory buffer with RH labels file.
    */
    std::unique_ptr<uint8_t[]> labels_data;

    /**
    * Size in bytes of memory buffer with RH labels file.
    */
    size_t labels_size;

    /**
    * Acoustic scaling factor suitable for the given
    * acoustic and language model.
    */
    float acoustic_scale_factor;

    /**
    * Width of the acoustic beam.
    * The beam width has an impact on recognition accuracy and decoding
    * speed.
    */
    float beam_width;

    /**
    * Width of the lattice beam, can be 0 for first best search.
    * The beam width has an impact on recognition accuracy and decoding
    * speed.
    */
    float lattice_beam_width;

    /**
    * Number of best results outputted in recognition result
    */
    int32_t n_best;

    /**
    * The "impact" scale of acoustic scores on confidence
    */
    float confidence_acoustic_scale_factor;

    /**
    * The "impact" scale of language model on confidence
    */
    float confidence_lm_scale_factor;

    /**
    * Size of the token buffer. This size does not directly relate
    * to the number of bytes used, but a larger value of token_buffer_size
    * results in more memory used.
    * The token buffer size has an impact on recognition accuracy and
    * decoding speed.
    */
    int32_t token_buffer_size;

    /**
    * Size of the trace back array. This size foes not directly relate
    * to the number of bytes used, but a larger value of
    * trace_back_log_size results in more memory used.
    * This value is too small if trace back array overflows appear
    * regularly (can be seen in logging messages).
    */
    int32_t trace_back_log_size;

    /**
    * The number of acoustic frames that a recognition result may not change
    * until it is considered stable by the decoder.
    * Larger values lead to higher latencies whereas smaller values
    * may lead to recognition errors during short pauses.
    */
    int32_t min_stable_frames;

    /**
    * Token buffer fill threshold that triggers inner frame beam tightening.
    */
    float token_buffer_fill_threshold;

    /**
    * Maximum fill rate of token buffer before histogram pruning
    * starts.
    */
    float token_buffer_max_fill;

    /**
    * Maximum sustained fill rate of the token buffer before histogram
    * pruning starts. If this value is larger than token_buffer_max_fill
    * it has no effect on decoding.
    */
    float token_buffer_max_avg_fill;

    /**
    * Minimum fill rate of token buffer before the pruning threshold
    * is increased compared to the default value beam_width.
    */
    float token_buffer_min_fill;

    /**
    * Tighting of the beam if a token buffer or trace back array
    * overflow happened.
    */
    float pruning_tightening_delta;

    /**
    * Relaxation of beam width towards default value each frame after
    * the beam width was tightened due to histogram pruning.
    */
    float pruning_relaxation_delta;

    /**
    * Use acoustic score trend for end of utternace detection
    * 0: no
    * 1: yes
    */
    int32_t use_score_trend_for_endpointing;

    /**
    * The size of grammar model cache expressed as Log2(entries count)
    */
    int32_t g_cache_log_size;

    /**
    * The result format type
    */
    SpeechLibraryResultFormatType result_format_type;

    /**
    * Subsampling factor
    */
    uint32_t subsampling_factor;

} DecoderParameters;

typedef struct SpeechLibraryParameters {
    FeatureExtractionParameters feature_extraction_parameters;
    ScorerParameters scorer_parameters;
    DecoderParameters decoder_parameters;
} SpeechLibraryParameters;
