@echo off

echo ========================================
echo   Clean Project
echo ========================================
echo.
echo This will delete:
echo - venv (virtual environment)
echo - build (temporary build files)
echo - dist (compiled EXE files)
echo - __pycache__ (Python cache)
echo.
echo Continue? (Y/N)
choice /C YN /N /M "Select: "
if errorlevel 2 (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo Cleaning...

if exist venv (
    echo Removing venv...
    rmdir /s /q venv
)

if exist build (
    echo Removing build...
    rmdir /s /q build
)

if exist dist (
    echo Removing dist...
    rmdir /s /q dist
)

if exist src\__pycache__ (
    echo Removing src\__pycache__...
    rmdir /s /q src\__pycache__
)

if exist __pycache__ (
    echo Removing __pycache__...
    rmdir /s /q __pycache__
)

for /r %%i in (*.pyc) do (
    echo Removing %%i
    del /q "%%i" 2>nul
)

echo.
echo ========================================
echo   Clean completed!
echo ========================================
echo.
echo You can now run build.bat
echo.

