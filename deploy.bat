@echo off
REM CEFR Language Learning Platform - Windows Deployment Script
REM This script helps deploy the application on Windows using Docker

echo 🚀 CEFR Language Learning Platform Deployment
echo =============================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not available. Please install Docker Desktop with Compose.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your actual configuration before continuing!
    echo    Required: GEMINI_API_KEY, SECRET_KEY
    echo    Optional: OPENAI_API_KEY, domain settings
    echo.
    pause
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist data\postgres mkdir data\postgres
if not exist data\redis mkdir data\redis
if not exist logs mkdir logs
if not exist uploads mkdir uploads

REM Pull the latest images
echo ⬇️  Pulling Docker images...
docker-compose pull

REM Build custom images
echo 🔨 Building application images...
docker-compose build

REM Start the services
echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🏥 Checking service health...
echo Database status (Host PostgreSQL):
echo ✅ Using existing PostgreSQL 17 on NAS server

echo Backend status:
curl -f http://localhost:8000/health 2>nul && echo ✅ Backend is healthy || echo ⚠️  Backend not ready yet

echo Frontend status:
curl -f http://localhost:3000 2>nul && echo ✅ Frontend is healthy || echo ⚠️  Frontend not ready yet

echo.
echo 🎉 Deployment completed!
echo ================================
echo 📱 Frontend: http://localhost:3000
echo 🔧 API: http://localhost:8000
echo 📊 API Docs: http://localhost:8000/docs
echo 🗄️  Database: Mevcut NAS PostgreSQL 17 (localhost:5432)
echo.
echo 📋 Useful commands:
echo   View logs: docker-compose logs -f
echo   Stop all: docker-compose down
echo   Restart: docker-compose restart
echo   Update: docker-compose pull ^&^& docker-compose up -d
echo.
echo 🔧 For Portainer integration:
echo 1. Install Portainer on your NAS
echo 2. Add this docker-compose.yml as a stack
echo 3. Set environment variables in Portainer UI
echo.
echo 📝 Don't forget to:
echo - Create database on PostgreSQL 17: CREATE DATABASE nexus_db;
echo - Create user: CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';
echo - Grant permissions: GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;
echo - Configure your domain/SSL if using in production
echo - Set up regular database backups
echo - Monitor resource usage

pause
