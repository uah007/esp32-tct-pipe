@echo off

echo ========================================
echo   Node Bridge - EXE build
echo   (with embedded Node.js from nodejs_portable)
echo ========================================
echo.

REM Check Python version
echo [0/6] Checking Python version...
python --version
echo.

REM Check server.js
if not exist server.js (
    echo.
    echo WARNING: server.js not found!
    echo.
    echo Please create server.js in project root
    echo or copy it here.
    echo Without server.js the application will not work correctly.
    echo.
    pause
    exit /b 1
)

echo [1/6] Checking virtual environment...
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing...
)

echo [4/6] Installing Python dependencies...
echo Installing: paho-mqtt, pyinstaller...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo.
    echo Trying to install packages individually...
    pip install paho-mqtt
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Installation failed completely
        pause
        exit /b 1
    )
)

echo [5/6] Checking Node.js in nodejs_portable...
if exist nodejs_portable\node.exe (
    nodejs_portable\node.exe --version
    set NODE_CMD=nodejs_portable\node.exe
    echo Node.js will be embedded into EXE using local node.exe
) else (
    echo.
    echo WARNING: node.exe not found in nodejs_portable!
    echo Build will continue WITHOUT embedded Node.js
    set NODE_CMD=
    echo Target system must have Node.js installed for full functionality.
    echo.
    timeout /t 3 >nul
)

echo.
echo [6/6] Building EXE with PyInstaller...
REM If you need Node.js embedded in PyInstaller, you can reference %NODE_CMD% in your spec
pyinstaller --clean NodeBridge.spec
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completed successfully!
echo   EXE file: dist\NodeBridge.exe
echo ========================================
echo.
