from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sqlite3
import re
from datetime import datetime
import os

app = FastAPI(
    title="Freight Broker API", 
    version="3.0",
    description="Simplified freight brokerage platform"
)

# API Key for authentication
API_KEY = "freight-broker-key-2025-secure"

async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Verify API key for protected endpoints"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Database setup
DATABASE_FILE = "freight_broker.db"

def init_database():
    """Initialize SQLite database with tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create call_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE NOT NULL,
            transcript TEXT,
            duration INTEGER,
            sentiment TEXT,
            outcome TEXT,
            revenue INTEGER,
            negotiations INTEGER,
            timestamp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class CallDataRequest(BaseModel):
    call_id: str
    transcript: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds as integer
    sentiment: Optional[str] = None  # String sentiment
    outcome: Optional[str] = None    # String outcome
    revenue: Optional[int] = None    # Revenue as integer
    negotiations: Optional[Any] = None  # Accept any format - string, int, null

# Helper functions for data conversion
def safe_int_convert(value: Any) -> int:
    """Safely convert any value to integer, handling various formats"""
    if value is None:
        return 0
    
    if isinstance(value, (int, float)):
        return int(value)
    
    if isinstance(value, str):
        # Remove common text and extract numbers
        value = value.lower()
        value = re.sub(r'[^\d.]', '', value)  # Keep only digits and decimals
        if value:
            try:
                return int(float(value))
            except ValueError:
                return 0
    
    return 0

def safe_revenue_convert(value: Any) -> Optional[int]:
    """Safely convert any value to integer for revenue"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            # Remove currency symbols, commas, and extra text
            cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return int(float(cleaned)) if cleaned else None
        except (ValueError, TypeError):
            return None
    return None

def normalize_sentiment(value: str) -> str:
    """Normalize sentiment string"""
    if not value:
        return "Unknown"
    sentiment_lower = str(value).lower().strip()
    if sentiment_lower in ['positive', 'pos', 'good', 'happy']:
        return "Positive"
    elif sentiment_lower in ['negative', 'neg', 'bad', 'unhappy']:
        return "Negative"
    elif sentiment_lower in ['neutral', 'neut', 'ok', 'normal']:
        return "Neutral"
    else:
        return value.title()

def normalize_outcome(value: str) -> str:
    """Normalize outcome string"""
    if not value:
        return "Unknown"
    outcome_lower = str(value).lower().strip()
    if 'accept' in outcome_lower or 'book' in outcome_lower or 'success' in outcome_lower:
        return "Offer accepted"
    elif 'reject' in outcome_lower or 'decline' in outcome_lower:
        return "Rate Rejected"
    elif 'no load' in outcome_lower or 'not found' in outcome_lower:
        return "No Loads Found"
    elif 'fail' in outcome_lower or 'ineligible' in outcome_lower:
        return "Eligibility Failed"
    else:
        return str(value).title()

