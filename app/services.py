from app.database import loads
import httpx

FMCSA_API_URL = "https://api.fmcsa.dot.gov/safer/company"  # Mocked for now

# ------------------------------
# Carrier Verification Service
# ------------------------------
async def verify_carrier(mc_number: str):
    """
    Verifies carrier MC number using FMCSA Safer API.
    """
    try:
        # For now, mock the API call since FMCSA API requires auth keys.
        # Later we'll integrate real FMCSA endpoints.
        async with httpx.AsyncClient() as client:
            # Example if FMCSA supports MC number lookup
            # response = await client.get(f"{FMCSA_API_URL}?mc_number={mc_number}")

            # Mock logic: valid carriers start with "1"
            if mc_number.startswith("1"):
                return {
                    "mc_number": mc_number,
                    "status": "active",
                    "authorized": True
                }
            else:
                return {
                    "mc_number": mc_number,
                    "status": "inactive",
                    "authorized": False
                }

    except Exception as e:
        return {
            "mc_number": mc_number,
            "status": "error",
            "authorized": False,
            "message": str(e)
        }

# ------------------------------
# Load Search Service
# ------------------------------
def search_loads(origin: str, destination: str):
    return [
        load for load in loads
        if load["origin"].lower() == origin.lower()
        and load["destination"].lower() == destination.lower()
    ]

# ------------------------------
# Negotiation Service
# ------------------------------
async def negotiate_offer(load_id: str, carrier_offer: float, mc_number: str):
    # First verify carrier
    carrier_status = await verify_carrier(mc_number)
    if not carrier_status["authorized"]:
        return {
            "status": "rejected",
            "message": "Carrier is unauthorized or inactive.",
            "final_rate": None
        }

    # Find the load by ID
    load = next((load for load in loads if load["load_id"] == load_id), None)
    if not load:
        return {"status": "error", "message": "Load not found"}

    broker_rate = load["loadboard_rate"]

    # Negotiation logic
    if carrier_offer >= broker_rate:
        return {
            "status": "accepted",
            "message": f"Offer accepted for ${carrier_offer}",
            "final_rate": carrier_offer
        }
    elif carrier_offer >= broker_rate * 0.9:
        counter_offer = (broker_rate + carrier_offer) / 2
        return {
            "status": "counter",
            "message": f"Broker counter-offers at ${counter_offer}",
            "final_rate": counter_offer
        }
    else:
        return {
            "status": "rejected",
            "message": f"Offer too low. Minimum acceptable rate is ${broker_rate}",
            "final_rate": broker_rate
        }
