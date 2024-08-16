# Copyright (C) 2018-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
#
# Inference Engine cmake config
# ------
#
# This config defines the following variables:
#
#   InferenceEngine_FOUND        - True if the system has the Inference Engine library
#   InferenceEngine_INCLUDE_DIRS - Inference Engine include directories
#   InferenceEngine_LIBRARIES    - Inference Engine libraries
#
# and the following imported targets:
#
#   IE::inference_engine            - The Inference Engine library
#   IE::inference_engine_c_api      - The Inference Engine C API library
#
# Inference Engine version variables:
#
#   InferenceEngine_VERSION_MAJOR - major version component
#   InferenceEngine_VERSION_MINOR - minor version component
#   InferenceEngine_VERSION_PATCH - patch version component
#


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was InferenceEngineConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

#
# Common functions
#

if(NOT DEFINED CMAKE_FIND_PACKAGE_NAME)
    set(CMAKE_FIND_PACKAGE_NAME InferenceEngine)
    set(_need_package_name_reset ON)
endif()

# we have to use our own version of find_dependency because of support cmake 3.7
macro(_ie_find_dependency dep)
    set(cmake_fd_quiet_arg)
    if(${CMAKE_FIND_PACKAGE_NAME}_FIND_QUIETLY)
        set(cmake_fd_quiet_arg QUIET)
    endif()
    set(cmake_fd_required_arg)
    if(${CMAKE_FIND_PACKAGE_NAME}_FIND_REQUIRED)
        set(cmake_fd_required_arg REQUIRED)
    endif()

    get_property(cmake_fd_alreadyTransitive GLOBAL PROPERTY
        _CMAKE_${dep}_TRANSITIVE_DEPENDENCY)

    find_package(${dep} ${ARGN}
        ${cmake_fd_quiet_arg}
        ${cmake_fd_required_arg})

    if(NOT DEFINED cmake_fd_alreadyTransitive OR cmake_fd_alreadyTransitive)
        set_property(GLOBAL PROPERTY _CMAKE_${dep}_TRANSITIVE_DEPENDENCY TRUE)
    endif()

    if(NOT ${dep}_FOUND)
        set(${CMAKE_FIND_PACKAGE_NAME}_NOT_FOUND_MESSAGE "${CMAKE_FIND_PACKAGE_NAME} could not be found because dependency ${dep} could not be found.")
        set(${CMAKE_FIND_PACKAGE_NAME}_FOUND False)
        return()
    endif()

    set(cmake_fd_required_arg)
    set(cmake_fd_quiet_arg)
endmacro()

function(_ie_target_no_deprecation_error)
    if(NOT MSVC)
        if(CMAKE_CXX_COMPILER_ID STREQUAL "Intel")
            set(flags "-diag-warning=1786")
        else()
            set(flags "-Wno-error=deprecated-declarations")
        endif()

        set_target_properties(${ARGV} PROPERTIES INTERFACE_COMPILE_OPTIONS ${flags})
    endif()
endfunction()

#
# Inference Engine config
#

# need to store current PACKAGE_PREFIX_DIR, because it's overwritten by ngraph one
set(IE_PACKAGE_PREFIX_DIR "${PACKAGE_PREFIX_DIR}")

set(THREADING "TBB")
if(THREADING STREQUAL "TBB" OR THREADING STREQUAL "TBB_AUTO" AND NOT TBB_FOUND)
    set_and_check(_tbb_dir "${PACKAGE_PREFIX_DIR}/external/tbb/cmake")
    _ie_find_dependency(TBB
                        COMPONENTS tbb tbbmalloc
                        CONFIG
                        PATHS ${TBBROOT}/cmake
                              ${_tbb_dir}
                        NO_CMAKE_FIND_ROOT_PATH
                        NO_DEFAULT_PATH)
endif()

set_and_check(_ngraph_dir "${PACKAGE_PREFIX_DIR}/../ngraph/cmake")
_ie_find_dependency(ngraph
                    CONFIG
                    PATHS ${_ngraph_dir}
                    NO_CMAKE_FIND_ROOT_PATH
                    NO_DEFAULT_PATH)

if(NOT TARGET inference_engine)
    set(_ie_as_external_package ON)
    include("${CMAKE_CURRENT_LIST_DIR}/InferenceEngineTargets.cmake")
endif()

# mark components as available
foreach(comp inference_engine inference_engine_c_api)
    set(${CMAKE_FIND_PACKAGE_NAME}_${comp}_FOUND ON)
endforeach()

if(NOT ${CMAKE_FIND_PACKAGE_NAME}_FIND_COMPONENTS)
    set(${CMAKE_FIND_PACKAGE_NAME}_FIND_COMPONENTS inference_engine inference_engine_c_api)
endif()

unset(InferenceEngine_LIBRARIES)
foreach(comp IN LISTS ${CMAKE_FIND_PACKAGE_NAME}_FIND_COMPONENTS)
    # check if the component is available
    if(${CMAKE_FIND_PACKAGE_NAME}_${comp}_FOUND)
        set(pcomp ${comp})
        if(_ie_as_external_package)
            set(pcomp IE::${comp})
        endif()

        list(APPEND InferenceEngine_LIBRARIES ${pcomp})
    endif()
endforeach()

if(_ie_as_external_package)
    _ie_target_no_deprecation_error(${InferenceEngine_LIBRARIES})
endif()
unset(_ie_as_external_package)

# restore PACKAGE_PREFIX_DIR
set(PACKAGE_PREFIX_DIR ${IE_PACKAGE_PREFIX_DIR})
unset(IE_PACKAGE_PREFIX_DIR)

set_and_check(InferenceEngine_INCLUDE_DIRS "${PACKAGE_PREFIX_DIR}/include")

check_required_components(${CMAKE_FIND_PACKAGE_NAME})

if(_need_package_name_reset)
    unset(CMAKE_FIND_PACKAGE_NAME)
    unset(_need_package_name_reset)
endif()