# Load data
loads = [
    {
        "load_id": "L123",
        "origin": "Dallas, TX",
        "destination": "Atlanta, GA",
        "pickup_datetime": "2025-08-27T09:00:00-05:00",
        "delivery_datetime": "2025-08-29T17:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 2100,
        "notes": "FCFS 08:00-14:00",
        "weight": 42000,
        "commodity_type": "consumer goods",
        "miles": 780,
        "dimensions": "48x40 pallets",
        "num_of_pieces": 22
    },
    {
        "load_id": "L456",
        "origin": "Fort Worth, TX",
        "destination": "Jacksonville, FL",
        "pickup_datetime": "2025-08-27T08:00:00-05:00",
        "delivery_datetime": "2025-08-29T16:00:00-04:00",
        "equipment_type": "reefer",
        "loadboard_rate": 2600,
        "notes": "Appt req",
        "weight": 38000,
        "commodity_type": "foodstuffs",
        "miles": 980,
        "dimensions": None,
        "num_of_pieces": 20
    },
    {
        "load_id": "L789",
        "origin": "Dallas, TX",
        "destination": "Charlotte, NC",
        "pickup_datetime": "2025-08-28T10:00:00-05:00",
        "delivery_datetime": "2025-08-30T12:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 2300,
        "notes": "No detention",
        "weight": 41000,
        "commodity_type": "consumer goods",
        "miles": 1000,
        "dimensions": None,
        "num_of_pieces": None
    },
    {
        "load_id": "L901",
        "origin": "Phoenix, AZ",
        "destination": "Denver, CO",
        "pickup_datetime": "2025-08-29T07:00:00-07:00",
        "delivery_datetime": "2025-08-31T15:00:00-06:00",
        "equipment_type": "flatbed",
        "loadboard_rate": 2850,
        "notes": "Tarps required",
        "weight": 45000,
        "commodity_type": "steel coils",
        "miles": 1180,
        "dimensions": "48x102 flatbed",
        "num_of_pieces": 8
    },
    {
        "load_id": "L234",
        "origin": "Miami, FL",
        "destination": "Nashville, TN",
        "pickup_datetime": "2025-08-30T12:00:00-04:00",
        "delivery_datetime": "2025-09-01T18:00:00-05:00",
        "equipment_type": "reefer",
        "loadboard_rate": 2450,
        "notes": "Temp control req",
        "weight": 35000,
        "commodity_type": "produce",
        "miles": 850,
        "dimensions": "53ft reefer",
        "num_of_pieces": 24
    },
    {
        "load_id": "L567",
        "origin": "Los Angeles, CA",
        "destination": "Chicago, IL",
        "pickup_datetime": "2025-08-31T06:00:00-07:00",
        "delivery_datetime": "2025-09-02T14:00:00-05:00",
        "equipment_type": "dry van",
        "loadboard_rate": 3200,
        "notes": "High value freight - team drivers preferred",
        "weight": 44000,
        "commodity_type": "electronics",
        "miles": 2015,
        "dimensions": "53ft dry van",
        "num_of_pieces": 18
    },
    {
        "load_id": "L890",
        "origin": "Seattle, WA",
        "destination": "Houston, TX",
        "pickup_datetime": "2025-09-01T10:00:00-07:00",
        "delivery_datetime": "2025-09-03T16:00:00-05:00",
        "equipment_type": "reefer",
        "loadboard_rate": 3800,
        "notes": "Keep frozen -10°F",
        "weight": 40000,
        "commodity_type": "frozen seafood",
        "miles": 2350,
        "dimensions": "53ft reefer",
        "num_of_pieces": 26
    },
    {
        "load_id": "L112",
        "origin": "Atlanta, GA",
        "destination": "New York, NY",
        "pickup_datetime": "2025-09-02T08:00:00-04:00",
        "delivery_datetime": "2025-09-03T20:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 1850,
        "notes": "Multiple stops - retail distribution",
        "weight": 39000,
        "commodity_type": "apparel",
        "miles": 875,
        "dimensions": "48ft dry van",
        "num_of_pieces": 32
    },
    {
        "load_id": "L334",
        "origin": "Portland, OR",
        "destination": "Salt Lake City, UT",
        "pickup_datetime": "2025-09-03T07:00:00-07:00",
        "delivery_datetime": "2025-09-04T18:00:00-06:00",
        "equipment_type": "flatbed",
        "loadboard_rate": 2100,
        "notes": "Lumber load - straps and blocking required",
        "weight": 47000,
        "commodity_type": "lumber",
        "miles": 765,
        "dimensions": "48x102 flatbed",
        "num_of_pieces": 45
    },
    {
        "load_id": "L445",
        "origin": "Boston, MA",
        "destination": "Orlando, FL",
        "pickup_datetime": "2025-09-04T11:00:00-04:00",
        "delivery_datetime": "2025-09-06T15:00:00-04:00",
        "equipment_type": "step deck",
        "loadboard_rate": 3500,
        "notes": "Oversize load - permits included",
        "weight": 52000,
        "commodity_type": "machinery",
        "miles": 1285,
        "dimensions": "48x102 step deck",
        "num_of_pieces": 1
    }
]

# API Endpoints

@app.get("/loads")
async def get_loads(api_key: str = Depends(verify_api_key)):
    """Get all available loads (requires API key)"""
    return {
        "status": "success",
        "loads": loads,
        "total_loads": len(loads)
    }

