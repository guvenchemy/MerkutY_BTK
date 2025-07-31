#!/bin/bash

echo "🚀 Nexus - AI-Powered Language Learning Platform Setup"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📁 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv_new" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv_new
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv_new/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your database URL and OpenAI API key"
fi

echo "✅ Backend setup complete!"
echo ""

echo "📁 Setting up frontend..."
cd ../frontend

# Install npm packages
echo "📦 Installing Node.js packages..."
npm install

echo "✅ Frontend setup complete!"
echo ""

echo "🗄️ Database setup instructions:"
echo "1. Make sure PostgreSQL is running"
echo "2. Create database: createdb nexus_db"
echo "3. Run migrations: cd backend && source venv_new/bin/activate && alembic upgrade head"
echo ""

echo "🚀 To start the application:"
echo "1. Backend: cd backend && source venv_new/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "2. Frontend: cd frontend && npm run dev"
echo ""

echo "📝 Don't forget to:"
echo "- Edit backend/.env file with your database URL and OpenAI API key"
echo "- Make sure PostgreSQL is running"
echo "- Run database migrations"
echo ""

echo "🎉 Setup complete! Happy coding!" 