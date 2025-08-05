#!/bin/bash

echo "🚀 MerkutY BTK - AI-Powered Language Learning Platform Setup"
echo "=========================================================="

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

# Install spaCy English model (optional)
echo "🔤 Installing spaCy English model for advanced grammar analysis..."
python -m spacy download en_core_web_sm || echo "⚠️ spaCy model installation failed - basic analysis will be used"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp env.example .env
    echo "⚠️  IMPORTANT: Please edit .env file with your database URL and GOOGLE_API_KEY"
    echo "   Get your Gemini API key from: https://makersuite.google.com/app/apikey"
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
echo "- Edit backend/.env file with your database URL and GOOGLE_API_KEY"
echo "- Get your Gemini API key from: https://makersuite.google.com/app/apikey"
echo "- Text analysis requires GOOGLE_API_KEY to work!"
echo ""
echo "🎯 New Features Added:"
echo "- Comprehensive text analysis with Turkish explanations"
echo "- Grammar pattern detection and user knowledge tracking"
echo "- PDF generation for reports and texts"
echo "- i+1 text adaptation"
echo "- YouTube transcript analysis"
echo "- Make sure PostgreSQL is running"
echo "- Run database migrations"
echo ""

echo "🎉 Setup complete! Happy coding!" 