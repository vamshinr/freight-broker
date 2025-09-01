# Freight Broker API - Clean Implementation

## 🚀 Final Implementation Summary

**Project Structure:**
```
freight-broker/
├── main.py              # Single file with all functionality
├── requirements.txt     # Minimal dependencies (FastAPI, Uvicorn, Pydantic)
├── templates/
│   └── dashboard.html   # Visual analytics dashboard
├── freight_broker.db    # SQLite database
└── .venv/              # Python virtual environment
```

## 🔗 API Endpoints

### 1. GET /loads (Protected)
- **Authentication**: Requires `X-API-Key` header
- **Purpose**: Returns all 10 available freight loads
- **Response**: JSON with load details (origin, destination, rates, equipment type)

### 2. POST /call-data (Protected)  
- **Authentication**: Requires `X-API-Key` header
- **Purpose**: Store call data in SQLite database
- **Data Types**:
  - `duration`: Integer (seconds)
  - `revenue`: Integer 
  - `sentiment`: String
  - `outcome`: String
  - `negotiations`: Any (null becomes 0)

### 3. GET /dashboard (Public)
- **Authentication**: No API key required
- **Purpose**: Visual analytics dashboard with charts and metrics
- **Features**: Real-time call metrics, visual charts, activity table with negotiations column

## 🔑 Authentication

**API Key**: `freight-broker-key-2025-secure`

**Usage Examples:**
```bash
# Get loads (requires API key)
curl -H "X-API-Key: freight-broker-key-2025-secure" "http://localhost:8000/loads"

# Post call data (requires API key)
curl -X POST "http://localhost:8000/call-data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: freight-broker-key-2025-secure" \
  -d '{
    "call_id": "call-001",
    "transcript": "Carrier inquiry about loads",
    "duration": 300,
    "sentiment": "Positive", 
    "outcome": "Offer accepted",
    "revenue": 2500,
    "negotiations": null
  }'

# View dashboard (no API key needed)
curl "http://localhost:8000/dashboard"
```

## ✅ Key Features

- **API Key Security**: Protected endpoints for loads and call data
- **Null Safety**: `negotiations: null` automatically becomes `0`
- **Data Type Validation**: Duration and revenue as integers, others as strings
- **Visual Analytics**: Interactive dashboard with Chart.js
- **Clean Codebase**: Single main.py file with all functionality
- **SQLite Storage**: Persistent database for call data

## 🚀 How to Run

```bash
cd freight-broker
python -m uvicorn main:app --port 8000 &
```

Then access:
- Dashboard: http://localhost:8000/dashboard
- API docs: http://localhost:8000/docs
