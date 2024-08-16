:: Copyright (C) 2018-2020 Intel Corporation
:: SPDX-License-Identifier: Apache-2.0
@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
set "BUILD_FOLDER=%USERPROFILE%\Documents\Intel\OpenVINO"
set "openvino_top_dir=c:\Program Files (x86)\IntelSWTools"

if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
   set "PLATFORM=x64"
) else (
   set "PLATFORM=Win32"
)
set "SOLUTION_DIR64=%BUILD_FOLDER%\data_processing_demos_build\audio\speech_recognition"
set "PATH=%PATH%;%ROOT_DIR%\lib\%PLATFORM%;%SOLUTION_DIR64%\intel64\Release;"
set CONFIGURATION=Release

:: Build Speech Library and C++ demo
if not exist "%INTEL_OPENVINO_DIR%\bin\setupvars.bat" (
    if exist "%ROOT_DIR%\..\..\..\bin\setupvars.bat" (
        call "%ROOT_DIR%\..\..\..\bin\setupvars.bat"
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

echo.
echo ###############^|^| Generate VS solution for Inference Engine demos using cmake ^|^|###############
echo.

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

cmake >NUL 2>NUL
if errorlevel 1 (
   echo Error^: cmake is not installed. Please install cmake from https://cmake.org/download/
   goto errorHandling
)

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

echo ##### Build Speech Library - start #####

echo Creating Visual Studio !MSBUILD_VERSION! %PLATFORM% files in %SOLUTION_DIR64%... && ^
if exist "%SOLUTION_DIR64%\CMakeCache.txt" del "%SOLUTION_DIR64%\CMakeCache.txt"
cmake -E make_directory "%SOLUTION_DIR64%" && cd "%SOLUTION_DIR64%" && cmake -G "Visual Studio !MSBUILD_VERSION!" -A %PLATFORM% "%ROOT_DIR%"
if ERRORLEVEL 1 GOTO errorHandling

echo.
echo ###############^|^| Build Inference Engine speech recognition demos using MS Visual Studio (MSBuild.exe) ^|^|###############
echo.
echo "!MSBUILD_BIN!" SpeechRecognitionDemo_n_Tools.sln /p:Configuration=Release /clp:ErrorsOnly /m
"!MSBUILD_BIN!" SpeechRecognitionDemo_n_Tools.sln /p:Configuration=Release /clp:ErrorsOnly /m
if ERRORLEVEL 1 GOTO errorHandling

GOTO eof

:errorHandling
echo Error
:eof
