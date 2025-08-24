@echo off
echo Starting Phoenix Observability Server for GAMP-5 System...
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

REM Stop any existing Phoenix containers
echo Stopping existing Phoenix containers...
docker stop phoenix-gamp5 >nul 2>&1
docker rm phoenix-gamp5 >nul 2>&1

REM Start Phoenix in Docker with correct port mapping
echo Starting Phoenix container...
docker run -d --name phoenix-gamp5 -p 6006:6006 arizephoenix/phoenix:latest

REM Wait for Phoenix to start
echo Waiting for Phoenix to start...
timeout /t 5 /nobreak >nul

REM Check if Phoenix is accessible
curl -f http://localhost:6006 >nul 2>&1
if errorlevel 1 (
    echo ERROR: Phoenix UI not accessible at http://localhost:6006
    echo Checking container status...
    docker logs phoenix-gamp5
    pause
    exit /b 1
)

echo.
echo ✅ SUCCESS: Phoenix UI is now accessible!
echo.
echo 🌐 Phoenix UI: http://localhost:6006
echo 📊 To view traces: Run your test generation workflow, then visit the URL above
echo.
echo Press any key to open Phoenix UI in browser...
pause >nul
start http://localhost:6006