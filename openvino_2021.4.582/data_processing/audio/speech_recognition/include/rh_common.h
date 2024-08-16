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

#ifndef __RH_COMMON_H__
#define __RH_COMMON_H__

#ifdef __cplusplus
extern "C" {
#endif

typedef enum RhAcousticModelType
{
    RH_ACOUSTIC_MODEL_TYPE_GENERIC_CHAIN = 0,
    RH_ACOUSTIC_MODEL_TYPE_ASPIRE_CHAIN_TDNN = 1,
    RH_ACOUSTIC_MODEL_TYPE_LAST = RH_ACOUSTIC_MODEL_TYPE_ASPIRE_CHAIN_TDNN
} RhAcousticModelType;

#ifdef __cplusplus
}
#endif
#endif  // __RH_COMMON_H__
