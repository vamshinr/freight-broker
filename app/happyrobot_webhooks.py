"""
HappyRobot webhook endpoints for inbound carrier call automation
Handles carrier verification, load matching, and negotiation
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import uuid
from datetime import datetime

from app.database import loads
from app.enhanced_services import verify_carrier_fmcsa, get_load_matcher, negotiate_rate

# Create router for HappyRobot webhooks
happyrobot_router = APIRouter(prefix="/webhook/happyrobot", tags=["HappyRobot Webhooks"])

# Pydantic models for HappyRobot webhook payloads
class CarrierVerificationRequest(BaseModel):
    mc_number: str = Field(..., description="Motor Carrier number to verify")
    call_id: Optional[str] = Field(None, description="Unique call identifier")

class LoadSearchRequest(BaseModel):
    equipment_type: str = Field(..., description="Equipment type (dry van, reefer, flatbed)")
    origin_state: Optional[str] = Field(None, description="Preferred origin state")
    destination_state: Optional[str] = Field(None, description="Preferred destination state") 
    min_rate: Optional[float] = Field(None, description="Minimum acceptable rate")
    max_miles: Optional[int] = Field(None, description="Maximum miles willing to travel")
    call_id: Optional[str] = Field(None, description="Unique call identifier")

class RateNegotiationRequest(BaseModel):
    load_id: str = Field(..., description="Load identifier")
    carrier_offer: float = Field(..., description="Carrier's rate offer")
    negotiation_round: Optional[int] = Field(1, description="Current negotiation round")
    mc_number: Optional[str] = Field(None, description="Carrier MC number")
    call_id: Optional[str] = Field(None, description="Unique call identifier")

class CallTranscriptRequest(BaseModel):
    call_id: str = Field(..., description="Unique call identifier")
    transcript: str = Field(..., description="Full call transcript")
    duration: Optional[int] = Field(None, description="Call duration in seconds")
    outcome: Optional[str] = Field(None, description="Call outcome classification")

# In-memory storage for call data (in production, use database)
call_data_store: Dict[str, Dict] = {}

@happyrobot_router.post("/verify-carrier")
async def verify_carrier_webhook(request: CarrierVerificationRequest):
    """
    Webhook endpoint for FMCSA carrier verification
    Called by HappyRobot AI agent during inbound calls
    """
    try:
        # Verify carrier with FMCSA
        verification_result = await verify_carrier_fmcsa(request.mc_number)
        
        # Store call data
        if request.call_id:
            call_data_store[request.call_id] = {
                **call_data_store.get(request.call_id, {}),
                "mc_number": request.mc_number,
                "verification_result": verification_result,
                "timestamp": datetime.now().isoformat()
            }
        
        # Format response for HappyRobot AI agent
        if verification_result["valid"]:
            response_message = (
                f"Great! I've verified your MC number {verification_result['mc_number']}. "
                f"Your company {verification_result.get('company_name', 'is')} is active and in good standing. "
                f"Let me find some loads that match your equipment."
            )
        else:
            response_message = (
                f"I'm having trouble verifying MC number {request.mc_number}. "
                f"Could you double-check that number? I want to make sure we have you set up correctly."
            )
            
        return {
            "success": verification_result["valid"],
            "verification": verification_result,
            "response_message": response_message,
            "next_action": "search_loads" if verification_result["valid"] else "retry_verification"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@happyrobot_router.post("/search-loads")
async def search_loads_webhook(request: LoadSearchRequest):
    """
    Webhook endpoint for load searching and matching
    Called by HappyRobot AI agent after carrier verification
    """
    try:
        # Get load matcher service
        load_matcher = get_load_matcher(loads)
        
        # Search for matching loads
        matching_loads = load_matcher.search_loads(
            equipment_type=request.equipment_type,
            origin_state=request.origin_state,
            destination_state=request.destination_state,
            min_rate=request.min_rate,
            max_miles=request.max_miles
        )
        
        # Store call data
        if request.call_id:
            call_data_store[request.call_id] = {
                **call_data_store.get(request.call_id, {}),
                "equipment_type": request.equipment_type,
                "search_criteria": request.dict(),
                "matching_loads": matching_loads,
                "load_count": len(matching_loads),
                "timestamp": datetime.now().isoformat()
            }
        
        # Format response for AI agent
        if matching_loads:
            best_load = matching_loads[0]
            response_message = (
                f"Perfect! I found {len(matching_loads)} loads for your {request.equipment_type}. "
                f"The best match is load {best_load['load_id']} going from {best_load['origin']} "
                f"to {best_load['destination']} for ${best_load['loadboard_rate']}. "
                f"It's {best_load.get('miles', 'unknown')} miles and picks up {best_load.get('pickup_datetime', 'soon')}. "
                f"Are you interested in this load?"
            )
            
            # Prepare load details for negotiation
            load_details = {
                "load_id": best_load["load_id"],
                "route": f"{best_load['origin']} to {best_load['destination']}",
                "rate": best_load["loadboard_rate"],
                "miles": best_load.get("miles"),
                "pickup": best_load.get("pickup_datetime"),
                "delivery": best_load.get("delivery_datetime"),
                "equipment": best_load.get("equipment_type"),
                "notes": best_load.get("notes")
            }
        else:
            response_message = (
                f"I don't have any loads right now that match your {request.equipment_type} "
                f"in your preferred areas. Can you be flexible on location or equipment type? "
                f"Or I can take your contact info and call you when something comes up."
            )
            load_details = None
            
        return {
            "success": len(matching_loads) > 0,
            "load_count": len(matching_loads),
            "matching_loads": matching_loads,
            "recommended_load": load_details,
            "response_message": response_message,
            "next_action": "present_load" if matching_loads else "take_contact_info"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load search failed: {str(e)}")

@happyrobot_router.post("/negotiate-rate")
async def negotiate_rate_webhook(request: RateNegotiationRequest):
    """
    Webhook endpoint for rate negotiation
    Called by HappyRobot AI agent during rate discussions
    """
    try:
        # Find the load
        target_load = None
        for load in loads:
            if load["load_id"] == request.load_id:
                target_load = load
                break
                
        if not target_load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        # Get carrier history (if available)
        carrier_history = None
        if request.mc_number and request.call_id:
            # In production, fetch from database
            carrier_history = {"reliability_score": 85}  # Mock data
        
        # Negotiate the rate
        negotiation_result = negotiate_rate(
            load_rate=target_load["loadboard_rate"],
            carrier_offer=request.carrier_offer,
            negotiation_round=request.negotiation_round,
            carrier_history=carrier_history
        )
        
        # Store negotiation data
        if request.call_id:
            negotiations = call_data_store.get(request.call_id, {}).get("negotiations", [])
            negotiations.append({
                "round": request.negotiation_round,
                "carrier_offer": request.carrier_offer,
                "result": negotiation_result,
                "timestamp": datetime.now().isoformat()
            })
            
            call_data_store[request.call_id] = {
                **call_data_store.get(request.call_id, {}),
                "negotiations": negotiations,
                "latest_negotiation": negotiation_result
            }
        
        # Format response based on negotiation outcome
        response = {
            "success": True,
            "decision": negotiation_result["decision"],
            "message": negotiation_result["message"],
            "negotiation_complete": negotiation_result.get("negotiation_complete", False)
        }
        
        if negotiation_result["decision"] == "accept":
            response.update({
                "final_rate": negotiation_result["final_rate"],
                "next_action": "confirm_load"
            })
        elif negotiation_result["decision"] == "counter_offer":
            response.update({
                "counter_rate": negotiation_result["counter_rate"],
                "negotiation_round": negotiation_result.get("negotiation_round", request.negotiation_round + 1),
                "next_action": "await_response"
            })
        elif negotiation_result["decision"] == "transfer":
            response.update({
                "next_action": "transfer_call"
            })
        else:  # decline
            response.update({
                "next_action": "end_call"
            })
            
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

@happyrobot_router.post("/confirm-load")
async def confirm_load_webhook(request: Dict[str, Any]):
    """
    Webhook endpoint for load confirmation and assignment
    Called when carrier accepts a load
    """
    try:
        call_id = request.get("call_id")
        load_id = request.get("load_id")
        final_rate = request.get("final_rate")
        mc_number = request.get("mc_number")
        
        # Generate confirmation number
        confirmation_number = f"CONF-{uuid.uuid4().hex[:8].upper()}"
        
        # Store confirmation data
        if call_id:
            call_data_store[call_id] = {
                **call_data_store.get(call_id, {}),
                "status": "load_assigned",
                "confirmation_number": confirmation_number,
                "final_rate": final_rate,
                "assignment_time": datetime.now().isoformat()
            }
        
        response_message = (
            f"Excellent! Load {load_id} is assigned to you at ${final_rate}. "
            f"Your confirmation number is {confirmation_number}. "
            f"You'll receive pickup details via email within 15 minutes. "
            f"Thanks for choosing us, and drive safe!"
        )
        
        return {
            "success": True,
            "confirmation_number": confirmation_number,
            "load_assigned": True,
            "response_message": response_message,
            "next_action": "transfer_to_dispatch"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load confirmation failed: {str(e)}")

@happyrobot_router.post("/extract-call-data") 
async def extract_call_data_webhook(request: CallTranscriptRequest):
    """
    Webhook endpoint for call data extraction and classification
    Called after call completion for analytics
    """
    try:
        call_data = call_data_store.get(request.call_id, {})
        
        # Extract key information from transcript using simple keyword analysis
        # In production, use more sophisticated NLP
        transcript_lower = request.transcript.lower()
        
        extracted_data = {
            "call_id": request.call_id,
            "duration": request.duration,
            "outcome": request.outcome,
            "transcript_length": len(request.transcript),
            "carrier_info": call_data.get("verification_result", {}),
            "loads_discussed": call_data.get("load_count", 0),
            "negotiations": len(call_data.get("negotiations", [])),
            "final_outcome": call_data.get("status", "unknown"),
            "extracted_at": datetime.now().isoformat()
        }
        
        # Sentiment analysis (basic keyword-based)
        positive_words = ["great", "perfect", "excellent", "good", "yes", "sure", "sounds good"]
        negative_words = ["no", "can't", "won't", "disappointed", "frustrated", "problem"]
        
        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"  
        else:
            sentiment = "neutral"
            
        extracted_data["sentiment"] = sentiment
        extracted_data["sentiment_score"] = positive_count - negative_count
        
        # Classification based on outcome
        if call_data.get("status") == "load_assigned":
            classification = "successful_booking"
        elif "negotiations" in call_data and len(call_data["negotiations"]) > 0:
            classification = "negotiation_attempted"
        elif call_data.get("verification_result", {}).get("valid") == False:
            classification = "verification_failed"
        else:
            classification = "no_suitable_loads"
            
        extracted_data["classification"] = classification
        
        # Update stored call data
        call_data_store[request.call_id] = {
            **call_data,
            "extracted_data": extracted_data,
            "processing_complete": True
        }
        
        return {
            "success": True,
            "extracted_data": extracted_data,
            "message": "Call data extracted and classified successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data extraction failed: {str(e)}")

@happyrobot_router.get("/call-analytics/{call_id}")
async def get_call_analytics(call_id: str):
    """
    Get detailed analytics for a specific call
    """
    if call_id not in call_data_store:
        raise HTTPException(status_code=404, detail="Call data not found")
        
    return {
        "success": True,
        "call_data": call_data_store[call_id]
    }

@happyrobot_router.get("/call-analytics")
async def get_all_call_analytics():
    """
    Get analytics for all processed calls
    """
    analytics_summary = {
        "total_calls": len(call_data_store),
        "successful_bookings": 0,
        "failed_verifications": 0,
        "negotiation_attempts": 0,
        "average_sentiment": 0,
        "calls": list(call_data_store.values())
    }
    
    total_sentiment = 0
    for call_data in call_data_store.values():
        extracted = call_data.get("extracted_data", {})
        
        if extracted.get("classification") == "successful_booking":
            analytics_summary["successful_bookings"] += 1
        elif extracted.get("classification") == "verification_failed":
            analytics_summary["failed_verifications"] += 1
        elif "negotiation" in extracted.get("classification", ""):
            analytics_summary["negotiation_attempts"] += 1
            
        total_sentiment += extracted.get("sentiment_score", 0)
    
    if len(call_data_store) > 0:
        analytics_summary["average_sentiment"] = total_sentiment / len(call_data_store)
        analytics_summary["success_rate"] = (analytics_summary["successful_bookings"] / len(call_data_store)) * 100
    
    return analytics_summary
