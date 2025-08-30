# HappyRobot AI Workflow Configuration
## Inbound Carrier Sales Automation

### Overview
This document provides step-by-step instructions for configuring HappyRobot AI to automate inbound carrier calls for freight brokerage operations.

## 🔑 API Configuration

### Environment Variables
The system uses environment variables for secure API key management:

**Local Development:**
```bash
# Copy example environment file
cp .env.example .env

# Environment variables are pre-configured with production FMCSA API key
FMCSA_API_KEY=cdc33e44d693a3a58451898d4ec9df862c65b954
```

**Production (Fly.io):**
```bash
# Production secrets are automatically set during deployment
# See deploy.sh for secure environment variable configuration
```

---

## 🤖 Workflow Configuration

### 1. Create New Workflow
1. Login to HappyRobot platform
2. Click "Create New Workflow"
3. Select "Inbound Call" template

### 2. Configure Trigger
**Trigger Type**: Phone Calls > Inbound to Number
- **To Number**: Use web call trigger feature (no phone number purchase needed)
- **Description**: "Inbound carrier load booking"

### 3. Configure AI Agent
**Action Type**: AI Agent > Inbound Voice Agent

#### Agent Settings:
- **Name**: "FreightBot - Carrier Sales Agent"
- **Voice**: Select preferred voice (recommend professional female voice)
- **Language**: English (US)
- **Initial Message**: "Thank you for calling FreightBroker Pro! I'm here to help you find profitable loads. May I get your MC number to get started?"

#### Agent Prompt:
```
You are a professional freight broker sales agent specializing in carrier relations. Your role is to:

1. Greet carriers professionally and warmly
2. Collect their MC number for verification
3. Identify their equipment type and preferences
4. Match them with suitable loads from our system
5. Present load details clearly and persuasively
6. Handle rate negotiations professionally (up to 3 rounds)
7. Confirm load assignments and provide next steps

Key Guidelines:
- Always verify carrier credentials before discussing loads
- Present loads with enthusiasm but realistic expectations
- Be flexible during negotiations but protect margins
- Use transportation industry terminology appropriately
- Transfer complex negotiations to human dispatchers when needed

Available load information includes: origin, destination, pickup/delivery times, equipment type, rate, miles, weight, commodity type, and special notes.

Stay professional, helpful, and focused on building long-term carrier relationships.
```

#### Keyterms Configuration:
Add these important terms for better recognition:
- MC numbers: "MC-123456", "Motor Carrier"
- Equipment: "dry van", "reefer", "flatbed", "step deck"
- States: "TX", "FL", "CA", "IL" (common freight lanes)
- Load terms: "loadboard", "pickup", "delivery", "detention"

---

## 🛠️ Tool Configuration

### Tool 1: Carrier Verification
**Function Name**: verify_carrier
**Description**: "Verify carrier MC number with FMCSA database"
**Message Type**: AI
**Example Message**: "Let me verify your MC number in our system..."

**Parameters**:
- `mc_number` (required): Carrier's MC number
- `call_id` (optional): Unique call identifier

**Webhook URL**: 
```
POST https://your-app.fly.dev/webhook/happyrobot/verify-carrier
```

**Headers**:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer freight-broker-api-key-2025"
}
```

### Tool 2: Load Search
**Function Name**: search_loads
**Description**: "Search for loads matching carrier equipment and preferences"
**Message Type**: AI
**Example Message**: "Perfect! Let me find loads that match your equipment..."

**Parameters**:
- `equipment_type` (required): Type of trailer/equipment
- `origin_state` (optional): Preferred pickup state
- `destination_state` (optional): Preferred delivery state
- `min_rate` (optional): Minimum acceptable rate
- `max_miles` (optional): Maximum distance willing to travel
- `call_id` (optional): Call tracking ID

**Webhook URL**:
```
POST https://your-app.fly.dev/webhook/happyrobot/search-loads
```

### Tool 3: Rate Negotiation
**Function Name**: negotiate_rate
**Description**: "Handle rate negotiation with AI-powered responses"
**Message Type**: Fixed
**Fixed Message**: "Let me see what I can do on the rate..."

**Parameters**:
- `load_id` (required): Load identifier being negotiated
- `carrier_offer` (required): Carrier's rate offer
- `negotiation_round` (optional): Current negotiation round
- `mc_number` (optional): Carrier MC number
- `call_id` (optional): Call tracking

**Webhook URL**:
```
POST https://your-app.fly.dev/webhook/happyrobot/negotiate-rate
```

### Tool 4: Load Confirmation  
**Function Name**: confirm_load
**Description**: "Confirm and assign load to carrier"
**Message Type**: AI
**Example Message**: "Excellent! Let me get this load assigned to you..."

**Parameters**:
- `load_id` (required): Load to assign
- `final_rate` (required): Agreed rate
- `mc_number` (required): Carrier MC number
- `call_id` (optional): Call tracking

**Webhook URL**:
```
POST https://your-app.fly.dev/webhook/happyrobot/confirm-load
```

---

## 📊 Post-Call Processing

### AI Classification
After each call, add an **AI > Classify** node:

**Prompt**:
```
Classify this freight broker call with a carrier based on the outcome and conversation quality.

