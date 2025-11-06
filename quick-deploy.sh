#!/bin/bash

# Quick deployment script for production
# Run this on your server to quickly deploy the Martin Psychology App

echo "🚀 Martin Psychology App - Quick Deploy"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Set your Groq API key here or as environment variable
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  Please set your Groq API key:"
    read -p "Enter your Groq API key: " GROQ_API_KEY
    export GROQ_API_KEY
fi

# Create .env file
echo "GROQ_API_KEY=$GROQ_API_KEY" > .env

# Create necessary directories
mkdir -p data sounds images

# Deploy with Docker Compose
echo "🔨 Building and starting the application..."
docker compose up -d --build

# Wait for health check
echo "⏳ Waiting for application to start..."
sleep 15

# Check if application is running
if curl -f http://localhost:8532/_stcore/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access the app at: http://localhost:8532"
else
    echo "❌ Application failed to start. Check logs:"
    docker compose logs martin-psychology-app
fi