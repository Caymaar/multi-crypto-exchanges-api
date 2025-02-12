from Utilities.Authentification import LoginRequest, RegisterRequest, TokenResponse, create_token, verify_token, verify_ws_token, invalidate_token
from Utilities.DataBaseManager import dbm
from Utilities.SubscriptionManager import AggregatedSubscriptionManager
from Utilities.SymbolFormatter import AdvancedSymbolFormatter
from Utilities.TWAPOrder import simulate_twap_order, TWAPOrderRequest
from Exchanges import exchange_dict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime
import pandas as pd
import asyncio




app = FastAPI(title="Exchange API", description="dev version")

symbols_dict = {
    exchange: exchange_obj.get_available_trading_pairs()
    for exchange, exchange_obj in exchange_dict.items()
}

formatter = AdvancedSymbolFormatter(symbols_dict)
subscription_manager = AggregatedSubscriptionManager()

@app.get("/health")
async def health_check():
    """Endpoint to check the health of the API"""
    return {"status": "healthy"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

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

    # Conversion du symbole standard en symbole propre à l'exchange.
    # Par exemple, "BTC-USD" devient "BTCUSDT" pour Binance, "BTC-USDT" pour OKX et "BTC/USD" pour Kraken.
    formatted_symbol = formatter.to_exchange(symbol, exchange)
    print(f"Input symbol: {symbol} converted to exchange-specific format: {formatted_symbol}")

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
    
    print(f"Getting klines for {exchange} - {formatted_symbol} - {interval} - {start_date} - {end_date}")
    klines = await exchange_obj.get_historical_klines(formatted_symbol, interval, start_time, end_time)
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

############################################################################################################
# Websocket
############################################################################################################

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    Endpoint WebSocket auquel les clients se connectent après authentification.
    Le token est passé en query string, par exemple : 
       ws://localhost:8000/ws?token=VOTRE_TOKEN
    Les clients envoient des messages JSON de la forme :
      {"action": "subscribe", "exchange": "kraken", "symbol": "BTC-USD"}
      {"action": "unsubscribe", "exchange": "kraken", "symbol": "BTC-USD"}
    Le serveur diffuse ensuite, toutes les secondes, les données agrégées des carnets d'ordres.
    """
    try:
        # On attend que la fonction vérifie le token et retourne le username.
        username = await verify_ws_token(token)
        print(f"User {username} connected to WebSocket")
    except Exception as e:
        print(f"Invalid token: {e}")
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Si le token est valide, on accepte la connexion
    await websocket.accept()

    # Le reste de votre logique d’abonnement, par exemple en utilisant votre AggregatedSubscriptionManager
    client_subscriptions = set()
    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            exchange = message.get("exchange")
            symbol = message.get("symbol")
            # Ici, vous pouvez (optionnellement) standardiser le symbole avec votre AdvancedSymbolFormatter
            # et ensuite gérer l'abonnement via votre gestionnaire
            if action == "subscribe":
                client_subscriptions.add((exchange, symbol))
                await subscription_manager.subscribe(websocket, exchange, symbol, formatter)
                await websocket.send_json({"message": f"Subscribed to {exchange} {symbol}"})
            elif action == "unsubscribe":
                key = (exchange, symbol)
                if key in client_subscriptions:
                    client_subscriptions.remove(key)
                    await subscription_manager.unsubscribe(websocket, exchange, symbol, formatter)
                    await websocket.send_json({"message": f"Unsubscribed from {exchange} {symbol}"})
                else:
                    await websocket.send_json({"error": "Not subscribed to this symbol"})
            else:
                await websocket.send_json({"error": "Unknown action"})
    except WebSocketDisconnect:
        for (exchange, symbol) in client_subscriptions:
            await subscription_manager.unsubscribe(websocket, exchange, symbol, formatter)

############################################################################################################
# TWAP Orders
############################################################################################################

# --- Endpoint REST: POST /orders/twap ---
@app.post("/orders/twap", status_code=202)
async def submit_twap_order(order_req: TWAPOrderRequest, username: str = Depends(verify_token)):
    try:
        dbm.create_order_token(order_req, username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {e}")
    
    # Lancer la simulation TWAP en tâche de fond
    asyncio.create_task(simulate_twap_order(
        order_id=order_req.order_id,
        username=username,
        symbol=order_req.symbol,
        side=order_req.side,
        total_quantity=order_req.total_quantity,
        limit_price=order_req.limit_price,
        duration=order_req.duration,
        interval=order_req.interval
    ))
    return {"message": "TWAP order accepted", "order_id": order_req.order_id}

# --- Endpoint REST: GET /orders ---
@app.get("/orders")
async def list_orders(order_id: str = None, order_status: str = None, username: str = Depends(verify_token)):
    return dbm.get_orders(username, order_id, order_status)

# --- Endpoint REST: GET /orders/{order_id} ---
@app.get("/orders/{order_id}")
async def get_order_detail(order_id: str, username: str = Depends(verify_token)):
    return dbm.get_order_details(username, order_id)


@app.on_event("shutdown")
async def shutdown_event():
    """Event handler for server shutdown"""
    open_orders = dbm.get_orders(order_status="open")
    for order in open_orders:
        dbm.update_order_status(order["order_id"], "cancel")
    print("All open orders have been cancelled")
    
############################################################################################################
# Main
############################################################################################################

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

