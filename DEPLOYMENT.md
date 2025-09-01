# 🚀 Fly.io Deployment Guide for Freight Broker API

Your FastAPI freight broker app is ready to deploy on Fly.io!

## 📦 Quick Deployment Steps

### Prerequisites
```bash
# 1. Install flyctl CLI
curl -L https://fly.io/install.sh | sh

# 2. Restart your terminal or reload PATH
# Add to ~/.zshrc or ~/.bashrc: export PATH="$HOME/.fly/bin:$PATH"
```

### Deploy to Fly.io
```bash
# 1. Login to Fly.io
flyctl auth login

# 2. Launch your app (creates fly.toml if needed)
flyctl launch --name freight-broker-api

# 3. Deploy
flyctl deploy

# Your app will be live at: https://freight-broker-api.fly.dev
```

## 🔧 Configuration Files

### Dockerfile ✅ Ready
- Multi-stage Python 3.11 build
- Optimized for FastAPI + SQLite
- Auto-initializes database
- Runs on port 8000

### fly.toml ✅ Ready
- Configured for `sjc` region (San Jose)
- 512MB RAM, 1 shared CPU
- Auto-scaling enabled
- HTTPS force enabled

## 🧪 Pre-Deployment Testing

Test locally with Docker (optional):
```bash
# Build and test Docker image
docker build -t freight-broker .
docker run -p 8000:8000 freight-broker

# Test endpoints
curl http://localhost:8000/dashboard
curl -H "X-API-Key: freight-broker-key-2025-secure" http://localhost:8000/loads
```

## 🎯 What Gets Deployed

**Your live API will have:**
- `GET /dashboard` - Analytics dashboard (public)
- `GET /loads` - Available loads (API key required)
- `POST /call-data` - Submit call data (API key required)
- `GET /dashboard/api/metrics` - Dashboard metrics (public)
- `GET /dashboard/api/call-details` - Call details (public)

**API Key:** `freight-broker-key-2025-secure`

## 🚀 Complete Deployment Process

```bash
# 1. Ensure you're in the project directory
cd /path/to/freight-broker

# 2. Login to Fly.io
flyctl auth login

# 3. Launch app (follow the prompts)
flyctl launch --name freight-broker-api
# Choose region: sjc (San Jose) or closest to you
# Deploy now: Yes

# 4. Your app is live! 🎉
# Fly.io will show: https://freight-broker-api.fly.dev
```

## � Post-Deployment

After deployment, test your live API:

```bash
# Replace with your actual Fly.io URL
export API_URL="https://freight-broker-api.fly.dev"

# Test dashboard
curl $API_URL/dashboard

# Test metrics
curl $API_URL/dashboard/api/metrics

# Test protected endpoint
curl -H "X-API-Key: freight-broker-key-2025-secure" $API_URL/loads

# Submit test call data
curl -X POST "$API_URL/call-data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: freight-broker-key-2025-secure" \
  -d '{"call_id": "live-test-001", "revenue": 2500, "negotiations": null}'
```

## 💰 Fly.io Pricing

**Free Tier Includes:**
- 3 shared-cpu-1x VMs with 256MB RAM
- 160GB/month outbound data transfer
- Perfect for testing and small production loads

**Your app uses:**
- 1 VM with 512MB RAM (within free tier)
- Minimal data transfer for API calls
- SQLite database (no external DB costs)

## 🔄 Updates & Management

```bash
# Deploy updates
flyctl deploy

# View logs
flyctl logs

# SSH into your app
flyctl ssh console

# Scale your app
flyctl scale count 2  # Run 2 instances

# Monitor your app
flyctl status
```

## 🎉 That's It!

Your freight broker API will be live at `https://freight-broker-api.fly.dev` in under 5 minutes! 🚛📞

**Key Benefits of Fly.io:**
- ⚡ Global edge deployment
- 🔒 Automatic HTTPS/TLS
- 📊 Built-in monitoring
- 🌍 Multi-region support
- 💾 Persistent storage for SQLite
