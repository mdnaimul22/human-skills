@echo off
setlocal enabledelayedexpansion

echo =================================================================
echo Installing human-skills global CLI dispatcher for Windows (CMD)...
echo =================================================================

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_DIR=%%~fI"
set "EXEC_PATH=%REPO_DIR%\skills\helpers\execute.py"

if not exist "%EXEC_PATH%" (
    echo Error: Could not find execute.py at "%EXEC_PATH%"
    exit /b 1
)

set "PYTHON_EXE="
where python >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=python"
) else (
    where py >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=py -3"
    ) else (
        where python3 >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=python3"
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo Error: Python 3 is required but not found in PATH.
    echo Please install Python from https://www.python.org/ and check 'Add Python to PATH'.
    exit /b 1
)

set "DEST_DIR=%USERPROFILE%\.local\bin"
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
)

set "CMD_FILE=%DEST_DIR%\human-skills.cmd"

(
    echo @echo off
    echo "%PYTHON_EXE%" "%EXEC_PATH%" %%*
) > "%CMD_FILE%"

for /f "tokens=2* delims= " %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"

echo !USER_PATH! | find /i "%DEST_DIR%" >nul 2>&1
if !errorlevel! neq 0 (
    if defined USER_PATH (
        setx PATH "%DEST_DIR%;%USER_PATH%" >nul
    ) else (
        setx PATH "%DEST_DIR%" >nul
    )
    set "PATH=%DEST_DIR%;%PATH%"
    echo Added %DEST_DIR% to your Windows User PATH.
) else (
    echo %DEST_DIR% is already in your PATH.
)

echo Verifying installation...
call "%CMD_FILE%" --list >nul 2>&1
if !errorlevel! equ 0 (
    echo Verification passed! 'human-skills' command is functional.
) else (
    echo Note: Verification check returned code !errorlevel!.
)

echo =================================================================
echo human-skills installed successfully!
echo Installed wrapper: %CMD_FILE%
echo.
echo You can run 'human-skills' from any CMD or PowerShell terminal:
echo   * human-skills --list
echo   * human-skills --list-all
echo   * human-skills --tool_info tree_gen
echo =================================================================

endlocal
