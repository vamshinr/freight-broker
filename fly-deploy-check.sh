#!/bin/bash

echo "🚀 Fly.io Deployment Checklist"
echo "=============================="

echo "✅ Required files:"
echo "   📄 Dockerfile - $([ -f Dockerfile ] && echo "Present" || echo "Missing")"
echo "   📄 fly.toml - $([ -f fly.toml ] && echo "Present" || echo "Missing")"
echo "   📄 main.py - $([ -f main.py ] && echo "Present" || echo "Missing")"
echo "   📄 requirements.txt - $([ -f requirements.txt ] && echo "Present" || echo "Missing")"

echo ""
echo "🔍 Docker build test:"
if command -v docker >/dev/null 2>&1; then
    if docker build -t freight-broker-test . >/dev/null 2>&1; then
        echo "   ✅ Docker build successful"
        docker rmi freight-broker-test >/dev/null 2>&1
    else
        echo "   ❌ Docker build failed"
    fi
else
    echo "   ⚠️  Docker not installed (optional for Fly.io)"
fi

echo ""
echo "📋 Deployment commands:"
echo "   1. flyctl auth login"
echo "   2. flyctl launch --name freight-broker-api"
echo "   3. flyctl deploy"
echo ""
echo "🌐 Your app will be live at:"
echo "   https://freight-broker-api.fly.dev"