@app.post("/call-data")
async def receive_call_data(call_data: CallDataRequest, api_key: str = Depends(verify_api_key)):
    """Store call data in database (requires API key)"""
    try:
        # Process and convert the data
        processed_duration = call_data.duration or 0  # Duration already integer in seconds
        processed_revenue = safe_revenue_convert(call_data.revenue)  # Convert to integer or None
        # Keep negotiations as integer or None (don't convert null to 0)
        processed_negotiations = call_data.negotiations if call_data.negotiations is not None else None
        if processed_negotiations is not None and not isinstance(processed_negotiations, int):
            processed_negotiations = safe_int_convert(processed_negotiations)
        processed_sentiment = normalize_sentiment(call_data.sentiment) if call_data.sentiment else "Unknown"
        processed_outcome = normalize_outcome(call_data.outcome) if call_data.outcome else "Unknown"
        
        # Store in database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO call_data 
            (call_id, transcript, duration, sentiment, outcome, revenue, negotiations, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_data.call_id,
            call_data.transcript,
            processed_duration,
            processed_sentiment,
            processed_outcome,
            processed_revenue,
            processed_negotiations,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Call data stored successfully",
            "call_id": call_data.call_id,
            "processed_values": {
                "duration": processed_duration,
                "revenue": processed_revenue,
                "negotiations": processed_negotiations,
                "sentiment": processed_sentiment,
                "outcome": processed_outcome
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store call data: {str(e)}")

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the analytics dashboard"""
    try:
        with open("templates/dashboard.html", "r") as f:
            html_content = f.read()
        
        # Replace template variables
        html_content = html_content.replace("{{title}}", "Freight Broker Dashboard")
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")

@app.get("/dashboard/api/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics from database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get all call data
        cursor.execute('SELECT * FROM call_data ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        # Calculate metrics
        total_calls = len(rows)
        total_revenue = sum(int(row[6]) if row[6] is not None else 0 for row in rows)  # revenue column as integer
        
        if total_calls > 0:
            avg_duration = sum(row[3] or 0 for row in rows) // total_calls  # duration column
            # Handle null negotiations properly
            negotiations_values = [row[7] for row in rows if row[7] is not None]
            avg_negotiations = sum(negotiations_values) / len(negotiations_values) if negotiations_values else 0
        else:
            avg_duration = 0
            avg_negotiations = 0
        
        # Success rate (accepted + booked outcomes)
        successful_outcomes = sum(1 for row in rows 
                                if row[5] and ('accept' in row[5].lower() or 'book' in row[5].lower()))
        success_rate = (successful_outcomes / total_calls * 100) if total_calls > 0 else 0
        
        conn.close()
        
        return {
            "total_calls": total_calls,
            "total_revenue": total_revenue,  # Already integer
            "avg_duration": avg_duration,
            "avg_negotiations": round(avg_negotiations, 1),
            "success_rate": round(success_rate, 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/dashboard/api/call-details")
async def get_call_details():
    """Get detailed call data for dashboard tables and charts"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT call_id, transcript, duration, sentiment, outcome, revenue, negotiations, timestamp
            FROM call_data 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        rows = cursor.fetchall()
        
        calls = []
        for row in rows:
            calls.append({
                "call_id": row[0],
                "transcript": row[1],
                "duration": row[2] or 0,
                "sentiment": row[3] or "Unknown",
                "outcome": row[4] or "Unknown", 
                "revenue": int(row[5]) if row[5] is not None else None,  # Revenue as integer or None
                "negotiations": row[6] if row[6] is not None else None,  # Keep null as None, don't convert to 0
                "call_time": row[7],
                "timestamp": row[7]
            })
        
        conn.close()
        
        return calls
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get call details: {str(e)}")

# Load data
loads = [
    {
        "load_id": "L123",
        "origin": "Dallas, TX",
        "destination": "Atlanta, GA",
        "pickup_datetime": "2025-08-27T09:00:00-05:00",
        "delivery_datetime": "2025-08-29T17:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 2100,
        "notes": "FCFS 08:00-14:00",
        "weight": 42000,
        "commodity_type": "consumer goods",
        "miles": 780,
        "dimensions": "48x40 pallets",
        "num_of_pieces": 22
    },
    {
        "load_id": "L456",
        "origin": "Fort Worth, TX",
        "destination": "Jacksonville, FL",
        "pickup_datetime": "2025-08-27T08:00:00-05:00",
        "delivery_datetime": "2025-08-29T16:00:00-04:00",
        "equipment_type": "reefer",
        "loadboard_rate": 2600,
        "notes": "Appt req",
        "weight": 38000,
        "commodity_type": "foodstuffs",
        "miles": 980,
        "dimensions": None,
        "num_of_pieces": 20
    },
    {
        "load_id": "L789",
        "origin": "Dallas, TX",
        "destination": "Charlotte, NC",
        "pickup_datetime": "2025-08-28T10:00:00-05:00",
        "delivery_datetime": "2025-08-30T12:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 2300,
        "notes": "No detention",
        "weight": 41000,
        "commodity_type": "consumer goods",
        "miles": 1000,
        "dimensions": None,
        "num_of_pieces": None
    },
    {
        "load_id": "L901",
        "origin": "Phoenix, AZ",
        "destination": "Denver, CO",
        "pickup_datetime": "2025-08-29T07:00:00-07:00",
        "delivery_datetime": "2025-08-31T15:00:00-06:00",
        "equipment_type": "flatbed",
        "loadboard_rate": 2850,
        "notes": "Tarps required",
        "weight": 45000,
        "commodity_type": "steel coils",
        "miles": 1180,
        "dimensions": "48x102 flatbed",
        "num_of_pieces": 8
    },
    {
        "load_id": "L234",
        "origin": "Miami, FL",
        "destination": "Nashville, TN",
        "pickup_datetime": "2025-08-30T12:00:00-04:00",
        "delivery_datetime": "2025-09-01T18:00:00-05:00",
        "equipment_type": "reefer",
        "loadboard_rate": 2450,
        "notes": "Temp control req",
        "weight": 35000,
        "commodity_type": "produce",
        "miles": 850,
        "dimensions": "53ft reefer",
        "num_of_pieces": 24
    },
    {
        "load_id": "L567",
        "origin": "Los Angeles, CA",
        "destination": "Chicago, IL",
        "pickup_datetime": "2025-08-31T06:00:00-07:00",
        "delivery_datetime": "2025-09-02T14:00:00-05:00",
        "equipment_type": "dry van",
        "loadboard_rate": 3200,
        "notes": "High value freight - team drivers preferred",
        "weight": 44000,
        "commodity_type": "electronics",
        "miles": 2015,
        "dimensions": "53ft dry van",
        "num_of_pieces": 18
    },
    {
        "load_id": "L890",
        "origin": "Seattle, WA",
        "destination": "Houston, TX",
        "pickup_datetime": "2025-09-01T10:00:00-07:00",
        "delivery_datetime": "2025-09-03T16:00:00-05:00",
        "equipment_type": "reefer",
        "loadboard_rate": 3800,
        "notes": "Keep frozen -10°F",
        "weight": 40000,
        "commodity_type": "frozen seafood",
        "miles": 2350,
        "dimensions": "53ft reefer",
        "num_of_pieces": 26
    },
    {
        "load_id": "L112",
        "origin": "Atlanta, GA",
        "destination": "New York, NY",
        "pickup_datetime": "2025-09-02T08:00:00-04:00",
        "delivery_datetime": "2025-09-03T20:00:00-04:00",
        "equipment_type": "dry van",
        "loadboard_rate": 1850,
        "notes": "Multiple stops - retail distribution",
        "weight": 39000,
        "commodity_type": "apparel",
        "miles": 875,
        "dimensions": "48ft dry van",
        "num_of_pieces": 32
    },
    {
        "load_id": "L334",
        "origin": "Portland, OR",
        "destination": "Salt Lake City, UT",
        "pickup_datetime": "2025-09-03T07:00:00-07:00",
        "delivery_datetime": "2025-09-04T18:00:00-06:00",
        "equipment_type": "flatbed",
        "loadboard_rate": 2100,
        "notes": "Lumber load - straps and blocking required",
        "weight": 47000,
        "commodity_type": "lumber",
        "miles": 765,
        "dimensions": "48x102 flatbed",
        "num_of_pieces": 45
    },
    {
        "load_id": "L445",
        "origin": "Boston, MA",
        "destination": "Orlando, FL",
        "pickup_datetime": "2025-09-04T11:00:00-04:00",
        "delivery_datetime": "2025-09-06T15:00:00-04:00",
        "equipment_type": "step deck",
        "loadboard_rate": 3500,
        "notes": "Oversize load - permits included",
        "weight": 52000,
        "commodity_type": "machinery",
        "miles": 1285,
        "dimensions": "48x102 step deck",
        "num_of_pieces": 1
    }
]

if __name__ == "__main__":
    # Initialize database when running directly
    init_database()
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
