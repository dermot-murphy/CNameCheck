@echo off
REM check_my_project.bat — run CStyleCheck against your own C codebase.
REM Edit the paths in the CONFIG section below before running.
REM Usage:  scripts\check_my_project.bat

REM =============================================================================
REM CONFIG — edit these paths
REM =============================================================================

REM Path to cstylecheck (use "cstylecheck" if installed via pip/pipx)
SET CHECKER=cstylecheck

REM Root of the C source tree to check (supports glob include below)
SET SRC_ROOT=C:\path\to\your\project\src

REM Your project rules.yml (copy src\rules.yml and customise)
SET CONFIG=C:\path\to\your\project\cstylecheck\rules.yml

REM Additional flags (remove or add as needed)
SET FLAGS=--summary --warnings-as-errors

REM =============================================================================
REM END CONFIG
REM =============================================================================

echo === CStyleCheck — %SRC_ROOT% ===
echo Config : %CONFIG%
echo.

%CHECKER% --config "%CONFIG%" --include "%SRC_ROOT%\**\*.c" --include "%SRC_ROOT%\**\*.h" %FLAGS%

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo [PASS] No violations found.
) ELSE IF %ERRORLEVEL% EQU 1 (
    echo.
    echo [WARN] Violations reported — see output above.
) ELSE (
    echo.
    echo [ERROR] CStyleCheck exited with error code %ERRORLEVEL% (config problem^?^)
)

exit /b %ERRORLEVEL%
