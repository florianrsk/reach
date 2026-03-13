# Reach - AI-Powered Reachability Platform

## Overview
Reach is a reachability-as-logic platform that replaces email addresses, contact forms, and DMs with logic-based access. Users don't receive messages by default - all incoming attempts are evaluated by AI and rules.

## Features
- **Face-based identities**: Users create public "Faces" with custom rules
- **AI-powered filtering**: Every incoming message is evaluated by AI
- **Rule-based access**: Custom rules determine who can reach you
- **Payment integration**: Senders may pay to cross boundaries
- **Public sender pages**: Anyone can reach identity owners via public pages

## Tech Stack
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Vite
- **Database**: MongoDB Atlas with optimized indexes
- **Caching**: Redis for high-traffic public pages
- **AI**: OpenAI integration for message evaluation
- **Payments**: Stripe integration

## Project Structure
```
reach/
├── backend/           # FastAPI backend server
│   ├── server.py              # Main application
│   ├── redis_cache.py         # Redis caching module
│   ├── create_indexes.py      # MongoDB index creation
│   ├── requirements.txt       # Python dependencies
│   └── .env                  # Environment variables
├── frontend/          # React frontend with Vite
│   ├── vite.config.js        # Vite configuration
│   ├── package.json          # Frontend dependencies
│   ├── index.html           # HTML template
│   └── src/                 # React components
└── memory/            # Project documentation
    └── PRD.md              # Product requirements
```

## Setup Instructions

### Backend Setup
1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB, Redis, and API keys
   ```

3. Create MongoDB indexes:
   ```bash
   python create_indexes.py
   ```

4. Start the backend server:
   ```bash
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Performance Optimizations
- **Vite migration**: Replaced CRA with Vite for faster builds
- **MongoDB indexes**: Optimized queries with strategic indexes
- **Redis caching**: Cached public pages with 5-minute TTL
- **Graceful fallback**: System works even when Redis is unavailable

## API Endpoints
- `GET /api/reach/{handle}` - Public sender page (cached)
- `POST /api/reach/{handle}/message` - Submit reach attempt
- `GET /api/cache/health` - Redis cache health check
- `GET /api/health` - System health check

## License
Proprietary
