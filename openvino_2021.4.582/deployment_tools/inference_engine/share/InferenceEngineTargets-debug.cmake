#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "IE::inference_engine_transformations" for configuration "Debug"
set_property(TARGET IE::inference_engine_transformations APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(IE::inference_engine_transformations PROPERTIES
  IMPORTED_IMPLIB_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engine_transformationsd.lib"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engine_transformationsd.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine_transformations )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine_transformations "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engine_transformationsd.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engine_transformationsd.dll" )

# Import target "IE::inference_engine" for configuration "Debug"
set_property(TARGET IE::inference_engine APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(IE::inference_engine PROPERTIES
  IMPORTED_IMPLIB_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engined.lib"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engined.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engined.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engined.dll" )

# Import target "IE::inference_engine_c_api" for configuration "Debug"
set_property(TARGET IE::inference_engine_c_api APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(IE::inference_engine_c_api PROPERTIES
  IMPORTED_IMPLIB_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engine_c_apid.lib"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engine_c_apid.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine_c_api )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine_c_api "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Debug/inference_engine_c_apid.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Debug/inference_engine_c_apid.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
