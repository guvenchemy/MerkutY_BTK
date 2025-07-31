#!/bin/bash

echo "🗄️ Database Setup for Nexus"
echo "=========================="

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL..."
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   On Mac: brew services start postgresql"
    echo "   On Linux: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database if it doesn't exist
echo "📦 Creating database..."
if createdb nexus_db 2>/dev/null; then
    echo "✅ Database 'nexus_db' created successfully"
else
    echo "ℹ️  Database 'nexus_db' already exists"
fi

# Setup backend environment
echo "🔧 Setting up backend environment..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv_new" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv_new
fi

# Activate virtual environment
source venv_new/bin/activate

# Install requirements if not already installed
if [ ! -d "venv_new/lib/python3.9/site-packages/fastapi" ]; then
    echo "📦 Installing Python packages..."
    pip install -r requirements.txt
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your OpenAI API key"
fi

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Database setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit backend/.env file with your OpenAI API key"
echo "2. Start backend: cd backend && source venv_new/bin/activate && uvicorn app.main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev" 