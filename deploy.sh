#!/bin/bash

# Freight Broker API - Fly.io Deployment Script
# This script deploys the HappyRobot-integrated freight broker API to Fly.io

echo "🚀 Freight Broker API - HappyRobot Integration Deployment"
echo "========================================================="

# Check if fly CLI is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    echo "   export PATH=\"\$HOME/.fly/bin:\$PATH\""
    exit 1
fi

# Check if user is authenticated
if ! flyctl auth whoami &> /dev/null; then
    echo "🔑 Please authenticate with Fly.io:"
    flyctl auth login
fi

echo "🏗️  Checking if app exists..."

# Check if app exists, create if it doesn't
if ! flyctl apps list | grep -q "freight-broker-happyrobot"; then
    echo "📱 Creating new Fly.io app..."
    flyctl apps create freight-broker-happyrobot --org personal
else
    echo "✅ App freight-broker-happyrobot already exists"
fi

echo "📦 Building and deploying application..."

# Set production environment variables
echo "🔑 Setting production environment variables..."
flyctl secrets set FMCSA_API_KEY="cdc33e44d693a3a58451898d4ec9df862c65b954" --app freight-broker-happyrobot
flyctl secrets set ENVIRONMENT="production" --app freight-broker-happyrobot  
flyctl secrets set API_KEY="freight-broker-prod-$(date +%Y%m%d)" --app freight-broker-happyrobot

# Deploy to Fly.io
flyctl deploy --app freight-broker-happyrobot

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your API is now available at:"
echo "   https://freight-broker-happyrobot.fly.dev"
echo ""
echo "📊 Dashboard:"
echo "   https://freight-broker-happyrobot.fly.dev/dashboard"
echo ""
echo "🔧 API Documentation:"
echo "   https://freight-broker-happyrobot.fly.dev/docs"
echo ""
echo "🤖 HappyRobot Webhook Endpoints:"
echo "   POST https://freight-broker-happyrobot.fly.dev/webhook/happyrobot/verify-carrier"
echo "   POST https://freight-broker-happyrobot.fly.dev/webhook/happyrobot/search-loads"
echo "   POST https://freight-broker-happyrobot.fly.dev/webhook/happyrobot/negotiate-rate"
echo ""
echo "🔑 Production FMCSA API Key: cdc33e44****** (securely set as environment variable)"
echo ""
echo "📝 Next Steps:"
echo "   1. Configure HappyRobot workflow with these webhook URLs"
echo "   2. Test inbound call automation"
echo "   3. Monitor dashboard for analytics"
echo ""
