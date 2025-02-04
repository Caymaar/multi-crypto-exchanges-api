from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from Authentification import LoginRequest, RegisterRequest, TokenResponse, create_token, verify_token, invalidate_token
from DataBaseManager import dbm
from datetime import datetime
from Exchanges import exchange_dict
from fastapi import Query
import pandas as pd

app = FastAPI(title="Exchange API", description="dev version")


@app.get("/exchanges")
async def get_exchanges():
    """Endpoint to get list of available exchanges"""
    return {"exchanges": list(exchange_dict.keys())}

############################################################################################################
# Request symbols
############################################################################################################

@app.get("/{exchange}/symbols")
def get_symbols(exchange: str):
    """Endpoint to get list of available trading pairs for a given exchange"""
    if exchange not in exchange_dict:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    return {"symbols": exchange_dict[exchange].get_available_trading_pairs()}

############################################################################################################
# Request historical data
############################################################################################################

def parse_date(date_str: str) -> int:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {date_str}. Supported formats are YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

@app.get("/klines/{exchange}/{symbol}")
async def get_klines(
        exchange: str,
        symbol: str,
        start_date: str = Query(None, description="Start date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
        end_date: str = Query(None, description="End date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
        interval: str = Query("1d", description="Candle interval, e.g., 1m, 5m, 1h")
):
    
    if exchange not in exchange_dict:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    exchange_obj = exchange_dict[exchange]
    
    if start_date is not None:
        start_time = parse_date(start_date)
    else:
        start_time = int((pd.to_datetime("today") - pd.DateOffset(days=5)).timestamp() * 1000)
    
    if end_date is not None:
        end_time = parse_date(end_date)
    else:
        end_time = int(pd.to_datetime("today").timestamp() * 1000)
    
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    if interval not in exchange_obj.valid_intervals:
        raise HTTPException(status_code=400, detail=f"Invalid interval '{interval}'. Valid intervals are: {', '.join(exchange_obj.valid_intervals.keys())}")
    
    print(f"Getting klines for {exchange} - {symbol} - {interval} - {start_date} - {end_date}")
    klines = await exchange_obj.get_historical_klines(symbol, interval, start_time, end_time)
    return klines

############################################################################################################
# Authentification
############################################################################################################

@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token"""
    user = dbm.get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")
    
    if request.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_token(request.username)
    return {"access_token": token}

@app.post("/logoff")
async def logoff(credentials: HTTPAuthorizationCredentials = Depends(invalidate_token)):
    """Logout endpoint - Invalidates the JWT token"""
    return {"message": "User logged off successfully"}

@app.post("/register", status_code=201)
async def register_user(request: RegisterRequest):
    """Endpoint to register a new user with 'user' role
    # Example query:
    {
        "username": "newuser",
        "password": "newpassword"
    }
    """
    if dbm.get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    dbm.create_user(request.username, request.password, "user")
    return {"message": "User registered successfully"}

@app.delete("/unregister")
async def unregister_user(username: str = Depends(verify_token)):
    """Endpoint to unregister a user - requires valid JWT"""

    user = dbm.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin user can't be unregistered")

    dbm.delete_user(username)
    return {"message": "User unregistered successfully"}

@app.get("/info")
async def secure_endpoint(username: str = Depends(verify_token)):
    """Protected endpoint requiring valid JWT"""
    return {
        "message": f"Hello {username}! This is info data",
        "timestamp": datetime.now().isoformat()
    }

############################################################################################################
# Admin section
############################################################################################################

@app.get("/users")
async def get_users(username: str = Depends(verify_token)):
    """Endpoint to get list of users - requires admin role"""
    user = dbm.get_user_by_username(username)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="You can't access this section with your actual role")
    
    users = dbm.get_all_users()
    return users

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

