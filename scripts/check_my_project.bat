@echo off
REM check_my_project.bat - run CStyleCheck against your own C codebase.
REM Edit the paths in the CONFIG section below before running.
REM Usage:  scripts\check_my_project.bat

REM =============================================================================
REM CONFIG - edit these paths
REM =============================================================================

REM Path to cstylecheck.  Options:
REM   1. Run directly from the cloned repo (always uses current source):
REM        SET CHECKER=python src\cstylecheck.py
REM   2. pip/pipx install (ensure you have the latest version installed):
REM        SET CHECKER=cstylecheck
SET CHECKER=python src\cstylecheck.py

REM Root of the C source tree to check (supports glob include below)
SET SRC_ROOT=C:\path\to\your\project\src

REM Your project rules.yml (copy src\rules.yml and customise)
SET CONFIG=C:\path\to\your\project\cstylecheck\rules.yml

REM Additional flags (remove or add as needed)
SET FLAGS=--summary --warnings-as-errors

REM When --fix is in FLAGS the checker may need multiple passes: fixing one
REM violation can expose others that were previously hidden.  Set FIX_PASSES
REM to the maximum number of passes to run.  The loop exits early once the
REM checker reports no violations (exit code 0).  Set FIX_PASSES=1 to
REM disable multi-pass behaviour (single run regardless of --fix).
SET FIX_PASSES=3

REM =============================================================================
REM END CONFIG
REM =============================================================================

echo === CStyleCheck - %SRC_ROOT% ===
echo Config : %CONFIG%
echo.

SET _PASS=0

:NEXT_PASS
SET /A _PASS+=1

IF %_PASS% GTR 1 (
    echo.
    echo --- Re-checking after fixes ^(pass %_PASS% of %FIX_PASSES%^) ---
    echo.
)

%CHECKER% --config "%CONFIG%" --include "%SRC_ROOT%\**\*.c" --include "%SRC_ROOT%\**\*.h" %FLAGS%
SET _RC=%ERRORLEVEL%

IF %_RC% EQU 0 GOTO :DONE
IF %_PASS% LSS %FIX_PASSES% GOTO :NEXT_PASS

:DONE
IF %_RC% EQU 0 (
    echo.
    echo [PASS] No violations found.
) ELSE IF %_RC% EQU 1 (
    echo.
    echo [WARN] Violations reported - see output above.
) ELSE (
    echo.
    echo [ERROR] CStyleCheck exited with error code %_RC% (config problem?)
)

exit /b %_RC%
