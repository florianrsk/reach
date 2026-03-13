# Quick Start Guide for Phase 1 Testing

## Prerequisites

1. **Python 3.8+** - Already installed ✓
2. **MongoDB** - Need to install/start
3. **Node.js 18+ & Yarn** - For frontend

## Step 1: Setup Environment

**Copy environment template:**
```bash
cd backend
copy .env.template .env
```

**Edit `.env` file with these minimal settings:**
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=reach_db
JWT_SECRET_KEY=test-jwt-secret-key-for-development-only
CSRF_SECRET_KEY=test-csrf-secret-key-for-development-only
CORS_ORIGINS=http://localhost:3000
```

## Step 2: Install Dependencies

**Backend:**
```bash
cd backend
pip install fastapi uvicorn motor pydantic python-dotenv bcrypt pyjwt slowapi psutil python-json-logger
```

**Frontend:**
```bash
cd frontend
yarn install
```

## Step 3: Start MongoDB

**Option A: Docker (Recommended)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Option B: Install MongoDB locally**
- Download from https://www.mongodb.com/try/download/community
- Start MongoDB service

## Step 4: Start Services

**Terminal 1 - Backend:**
```bash
cd backend
python server.py
```
Expected output: `Server running on http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```
Expected output: `Compiled successfully! App running on http://localhost:3000`

## Step 5: Test Phase 1 Implementation

**Run validation tests:**
```bash
cd ..
python test_phase1_local.py
```

**Or test manually with curl:**

1. **Check health:**
```bash
curl http://localhost:8000/health
```

2. **Get CSRF token:**
```bash
curl http://localhost:8000/api/auth/csrf
```

3. **Register user (replace TOKEN):**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: YOUR_TOKEN_HERE" \
  -d '{"email": "test@example.com", "password": "SecurePass123!@#", "name": "Test User"}'
```

4. **Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: YOUR_TOKEN_HERE" \
  -d '{"email": "test@example.com", "password": "SecurePass123!@#"}'
```

## Step 6: Verify Security Features

✅ **Check httpOnly cookies** in response headers
✅ **Test rate limiting** by making 11 rapid login attempts
✅ **Verify password policy** with weak passwords
✅ **Check security headers** with `curl -I http://localhost:8000/`

## Troubleshooting

**"Module not found" errors:**
```bash
pip install <missing-module>
```

**MongoDB connection failed:**
```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print(client.server_info())"
```

**CORS errors in frontend:**
- Ensure `CORS_ORIGINS` includes `http://localhost:3000`
- Restart backend after changing .env

**Frontend build errors:**
```bash
cd frontend
rm -rf node_modules
yarn install
```

## Next Steps After Successful Test

1. Review `phase1_test_results.json` for detailed results
2. Check backend logs for structured logging
3. Test backup script: `python backup_mongodb.py --test`
4. Proceed to Phase 2: Performance & Scalability