"""
HappyRobot AI Workflow Service for Inbound Carrier Calls

This service handles automated inbound carrier calls using the HappyRobot platform.
It processes carrier inquiries, verifies credentials, and manages load assignments.
"""

import httpx
import json
from typing import Dict, Any, Optional
from app.services import verify_carrier
from app.database import loads

class HappyRobotService:
    def __init__(self):
        self.base_url = "https://api.happyrobot.ai/v1"
        self.api_key = "your_happyrobot_api_key"  # Replace with actual API key
        
    async def create_inbound_call_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an AI workflow for handling inbound carrier calls
        
        Args:
            workflow_config: Configuration for the AI workflow
            
        Returns:
            Dictionary containing workflow creation response
        """
        endpoint = f"{self.base_url}/workflows"
        
        default_workflow = {
            "name": "Inbound Carrier Call Handler",
            "description": "Automated workflow for handling inbound carrier calls",
            "triggers": [
                {
                    "type": "phone_call",
                    "phone_number": "+1-800-FREIGHT"  # Your business phone
                }
            ],
            "steps": [
                {
                    "id": "greeting",
                    "type": "voice_response",
                    "message": "Thank you for calling FreightBroker Pro. How can I help you with freight opportunities today?",
                    "collect_input": True,
                    "input_type": "speech_to_text"
                },
                {
                    "id": "carrier_identification", 
                    "type": "data_collection",
                    "prompts": [
                        "Can you please provide your MC number?",
                        "What's your company name?",
                        "What type of equipment do you have available?"
                    ],
                    "required_fields": ["mc_number", "company_name", "equipment_type"]
                },
                {
                    "id": "carrier_verification",
                    "type": "api_call",
                    "endpoint": "/verify-carrier",
                    "method": "POST",
                    "data": {
                        "mc_number": "{{mc_number}}",
                        "company_name": "{{company_name}}"
                    }
                },
                {
                    "id": "load_matching",
                    "type": "api_call", 
                    "endpoint": "/search-loads",
                    "method": "POST",
                    "data": {
                        "equipment_type": "{{equipment_type}}",
                        "origin": "{{preferred_origin}}",
                        "destination": "{{preferred_destination}}"
                    }
                },
                {
                    "id": "load_presentation",
                    "type": "voice_response",
                    "message": "I found {{load_count}} loads that match your equipment. Let me share the details with you.",
                    "dynamic_content": True
                },
                {
                    "id": "negotiation",
                    "type": "conversation_flow",
                    "allow_rate_discussion": True,
                    "rate_flexibility": 0.1  # 10% negotiation room
                },
                {
                    "id": "load_assignment",
                    "type": "conditional",
                    "condition": "agreement_reached == true",
                    "actions": [
                        {
                            "type": "api_call",
                            "endpoint": "/assign-load",
                            "method": "POST"
                        },
                        {
                            "type": "voice_response", 
                            "message": "Great! I've assigned load {{load_id}} to your company. You'll receive confirmation details via email."
                        }
                    ]
                }
            ],
            "fallback": {
                "type": "voice_response",
                "message": "I'll connect you with one of our load coordinators. Please hold while I transfer your call."
            }
        }
        
        # Merge with custom config
        workflow_config = {**default_workflow, **workflow_config}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=workflow_config,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"error": f"Request failed: {str(e)}", "success": False}
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}", "success": False}
    
    async def process_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an inbound carrier call through the AI workflow
        
        Args:
            call_data: Data from the inbound call (caller ID, audio, etc.)
            
        Returns:
            Processing result with next steps
        """
        
        # Extract carrier information from call
        mc_number = call_data.get("mc_number")
        equipment_type = call_data.get("equipment_type", "").lower()
        
        result = {
            "call_id": call_data.get("call_id"),
            "status": "processing",
            "steps_completed": [],
            "next_action": None
        }
        
        # Step 1: Verify carrier
        if mc_number:
            verification = await verify_carrier(mc_number)
            result["carrier_verified"] = verification["valid"]
            result["steps_completed"].append("carrier_verification")
            
            if not verification["valid"]:
                result["status"] = "rejected"
                result["reason"] = "Carrier verification failed"
                return result
        
        # Step 2: Find matching loads
        matching_loads = []
        for load in loads:
            if equipment_type in load.get("equipment_type", "").lower():
                matching_loads.append(load)
        
        result["matching_loads"] = matching_loads
        result["load_count"] = len(matching_loads)
        result["steps_completed"].append("load_matching")
        
        if not matching_loads:
            result["status"] = "no_matches"
            result["message"] = "No loads available for your equipment type"
            return result
        
        # Step 3: Prepare load presentation
        result["status"] = "ready_for_presentation"
        result["next_action"] = "present_loads"
        result["steps_completed"].append("load_preparation")
        
        return result
    
    async def handle_load_negotiation(self, negotiation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle load rate negotiation through AI workflow
        
        Args:
            negotiation_data: Negotiation parameters (load_id, carrier_offer, etc.)
            
        Returns:
            Negotiation result
        """
        
        load_id = negotiation_data.get("load_id")
        carrier_offer = negotiation_data.get("carrier_offer", 0)
        mc_number = negotiation_data.get("mc_number")
        
        # Find the load
        target_load = None
        for load in loads:
            if load["load_id"] == load_id:
                target_load = load
                break
        
        if not target_load:
            return {
                "success": False,
                "error": "Load not found",
                "status": "error"
            }
        
        loadboard_rate = target_load["loadboard_rate"]
        
        # AI-powered negotiation logic
        rate_difference = abs(carrier_offer - loadboard_rate) / loadboard_rate
        
        if rate_difference <= 0.05:  # Within 5%
            return {
                "success": True,
                "status": "accepted",
                "final_rate": carrier_offer,
                "message": f"Rate accepted! Load {load_id} assigned at ${carrier_offer}"
            }
        elif rate_difference <= 0.15:  # Within 15% - counter offer
            counter_offer = (carrier_offer + loadboard_rate) / 2
            return {
                "success": True,
                "status": "counter_offer",
                "counter_rate": round(counter_offer, 2),
                "message": f"How about ${counter_offer}? That works better for our margins."
            }
        else:  # Too far apart
            return {
                "success": False,
                "status": "rejected", 
                "message": f"Sorry, ${carrier_offer} is too far from our rate of ${loadboard_rate}. Can you do better?"
            }

# Global service instance
happyrobot_service = HappyRobotService()

async def create_carrier_call_workflow(workflow_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to create inbound carrier call workflow
    """
    if workflow_config is None:
        workflow_config = {}
    
    return await happyrobot_service.create_inbound_call_workflow(workflow_config)

async def process_carrier_call(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to process inbound carrier calls
    """
    return await happyrobot_service.process_inbound_call(call_data)

async def negotiate_with_ai(negotiation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for AI-powered negotiation
    """
    return await happyrobot_service.handle_load_negotiation(negotiation_data)
