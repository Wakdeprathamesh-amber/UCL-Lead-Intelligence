#!/bin/bash

echo "🚀 Setting up UCL Lead Intelligence AI POC"
echo "=========================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "📝 Creating .env template..."
    echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OpenAI API key!"
    echo "   Open .env and replace 'your_openai_api_key_here' with your actual key"
else
    echo "✅ .env file found"
fi

# Check if data is ingested
if [ ! -f "data/leads.db" ]; then
    echo "📊 Ingesting lead data..."
    python src/data_ingestion.py
else
    echo "✅ Lead data already ingested"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: streamlit run app.py"
echo "3. (Optional) Create embeddings: python src/rag_system.py"
echo ""
echo "Happy analyzing! 🎓"

