:: Copyright (C) 2018-2020 Intel Corporation
:: SPDX-License-Identifier: Apache-2.0

@echo off
setlocal EnableDelayedExpansion

set TARGET=CPU
set BUILD_FOLDER=%USERPROFILE%\Documents\Intel\OpenVINO
set "openvino_top_dir=C:\Program Files (x86)\IntelSWTools"
set ROOT_DIR="%~dp0..\..\..\..\.."

if exist "%INTEL_OPENVINO_DIR%\bin\setupvars.bat" (
    :: first check if INTEL_OPENVINO_DIR is already set
    call "%INTEL_OPENVINO_DIR%\bin\setupvars.bat"
    set "ROOT_DIR=%INTEL_OPENVINO_DIR%"
) else if exist "%ROOT_DIR%\bin\setupvars.bat" (
    :: then check if we are running from speech demo folder
    call "%ROOT_DIR%\bin\setupvars.bat"
) else (
    set /a count=1
    for /f "tokens=*" %%a in ('dir /B /O-N /AD "%openvino_top_dir%\openvino_20*"') do (
        if !count!==1 (
            set latest_openvino_dir=%%a
        )
        set /a count=count+1
    )

    if exist "%openvino_top_dir%\!latest_openvino_dir!\bin\setupvars.bat" (
        call "%openvino_top_dir%\!latest_openvino_dir!\bin\setupvars.bat"
        set "ROOT_DIR=%openvino_top_dir%\!latest_openvino_dir!"
    ) else (
        echo Error^: setupvars.bat is not found, INTEL_OPENVINO_DIR can't be set
        goto errorHandling
    )
)

set TARGET_PRECISION=FP32
echo target_precision = !TARGET_PRECISION!
echo INTEL_OPENVINO_DIR is set to %INTEL_OPENVINO_DIR%
echo DEMO_ROOT_DIR is set to %ROOT_DIR%

set "target_wave_path=%ROOT_DIR%\deployment_tools\demo\how_are_you_doing.wav"
set model_package_name=intel\lspeech_s5_ext\!TARGET_PRECISION!
set models_path=%BUILD_FOLDER%\openvino_models\ir
set CONFIGURATION_FILE=%models_path%\%model_package_name%\speech_lib.cfg
if not exist "%CONFIGURATION_FILE%" (
   echo Error^: model configuration file does not exist!
   echo Please run demo_speech_recognition.bat from deployment_tools\demo folder first.
   echo The batch file downloads models and builds required executables.
   goto errorHandling
)

if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
   set "PLATFORM=x64"
) else (
   set "PLATFORM=Win32"
)
set SOLUTION_DIR64=%BUILD_FOLDER%\data_processing_demos_build\audio\speech_recognition
set PATH=%PATH%;%ROOT_DIR%\data_processing\audio\speech_recognition\lib\%PLATFORM%;%SOLUTION_DIR64%\intel64\Release;

echo ###############^|^| Run Inference Engine offline speech recognition demo ^|^|###############
echo.
cd "%SOLUTION_DIR64%\intel64\Release"

if exist "offline_speech_recognition_app.exe" (
   echo "%SOLUTION_DIR64%\intel64\Release\offline_speech_recognition_app.exe" -wave="%target_wave_path%" -c="%CONFIGURATION_FILE%"
   offline_speech_recognition_app.exe -wave="%target_wave_path%" -c="%CONFIGURATION_FILE%"
) else (
   echo Error^: offline speech recognition demo executable does not exist!
   echo Please run demo_speech_recognition.bat from deployment_tools\demo first.
   echo The batch file downloads models and builds required executables.
   goto errorHandling
)
GOTO eof
:errorHandling
echo Error
:eof
cd "%ROOT_DIR%"