Consider these factors:
- Did the carrier get verified successfully?
- Were suitable loads found and presented?
- Did negotiations take place?
- Was a load successfully assigned?
- What was the overall tone and carrier satisfaction?

Classification should reflect the business outcome and carrier experience.
```

**Input**: Use `{{Transcript}}` from the AI Agent output

**Tags**:
- successful_booking
- negotiation_attempted  
- verification_failed
- no_suitable_loads
- carrier_disconnect
- transferred_to_human

### AI Extract
Add an **AI > Extract** node for data extraction:

**Prompt**:
```
Extract key business information from this freight broker call with a carrier.

Focus on extracting structured data that can be used for analytics, follow-up, and business intelligence.

Pay attention to:
- Carrier details and equipment capabilities
- Load preferences and requirements
- Rate negotiations and final agreements
- Call quality indicators and carrier satisfaction
- Operational details for dispatch coordination
```

**Input**: Use `{{Transcript}}` from the AI Agent output

**Parameters to Extract**:
- `mc_number`: Carrier's MC number
- `company_name`: Carrier company name
- `equipment_type`: Type of equipment discussed
- `final_rate`: Agreed rate (if applicable)
- `load_assigned`: Load ID that was assigned
- `carrier_sentiment`: Overall carrier attitude (positive/negative/neutral)
- `negotiation_rounds`: Number of negotiation attempts
- `call_outcome`: Final result of the call

### Webhook Integration
Add a **Webhook > POST** node to send call data to your system:

**URL**: 
```
https://your-app.fly.dev/webhook/happyrobot/extract-call-data
```

**Body**:
```json
{
  "call_id": "{{call_id}}",
  "transcript": "{{Transcript}}",
  "duration": "{{Duration}}",
  "outcome": "{{Classification}}",
  "extracted_data": "{{Extracted_Data}}"
}
```

**Headers**:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer freight-broker-api-key-2025"
}
```

---

## 🧪 Testing Configuration

### Test Scenarios
1. **Happy Path**: Verified carrier finds suitable load, accepts rate
2. **Negotiation**: Carrier counters rate, AI negotiates successfully  
3. **No Match**: Verified carrier but no suitable loads available
4. **Verification Failure**: Invalid or inactive MC number
5. **Complex Negotiation**: Multiple rounds requiring human transfer

### Test Scripts
Use these conversation flows for testing:

#### Test 1: Successful Booking
```
Caller: "Hi, I'm looking for loads out of Dallas"
Expected: Greeting + MC number request
Caller: "My MC number is 123456"  
Expected: Verification + equipment type request
Caller: "I have a dry van"
Expected: Load search + presentation
Caller: "That Dallas to Atlanta load sounds good at $2100"
Expected: Load confirmation + next steps
```

#### Test 2: Rate Negotiation
```
Caller: "I can do the Dallas-Atlanta run for $1900"
Expected: Counter-offer negotiation
Caller: "How about $2000?"
Expected: AI evaluation + response
Caller: "OK, I'll take $2050"
Expected: Acceptance + load assignment
```

---

## 📈 Analytics & Monitoring

### Dashboard Access
Monitor call performance at:
```
https://your-app.fly.dev/dashboard
```

### Key Metrics Tracked
- **Call Volume**: Total inbound calls processed
- **Success Rate**: Percentage of calls resulting in bookings
- **Verification Rate**: Carrier verification success rate
- **Negotiation Analysis**: Average rounds and success rates
- **Sentiment Tracking**: Carrier satisfaction scores
- **Revenue Metrics**: Total bookings and revenue generated

### API Endpoints for Analytics
```bash
GET /dashboard/api/metrics - Overall performance metrics
GET /dashboard/api/call-details - Detailed call logs
GET /webhook/happyrobot/call-analytics - Individual call data
```

---

## 🔒 Security & Authentication

### API Key Authentication
All webhook endpoints require Bearer token authentication:
```
Authorization: Bearer freight-broker-api-key-2025
```

### HTTPS/SSL
All communications use HTTPS encryption automatically via Fly.io

### Rate Limiting
API endpoints are protected against abuse with built-in rate limiting

---

## 🚀 Deployment Instructions

1. **Deploy API**: Run `./deploy.sh` to deploy to Fly.io
2. **Configure HappyRobot**: Use webhook URLs in workflow setup
3. **Test Integration**: Use web call feature to test workflows
4. **Monitor Performance**: Check dashboard for real-time analytics

### Live Deployment URLs
- **API Base**: `https://freight-broker-happyrobot.fly.dev`
- **Dashboard**: `https://freight-broker-happyrobot.fly.dev/dashboard`
- **API Docs**: `https://freight-broker-happyrobot.fly.dev/docs`

---

## 📞 Support & Troubleshooting

### Common Issues
1. **Webhook Timeouts**: Ensure API is running and accessible
2. **Authentication Errors**: Verify API key in headers
3. **Tool Parameter Issues**: Check required vs optional parameters
4. **Voice Recognition**: Add more keyterms for better accuracy

### Debugging
- Check API logs in Fly.io dashboard
- Monitor webhook response codes
- Review call transcripts for accuracy
- Test individual endpoints with curl/Postman

### Contact
For technical support or custom configurations, contact the development team.
