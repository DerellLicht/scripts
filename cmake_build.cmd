::  This will be an example file that demonstrates flow-control options
::  To see An A-Z Index of Windows CMD commands, visit:
::  https://ss64.com/nt/

@if /I "%~1"=="--build" goto :build_init
@if /I "%~1"=="--clean" goto :clean

:usage
   @echo USAGE:
   @echo     cmake_build [--build [init]] [--clean]
   @echo.
   @echo ARGUMENTS
   @echo    --build      - run cmake build command 
   @echo    --build init - run cmake init and build commands 
   @echo    --clean      - run cmake clean command
   @echo.
   @echo    Either --build or --clean are required
   @echo.
   @echo    Example: 
   @echo    cmake_build --build init
   @goto :eof

:build_init
   @if /I "%~2" NEQ "init" goto :build
      @rem This command only needs to be run *once*, any time the targets change
      cmake -B build -G "MinGW Makefiles" -DCMAKE_CXX_COMPILER=d:/tdm32/bin/g++.exe
:build
      @rem this will build the target
      cmake --build build
   @goto :eof

:clean
   @rem this is equivalent to 'make clean'
   cmake --build build --target clean
   @goto :eof






