:: Copyright (C) 2018-2020 Intel Corporation
:: SPDX-License-Identifier: Apache-2.0

@echo off
setlocal EnableDelayedExpansion

set TARGET=CPU
set SAMPLE_OPTIONS=
set BUILD_FOLDER=%USERPROFILE%\Documents\Intel\OpenVINO

set "openvino_top_dir=c:\Program Files (x86)\IntelSWTools"

set /a GUI_ENABLED=1
:: command line arguments parsing
:input_arguments_loop
if not "%1"=="" (
    if "%1"=="--no-show" (
        set /a GUI_ENABLED=0
        echo Live speech demo is disabled
    )
    if "%1"=="-no-show" (
        set /a GUI_ENABLED=0
        echo Live speech demo is disabled
    )
    if "%1"=="-help" (
        echo %~n0%~x0 is speech recogntion demo that showcases recognition of speech from wave file
        echo.
        exit /b
    )
    shift
    goto :input_arguments_loop
)

set ROOT_DIR=%~dp0
set target_wave_path=%ROOT_DIR%\how_are_you_doing.wav
set SPEECH_DEMO_ROOT_DIR=%ROOT_DIR%\..\..\data_processing\audio\speech_recognition
set TARGET_PRECISION=FP32

echo target_precision = !TARGET_PRECISION!
if not exist "%INTEL_OPENVINO_DIR%\bin\setupvars.bat" (
    if exist "%ROOT_DIR%\..\..\bin\setupvars.bat" (
        call "%ROOT_DIR%\..\..\bin\setupvars.bat"
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
        ) else (
            echo Error^: setupvars.bat is not found, INTEL_OPENVINO_DIR can't be set
            goto errorHandling
        )
    )
)

echo INTEL_OPENVINO_DIR is set to %INTEL_OPENVINO_DIR%

:: Check if cmake is installed
cmake >NUL 2>NUL
if errorlevel 1 (
   echo Error^: cmake is not installed. Please install cmake from https://cmake.org/download/
   goto errorHandling
)

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

echo.
echo ###############^|^| Generate VS solution for Inference Engine demos using cmake ^|^|###############
echo.
timeout 3

if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
   set "PLATFORM=x64"
) else (
   set "PLATFORM=Win32"
)

set VSWHERE="false"
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
   set VSWHERE="true"
   cd "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer"
) else if exist "%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe" (
      set VSWHERE="true"
      cd "%ProgramFiles%\Microsoft Visual Studio\Installer"
) else (
   echo "vswhere tool is not found"
)

set MSBUILD_BIN=
set VS_PATH=

