"""
Analytics dashboard for freight broker operations
Provides metrics, reports, and KPI tracking
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json

from app.happyrobot_webhooks import call_data_store
from app.database import loads

dashboard_router = APIRouter(prefix="/dashboard", tags=["Analytics Dashboard"])
templates = Jinja2Templates(directory="templates")

@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main analytics dashboard"""
    
    # Calculate key metrics
    metrics = calculate_dashboard_metrics()
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "metrics": metrics,
            "title": "Freight Broker Analytics Dashboard"
        }
    )

@dashboard_router.get("/api/metrics")
async def get_metrics():
    """API endpoint for dashboard metrics"""
    return calculate_dashboard_metrics()

@dashboard_router.get("/api/call-details")
async def get_call_details():
    """Get detailed call analytics"""
    
    calls = []
    for call_id, call_data in call_data_store.items():
        extracted = call_data.get("extracted_data", {})
        verification = call_data.get("verification_result", {})
        
        call_summary = {
            "call_id": call_id,
            "timestamp": call_data.get("timestamp", "Unknown"),
            "mc_number": call_data.get("mc_number", "Unknown"),
            "company_name": verification.get("company_name", "Unknown"),
            "equipment_type": call_data.get("equipment_type", "Unknown"),
            "loads_found": call_data.get("load_count", 0),
            "negotiations": len(call_data.get("negotiations", [])),
            "outcome": extracted.get("classification", "Unknown"),
            "sentiment": extracted.get("sentiment", "Unknown"),
            "duration": extracted.get("duration", 0),
            "final_rate": call_data.get("final_rate"),
            "status": call_data.get("status", "Unknown")
        }
        calls.append(call_summary)
    
    # Sort by timestamp descending
    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"calls": calls}

@dashboard_router.get("/api/load-performance")
async def get_load_performance():
    """Get load performance metrics"""
    
    load_metrics = []
    
    for load in loads:
        # Count how many times this load was discussed in calls
        discussions = 0
        assignments = 0
        
        for call_data in call_data_store.values():
            matching_loads = call_data.get("matching_loads", [])
            for match in matching_loads:
                if match.get("load_id") == load["load_id"]:
                    discussions += 1
                    if call_data.get("status") == "load_assigned":
                        assignments += 1
                    break
        
        load_metric = {
            "load_id": load["load_id"],
            "origin": load["origin"],
            "destination": load["destination"],
            "rate": load["loadboard_rate"],
            "equipment_type": load["equipment_type"],
            "discussions": discussions,
            "assignments": assignments,
            "conversion_rate": (assignments / discussions * 100) if discussions > 0 else 0
        }
        load_metrics.append(load_metric)
    
    return {"load_performance": load_metrics}

def calculate_dashboard_metrics() -> Dict[str, Any]:
    """Calculate comprehensive dashboard metrics"""
    
    total_calls = len(call_data_store)
    successful_bookings = 0
    failed_verifications = 0
    total_negotiations = 0
    total_revenue = 0.0
    sentiment_scores = []
    
    # Equipment type distribution
    equipment_distribution = {}
    
    # Hourly call distribution
    hourly_distribution = {str(i): 0 for i in range(24)}
    
    # Process each call
    for call_data in call_data_store.values():
        extracted = call_data.get("extracted_data", {})
        verification = call_data.get("verification_result", {})
        
        # Outcomes
        if extracted.get("classification") == "successful_booking":
            successful_bookings += 1
            if call_data.get("final_rate"):
                total_revenue += call_data.get("final_rate", 0)
                
        if extracted.get("classification") == "verification_failed":
            failed_verifications += 1
            
        # Negotiations
        total_negotiations += len(call_data.get("negotiations", []))
        
        # Sentiment
        sentiment_score = extracted.get("sentiment_score", 0)
        sentiment_scores.append(sentiment_score)
        
        # Equipment distribution
        equipment = call_data.get("equipment_type", "Unknown")
        equipment_distribution[equipment] = equipment_distribution.get(equipment, 0) + 1
        
        # Time distribution (mock - would use actual timestamp parsing)
        try:
            timestamp = call_data.get("timestamp", "")
            if timestamp:
                # Extract hour from timestamp (simplified)
                hour = "12"  # Mock hour
                hourly_distribution[hour] += 1
        except:
            pass
    
    # Calculate averages and rates
    success_rate = (successful_bookings / total_calls * 100) if total_calls > 0 else 0
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    avg_negotiations_per_call = total_negotiations / total_calls if total_calls > 0 else 0
    
    # Recent activity (last 7 days mock data)
    recent_activity = {
        "today": total_calls,
        "yesterday": max(0, total_calls - 2),
        "this_week": total_calls,
        "last_week": max(0, total_calls - 3)
    }
    
    return {
        "overview": {
            "total_calls": total_calls,
            "successful_bookings": successful_bookings,
            "success_rate": round(success_rate, 1),
            "failed_verifications": failed_verifications,
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_booking": round(total_revenue / successful_bookings, 2) if successful_bookings > 0 else 0
        },
        "call_quality": {
            "avg_sentiment": round(avg_sentiment, 2),
            "avg_negotiations_per_call": round(avg_negotiations_per_call, 1),
            "positive_calls": len([s for s in sentiment_scores if s > 0]),
            "negative_calls": len([s for s in sentiment_scores if s < 0]),
            "neutral_calls": len([s for s in sentiment_scores if s == 0])
        },
        "load_metrics": {
            "total_loads_available": len(loads),
            "avg_load_rate": round(sum(load["loadboard_rate"] for load in loads) / len(loads), 2) if loads else 0,
            "equipment_distribution": equipment_distribution,
            "most_popular_equipment": max(equipment_distribution.items(), key=lambda x: x[1])[0] if equipment_distribution else "N/A"
        },
        "time_analysis": {
            "hourly_distribution": hourly_distribution,
            "peak_hour": max(hourly_distribution.items(), key=lambda x: x[1])[0] if any(hourly_distribution.values()) else "N/A",
            "recent_activity": recent_activity
        },
        "conversion_funnel": {
            "total_calls": total_calls,
            "verified_carriers": total_calls - failed_verifications,
            "loads_presented": sum(1 for call in call_data_store.values() if call.get("load_count", 0) > 0),
            "negotiations_started": sum(1 for call in call_data_store.values() if len(call.get("negotiations", [])) > 0),
            "successful_bookings": successful_bookings
        },
        "performance_trends": {
            "daily_calls": [2, 3, 1, 4, 2, 1, 3],  # Mock 7-day data
            "daily_bookings": [1, 2, 0, 2, 1, 0, 1],  # Mock 7-day data
            "daily_revenue": [2100, 5100, 0, 4600, 2300, 0, 2600]  # Mock 7-day data
        }
    }
