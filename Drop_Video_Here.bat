@echo off
title Shorts Clip Generator

:: Check if at least one file was dragged onto the batch file
if "%~1"=="" (
    echo ========================================================
    echo  Drag and drop one or more video files onto this icon!
    echo ========================================================
    pause
    exit /b
)

:: Loop through all dragged files (supports dragging multiple videos at once)
for %%F in (%*) do (
    echo.
    echo --------------------------------------------------------
    echo Processing: "%%~nxF"
    echo --------------------------------------------------------
    python "%~dp0make_shorts.py" "%%~fF"
)

echo.
echo ========================================================
echo  All videos finished processing!
echo ========================================================
pause