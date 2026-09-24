@echo off
REM Launch the crosshair overlay via "python -m", which avoids the generated
REM crosshair.exe launcher that Windows Smart App Control may block.
REM Requires uv (https://astral.sh/uv). Pass extra args through, e.g. run.bat --settings
uv run python -m crosshair_overlay %*
