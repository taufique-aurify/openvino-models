#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "IE::inference_engine_transformations" for configuration "Release"
set_property(TARGET IE::inference_engine_transformations APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(IE::inference_engine_transformations PROPERTIES
  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine_transformations.lib"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine_transformations.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine_transformations )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine_transformations "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine_transformations.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine_transformations.dll" )

# Import target "IE::inference_engine" for configuration "Release"
set_property(TARGET IE::inference_engine APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(IE::inference_engine PROPERTIES
  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine.lib"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine.dll" )

# Import target "IE::inference_engine_c_api" for configuration "Release"
set_property(TARGET IE::inference_engine_c_api APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(IE::inference_engine_c_api PROPERTIES
  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine_c_api.lib"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine_c_api.dll"
  )

list(APPEND _IMPORT_CHECK_TARGETS IE::inference_engine_c_api )
list(APPEND _IMPORT_CHECK_FILES_FOR_IE::inference_engine_c_api "${_IMPORT_PREFIX}/deployment_tools/inference_engine/lib/intel64/Release/inference_engine_c_api.lib" "${_IMPORT_PREFIX}/deployment_tools/inference_engine/bin/intel64/Release/inference_engine_c_api.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
