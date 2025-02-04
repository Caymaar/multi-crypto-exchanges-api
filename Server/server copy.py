from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
# Make sure to use PyJWT
# pip uninstall jwt pyjwt
# pip install pyjwt fastapi uvicorn requests
import jwt as PyJWT
import time

from jwt import ExpiredSignatureError, InvalidTokenError

# Simple configs
SECRET_KEY = "your-secret-key"  # In production use proper secret management
security = HTTPBearer()
app = FastAPI(title="Simple Secure API", description="Basic JWT authentication demo")
 
# Simple user database
users_db = {
    "alice": {"password": "wonderland", "role": "user"},
    "admin": {"password": "admin123", "role": "admin"}
}

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_token(username: str) -> str:
    """Create a simple JWT token"""
    expiration = datetime.utcnow() + timedelta(minutes=30)
    token = PyJWT.encode(
        {
            "username": username, 
            "exp": expiration
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    print(token)
    return token

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        print(token)
        payload = PyJWT.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload["exp"] < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload["username"]
    except PyJWT.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except PyJWT.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token"""
    if request.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid username")
    
    if users_db[request.username]["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_token(request.username)
    return {"access_token": token}

@app.get("/secure")
async def secure_endpoint(username: str = Depends(verify_token)):
    """Protected endpoint requiring valid JWT"""
    return {
        "message": f"Hello {username}! This is secure data",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)