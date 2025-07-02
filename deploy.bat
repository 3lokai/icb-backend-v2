@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting deployment to Fly.io...

REM Check if flyctl is installed
where flyctl >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ flyctl is not installed. Please install it first:
    echo    Windows: powershell -Command "iwr https://fly.io/install.ps1 -useb ^| iex"
    pause
    exit /b 1
)

REM Check if user is logged in
flyctl auth whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Not logged in to Fly.io. Please run: flyctl auth login
    pause
    exit /b 1
)

REM Check if app exists, create if it doesn't
flyctl apps list | findstr "icb-backend-v2" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📱 Creating new app: icb-backend-v2
    flyctl apps create icb-backend-v2
) else (
    echo ✅ App icb-backend-v2 already exists
)

REM Check if required secrets are set
echo 🔐 Checking environment variables...

REM Check for required Supabase variables
flyctl secrets list | findstr "SUPABASE_URL" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  SUPABASE_URL not set. Please set it with:
    echo    fly secrets set SUPABASE_URL=your_supabase_url
    echo    fly secrets set SUPABASE_KEY=your_supabase_key
    echo.
    set /p continue="Continue with deployment anyway? (y/N): "
    if /i not "!continue!"=="y" (
        echo Deployment cancelled.
        pause
        exit /b 1
    )
)

REM Deploy the application
echo 🚀 Deploying to Fly.io...
flyctl deploy

REM Check deployment status
echo 📊 Checking deployment status...
flyctl status

echo ✅ Deployment completed!
echo.
echo 🌐 Your application is available at:
echo    https://icb-backend-v2.fly.dev
echo.
echo 📚 API Documentation:
echo    https://icb-backend-v2.fly.dev/docs
echo.
echo 💚 Health Check:
echo    https://icb-backend-v2.fly.dev/health
echo.
echo 📋 Useful commands:
echo    fly logs --follow          # View real-time logs
echo    fly status                 # Check app status
echo    fly ssh console            # SSH into container
echo    fly apps restart           # Restart the app

pause 