if !VSWHERE! == "true" (
   for /f "usebackq tokens=*" %%i in (`vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do (
      set VS_PATH=%%i
   )
   if exist "!VS_PATH!\MSBuild\14.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=!VS_PATH!\MSBuild\14.0\Bin\MSBuild.exe"
   )
   if exist "!VS_PATH!\MSBuild\15.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=!VS_PATH!\MSBuild\15.0\Bin\MSBuild.exe"
   )
   if exist "!VS_PATH!\MSBuild\Current\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=!VS_PATH!\MSBuild\Current\Bin\MSBuild.exe"
   )
)

if "!MSBUILD_BIN!" == "" (
   if exist "C:\Program Files (x86)\MSBuild\14.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=C:\Program Files (x86)\MSBuild\14.0\Bin\MSBuild.exe"
      set "MSBUILD_VERSION=14 2015"
   )
   if exist "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\MSBuild\15.0\Bin\MSBuild.exe"
      set "MSBUILD_VERSION=15 2017"
   )
   if exist "C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"
      set "MSBUILD_VERSION=15 2017"
   )
   if exist "C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe" (
      set "MSBUILD_BIN=C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
      set "MSBUILD_VERSION=15 2017"
   )
) else (
   if not "!MSBUILD_BIN:2019=!"=="!MSBUILD_BIN!" set "MSBUILD_VERSION=16 2019"
   if not "!MSBUILD_BIN:2017=!"=="!MSBUILD_BIN!" set "MSBUILD_VERSION=15 2017"
   if not "!MSBUILD_BIN:2015=!"=="!MSBUILD_BIN!" set "MSBUILD_VERSION=14 2015"
)

if "!MSBUILD_BIN!" == "" (
   echo Error^: Build tools for Visual Studio 2015 / 2017 / 2019 cannot be found. If you use Visual Studio 2017 / 2019, please download and install build tools from https://www.visualstudio.com/downloads/#build-tools-for-visual-studio-2017
   GOTO errorHandling
)

set SOLUTION_DIR64=%BUILD_FOLDER%\data_processing_demos_build\audio\speech_recognition
set PATH=%PATH%;%SPEECH_DEMO_ROOT_DIR%\lib\%PLATFORM%;%SOLUTION_DIR64%\intel64\Release;%INTEL_OPENVINO_DIR%\deployment_tools\inference_engine\bin\intel64\Release

:: install yaml python modules required for downloader.py
python -m pip install --user -r "%INTEL_OPENVINO_DIR%\deployment_tools\open_model_zoo\tools\downloader\requirements.in"
if ERRORLEVEL 1 GOTO errorHandling


set models_path=%BUILD_FOLDER%\openvino_models\ir
set models_cache=%BUILD_FOLDER%\openvino_models\cache

if not exist %models_cache% (
  mkdir %models_cache%
)

set "downloader_dir=%SOLUTION_DIR64%\tools\downloader"
xcopy /s /q /y /i "%INTEL_OPENVINO_DIR%\deployment_tools\open_model_zoo\tools\downloader" "%SOLUTION_DIR64%\tools\downloader"
xcopy /s /q /y /i "%SPEECH_DEMO_ROOT_DIR%\models" "%SOLUTION_DIR64%\models"

echo python "%downloader_dir%\downloader.py" --all --output_dir "%models_path%" --cache_dir "%models_cache%"
python "%downloader_dir%\downloader.py" --all --output_dir "%models_path%" --cache_dir "%models_cache%"

echo.
echo ###############^|^| Generate configuration file for models ^|^|###############
echo.
setlocal EnableDelayedExpansion
set "model_package_name=intel\lspeech_s5_ext\!TARGET_PRECISION!"
set CONFIGURATION_FILE=%models_path%\%model_package_name%\speech_lib.cfg
set CONFIGURATION_TEMPLATE=%models_path%\%model_package_name%\speech_recognition_config.template
set MODELS_ROOT=%models_path%\%model_package_name%\

echo #Speech recognition configuration file > %CONFIGURATION_FILE%
for /F "tokens=* delims= " %%a in (%CONFIGURATION_TEMPLATE%) do (
  set str=%%a
  set str=!str:__MODELS_ROOT__=%MODELS_ROOT%!
  echo.!str! >> %CONFIGURATION_FILE%
)

echo Creating Visual Studio !MSBUILD_VERSION! %PLATFORM% files in %SOLUTION_DIR64%...
if exist "%SOLUTION_DIR64%\CMakeCache.txt" del "%SOLUTION_DIR64%\CMakeCache.txt"
cmake -E make_directory "%SOLUTION_DIR64%"
if ERRORLEVEL 1 GOTO errorHandling

cd "%SOLUTION_DIR64%"
cmake -G "Visual Studio !MSBUILD_VERSION!" -A %PLATFORM% "%ROOT_DIR%\..\..\data_processing\audio\speech_recognition"
if ERRORLEVEL 1 GOTO errorHandling

timeout 7
echo.
echo ###############^|^| Build Inference Engine speech recognition demos using MS Visual Studio (MSBuild.exe) ^|^|###############
echo.
timeout 3
echo "!MSBUILD_BIN!" SpeechRecognitionDemo_n_Tools.sln /p:Configuration=Release /clp:ErrorsOnly /m
"!MSBUILD_BIN!" SpeechRecognitionDemo_n_Tools.sln /p:Configuration=Release /clp:ErrorsOnly /m
if ERRORLEVEL 1 GOTO errorHandling

timeout 7

:runSample
echo.
echo ###############^|^| Run Inference Engine offline speech recognition demo ^|^|###############
echo.
timeout 3
cd "%SOLUTION_DIR64%\intel64\Release"
echo "%SOLUTION_DIR64%\intel64\Release\offline_speech_recognition_app.exe" -wave="%target_wave_path%" -c="%CONFIGURATION_FILE%"
offline_speech_recognition_app.exe -wave="%target_wave_path%" -c="%CONFIGURATION_FILE%"

if ERRORLEVEL 1 GOTO errorHandling

echo.
echo ###############^|^| Demo completed successfully ^|^|###############
cd "%ROOT_DIR%"
if !GUI_ENABLED! == 1 (
echo ###############^|^| Installing requirements for live speech recognition demo^|^|###############
python -m pip install -r "%ROOT_DIR%\..\..\data_processing\audio\speech_recognition\demos\live_speech_recognition_demo\requirements_windows.txt"
xcopy /s /q /y /i "%ROOT_DIR%\..\..\data_processing\audio\speech_recognition\demos\live_speech_recognition_demo" "%SOLUTION_DIR64%\demos\live_speech_recognition_demo"
cd "%SOLUTION_DIR64%\demos\live_speech_recognition_demo"
mkdir ..\models\en-us
copy %CONFIGURATION_FILE% ..\models\en-us
python speech_demo_app.py
cd "%ROOT_DIR%"
)
goto eof

:errorHandling
echo Error
:eof
cd "%ROOT_DIR%"
