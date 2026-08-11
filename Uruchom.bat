@echo off
chcp 65001 >nul
cd /d "%~dp0"

where uv >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" uv run python -m baska_diagramy.gui
  exit /b 0
)

if exist "%~dp0.venv\Scripts\pythonw.exe" (
  start "" "%~dp0.venv\Scripts\pythonw.exe" -m baska_diagramy.gui
  exit /b 0
)

if exist "%~dp0.venv\Scripts\python.exe" (
  start "" "%~dp0.venv\Scripts\python.exe" -m baska_diagramy.gui
  exit /b 0
)

echo Nie znaleziono uv ani .venv.
echo Otworz ten folder w terminalu i uruchom: uv sync
pause
