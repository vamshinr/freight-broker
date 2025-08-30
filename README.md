# Freight Broker AI

## 🎯 API Endpoints

### Core Freight Broker
- `GET /` - API status and health check
- `GET /loads` - List available loads with filtering
- `POST /loads/search` - Advanced load search with criteria
- `GET /carrier/verify/{mc_number}` - Real FMCSA verification

### HappyRobot Webhooks
- `POST /happyrobot/verify-carrier` - Carrier verification webhook
- `POST /happyrobot/search-loads` - Load matching webhook  
- `POST /happyrobot/negotiate-rate` - Negotiation webhook
- `POST /happyrobot/confirm-load` - Load confirmation webhook

### Analytics Dashboard
- `GET /dashboard` - Interactive analytics interface
- `GET /analytics/metrics` - KPI data API
- `GET /analytics/calls` - Call activity data

## 📊 Sample Data
Database includes realistic freight loads:
- **L123**: Dallas, TX → Atlanta, GA (Dry Van, $2,100, 925 miles)
- **L456**: Fort Worth, TX → Jacksonville, FL (Reefer, $2,600, 1,200 miles)
- **L789**: Dallas, TX → Charlotte, NC (Dry Van, $2,300, 1,050 miles)

## 🔧 Technology Stack
- **Backend**: FastAPI 2.0 with async support
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 templates + Chart.js + Bootstrap
- **AI Integration**: HappyRobot webhook architecture  
- **Deployment**: Docker + Fly.io cloud platform
- **APIs**: Real FMCSA integration with fallback system
