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

:: Check if Python is installed
python --version 2>NUL
if errorlevel 1 (
   echo Error^: Python is not installed. Please install Python 3.5 ^(64-bit^) or higher from https://www.python.org/downloads/
   goto errorHandling
)

:: Check if Python version is equal or higher 3.4
for /F "tokens=* USEBACKQ" %%F IN (`python --version 2^>^&1`) DO (
   set version=%%F
)
echo %var%

for /F "tokens=1,2,3 delims=. " %%a in ("%version%") do (
   set Major=%%b
   set Minor=%%c
)

if "%Major%" geq "3" (
   if "%Minor%" geq "5" (
  set python_ver=okay
   )
)
if not "%python_ver%"=="okay" (
   echo Error^: Unsupported Python version. Please install Python 3.5 ^(64-bit^) or higher from https://www.python.org/downloads/
   goto errorHandling
)

echo ###############^|^| Run Inference Engine live speech recognition demo ^|^|###############
echo.

if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
   set "PLATFORM=x64"
) else (
   set "PLATFORM=Win32"
)
set SOLUTION_DIR64=%BUILD_FOLDER%\data_processing_demos_build\audio\speech_recognition
set PATH=%PATH%;%ROOT_DIR%\data_processing\audio\speech_recognition\lib\%PLATFORM%;%SOLUTION_DIR64%\intel64\Release;

if exist "%SOLUTION_DIR64%\demos\live_speech_recognition_demo\speech_demo_app.py" (
   cd "%SOLUTION_DIR64%\demos\live_speech_recognition_demo"
   python speech_demo_app.py
) else (
   echo Error^: live speech recognition demo python app is not setup correctly!
   echo Please run demo_speech_recognition.bat from deployment_tools\demo folder first.
   echo The batch file downloads models and builds required executables.
   goto errorHandling
)
goto eof

:errorHandling
echo Error
:eof
cd "%ROOT_DIR%"
