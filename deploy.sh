#!/bin/bash

# CEFR Language Learning Platform - Deployment Script
# This script helps deploy the application on a NAS server using Docker and Portainer

set -e

echo "🚀 CEFR Language Learning Platform Deployment"
echo "============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration before continuing!"
    echo "   Required: GEMINI_API_KEY, SECRET_KEY"
    echo "   Optional: OPENAI_API_KEY, domain settings"
    echo ""
    read -p "Press enter to continue after editing .env file..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p logs
mkdir -p uploads

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 data/postgres data/redis logs uploads

# Pull the latest images
echo "⬇️  Pulling Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building application images..."
docker-compose build

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
echo "Database status (Host PostgreSQL):"
echo "✅ Using existing PostgreSQL 17 on NAS server"

echo "Backend status:"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend is healthy" || echo "⚠️  Backend not ready yet"

echo "Frontend status:"
curl -f http://localhost:3000 2>/dev/null && echo "✅ Frontend is healthy" || echo "⚠️  Frontend not ready yet"

echo ""
echo "🎉 Deployment completed!"
echo "================================"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🗄️  Database: Mevcut NAS PostgreSQL 17 (localhost:5432)"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop all: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Update: docker-compose pull && docker-compose up -d"
echo ""
echo "🔧 For Portainer integration:"
echo "1. Install Portainer on your NAS"
echo "2. Add this docker-compose.yml as a stack"
echo "3. Set environment variables in Portainer UI"
echo ""
echo "📝 Don't forget to:"
echo "- Create database on PostgreSQL 17: CREATE DATABASE nexus_db;"
echo "- Create user: CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';"
echo "- Grant permissions: GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;"
echo "- Configure your domain/SSL if using in production"
echo "- Set up regular database backups"
echo "- Monitor resource usage"
