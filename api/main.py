from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
import os
import redis
import asyncpg
from datetime import datetime
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NAC Policy Engine", version="1.1.0")

# Global DB Havuzu
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama Başlarken Çalışacak Kodlar (Startup)
    global db_pool
    db_url = os.getenv("DATABASE_URL", "postgresql://radius:6767523@postgres:5432/radius")
    try:
        db_pool = await asyncpg.create_pool(db_url)
        logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
    
    yield # Uygulama bu noktada çalışmaya başlar
    
    # Uygulama Kapanırken Çalışacak Kodlar (Shutdown)
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

# FastAPI tanımına lifespan'i ekliyoruz
app = FastAPI(title="NAC Policy Engine", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthRequest(BaseModel):
    username: str
    password: str
    nas_ip: Optional[str] = None

class AccountingRequest(BaseModel):
    username: str
    session_id: str
    status_type: str
    session_time: Optional[Union[int, str]] = 0
    input_octets: Optional[int] = 0
    output_octets: Optional[int] = 0
    nas_ip: Optional[str] = "127.0.0.1"

def get_redis_client():
    try:
        redis_url = os.getenv("REDIS_URL", "redis://:redis2323@redis:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        return client
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "NAC Policy Engine is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/accounting")
async def accounting(request: AccountingRequest):
    logger.info(f"Received RADIUS Accounting: {request.status_type} for {request.username}")
    
    if not db_pool:
        return {"result": "fail", "message": "DB Pool not ready"}
    
    redis_client = get_redis_client()
    
    try:
        async with db_pool.acquire() as conn:
            if request.status_type == "Start":
                # DİKKAT: acctuniqueid eklendi!
                await conn.execute("""
                    INSERT INTO radacct 
                    (acctsessionid, acctuniqueid, username, acctstarttime, acctstatustype, nasipaddress)
                    VALUES ($1, $2, $3, NOW(), $4, $5)
                    ON CONFLICT (acctuniqueid) DO UPDATE SET acctstarttime = NOW()
                """, request.session_id, f"ID-{request.session_id}", request.username, request.status_type, request.nas_ip)
                
                if redis_client:
                    redis_client.hset(f"session:{request.session_id}", mapping={
                        "username": request.username,
                        "start_time": datetime.now().isoformat(),
                        "nas_ip": request.nas_ip,
                        "status": "active"
                    })
                    redis_client.expire(f"session:{request.session_id}", 86400)
                
            elif request.status_type == "Stop":
                await conn.execute("""
                    UPDATE radacct 
                    SET acctstoptime = NOW(),
                        acctsessiontime = $1,
                        acctterminatecause = 'User-Request'
                    WHERE acctsessionid = $2
                """, request.session_time, request.session_id)
                
                if redis_client:
                    redis_client.delete(f"session:{request.session_id}")
            
            return {"result": "success", "message": "Recorded"}
            
    except Exception as e:
        logger.error(f"Accounting SQL error: {e}")
        return {"result": "fail", "message": str(e)}

@app.get("/sessions/active")
async def get_active_sessions():
    redis_client = get_redis_client()
    if not redis_client:
        return {"sessions": [], "error": "Redis not reachable"}
    
    try:
        keys = redis_client.keys("session:*")
        sessions = []
        for key in keys:
            data = redis_client.hgetall(key)
            data["session_id"] = key.replace("session:", "")
            sessions.append(data)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        return {"sessions": [], "error": str(e)}