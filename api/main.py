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

# Global DB Havuzu
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_url = os.getenv("DATABASE_URL", "postgresql://radius:6767523@postgres:5432/radius")
    try:
        db_pool = await asyncpg.create_pool(db_url)
        logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
    
    yield 
    
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

app = FastAPI(title="NAC Policy Engine", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC MODELLERİ ---
class AuthRequest(BaseModel):
    username: str
    password: Optional[str] = None 

class AuthorizeRequest(BaseModel):
    username: str
    nas_ip: Optional[str] = None

class AccountingRequest(BaseModel):
    username: str
    session_id: str
    status_type: str
    nas_ip: Optional[str] = "127.0.0.1"
    session_time: Optional[Union[int, str]] = 0

class EventRequest(BaseModel):
    username: str

# --- REDIS BAĞLANTISI ---
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

@app.post("/auth")
async def authenticate_user(request: AuthRequest):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not ready")
    
    # Hız limiti (Rate Limit) Kontrolü
    redis_client = get_redis_client()
    if redis_client:
        retry_count = redis_client.get(f"retry:{request.username}")
        if retry_count and int(retry_count) > 5:
            return {"reply:Reply-Message": "Too many failed attempts", "control:Auth-Type": "Reject"}

    async with db_pool.acquire() as conn:

        user = await conn.fetchrow("SELECT * FROM radcheck WHERE username = $1", request.username)
        
        if user:
            if redis_client:
                redis_client.delete(f"retry:{request.username}")
            return {
                "control:Auth-Type": "Accept",
                "reply:Reply-Message": "API Authentication Successful"
            }
        else:
            if redis_client:
                redis_client.incr(f"retry:{request.username}")
                redis_client.expire(f"retry:{request.username}", 600)
            raise HTTPException(status_code=401, detail="Authentication Failed")

@app.post("/authorize")
async def authorize_user(request: AuthorizeRequest):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not ready")

    async with db_pool.acquire() as conn:

        group = await conn.fetchrow("SELECT groupname FROM radusergroup WHERE username = $1", request.username)
        
        if group:
            grp_name = group["groupname"]

            replies = await conn.fetch("SELECT attribute, value FROM radgroupreply WHERE groupname = $1", grp_name)
            
            response_data = {}
            for row in replies:
                response_data[f"reply:{row['attribute']}"] = row['value']
                
            return response_data
        
    return {"reply:Reply-Message": "No specific policy found"}

@app.post("/accounting")
async def accounting(request: AccountingRequest):
    logger.info(f"Received RADIUS Accounting: {request.status_type} for {request.username}")
    
    redis_client = get_redis_client()
    if not redis_client:
        return {"result": "fail", "message": "Redis not reachable"}
    
    try:
        if request.status_type == "Start":
            redis_client.hset(f"session:{request.session_id}", mapping={
                "username": request.username,
                "start_time": datetime.now().isoformat(),
                "nas_ip": request.nas_ip,
                "status": "active"
            })
            redis_client.expire(f"session:{request.session_id}", 86400)
            
        elif request.status_type == "Stop":
            redis_client.delete(f"session:{request.session_id}")
            logger.info(f"Redis session deleted: {request.session_id}")
        
        return {"result": "success", "message": "Redis Updated"}
            
    except Exception as e:
        logger.error(f"Redis operation error: {e}")
        return {"result": "fail", "message": str(e)}

@app.get("/users")
async def get_users():
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not ready")
        
    redis_client = get_redis_client()
    
    active_users = set()
    if redis_client:
        keys = redis_client.keys("session:*")
        for key in keys:
            data = redis_client.hgetall(key)
            if "username" in data:
                active_users.add(data["username"])

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT DISTINCT username FROM radcheck")
        
        users_list = []
        for row in rows:
            uname = row["username"]
            users_list.append({
                "username": uname,
                "status": "Online" if uname in active_users else "Offline"
            })
            
        return {"total_users": len(users_list), "users": users_list}

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