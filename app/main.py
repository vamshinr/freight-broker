from fastapi import FastAPI, HTTPException, Depends, Header
from app.services import search_loads, negotiate_offer, verify_carrier
from app.enhanced_services import verify_carrier_fmcsa
from app.models import SearchRequest, NegotiationRequest, CreateLoadRequest
from app.happyrobot_service import create_carrier_call_workflow, process_carrier_call, negotiate_with_ai
from app.happyrobot_webhooks import happyrobot_router
import uuid
from app.database import loads
from app import crud
from app.db import get_db, create_tables
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

# Security - API Key authentication
API_KEY = os.getenv("API_KEY", "freight-broker-api-key-2025")

async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Verify API key for protected endpoints"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


app = FastAPI(
    title="Freight Broker API", 
    version="2.0",
    description="AI-powered freight brokerage platform with HappyRobot integration",
    contact={
        "name": "Freight Broker Support",
        "email": "support@freightbroker.com"
    }
)

# Include HappyRobot webhook router
app.include_router(happyrobot_router)

# Include analytics dashboard router
from app.analytics import dashboard_router
app.include_router(dashboard_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()

@app.get("/")
def root():
    return {"message": "Freight Broker API is running"}

@app.post("/loads/search")
def search_loads_api(req: SearchRequest):
    results = search_loads(req.origin, req.destination)
    if not results:
        raise HTTPException(status_code=404, detail="No matching loads found")
    return {"matches": results}

@app.get("/carrier/verify")
async def carrier_verify(mc_number: str):
    return await verify_carrier_fmcsa(mc_number)

@app.post("/loads/negotiate")
async def negotiate_load(req: NegotiationRequest):
    result = await negotiate_offer(req.load_id, req.carrier_offer, req.mc_number)
    return result


@app.post("/loads/create")
def create_load(req: CreateLoadRequest, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    load_id = f"L{uuid.uuid4().hex[:6].upper()}"
    new_load = {
        "load_id": load_id,
        "origin": req.origin,
        "destination": req.destination,
        "commodity": req.commodity,
        "loadboard_rate": req.loadboard_rate
    }
    created = crud.create_load(db, new_load)
    return {"message": "Load created successfully", "load": created}

@app.get("/loads")
def get_all_loads(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    return crud.get_loads(db)

# -------------------------------
# HappyRobot AI Workflow Endpoints
# -------------------------------

class WorkflowConfigRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    custom_greeting: Optional[str] = None

class InboundCallData(BaseModel):
    call_id: str
    caller_phone: Optional[str] = None
    mc_number: Optional[str] = None
    company_name: Optional[str] = None
    equipment_type: Optional[str] = None
    preferred_origin: Optional[str] = None
    preferred_destination: Optional[str] = None

class AICarrierNegotiationRequest(BaseModel):
    load_id: str
    carrier_offer: float
    mc_number: str
    call_id: Optional[str] = None

@app.post("/happyrobot/create-workflow")
async def create_workflow(config: WorkflowConfigRequest):
    """Create AI workflow for handling inbound carrier calls"""
    try:
        workflow_config = {}
        if config.name:
            workflow_config["name"] = config.name
        if config.phone_number:
            workflow_config["triggers"] = [{"type": "phone_call", "phone_number": config.phone_number}]
        if config.custom_greeting:
            workflow_config["steps"] = [{"id": "greeting", "type": "voice_response", "message": config.custom_greeting}]
        
        result = await create_carrier_call_workflow(workflow_config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@app.post("/happyrobot/process-call")
async def process_inbound_call(call_data: InboundCallData):
    """Process an inbound carrier call through AI workflow"""
    try:
        call_dict = call_data.dict()
        result = await process_carrier_call(call_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process call: {str(e)}")

@app.post("/happyrobot/negotiate")
async def ai_negotiate_load(negotiation: AICarrierNegotiationRequest):
    """Handle load negotiation with AI assistance"""
    try:
        negotiation_dict = negotiation.dict()
        result = await negotiate_with_ai(negotiation_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation failed: {str(e)}")

@app.get("/happyrobot/status")
async def workflow_status():
    """Get status of HappyRobot AI workflows"""
    return {
        "service": "HappyRobot AI Integration",
        "status": "active",
        "features": [
            "Inbound carrier call automation",
            "AI-powered load matching", 
            "Automated rate negotiation",
            "Carrier verification integration"
        ],
        "available_loads": len(loads),
        "workflow_version": "1.0"
    }