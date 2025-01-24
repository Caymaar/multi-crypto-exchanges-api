from asyncio import tasks

from fastapi import FastAPI, Query, BackgroundTasks
import asyncio
from Exchange import Binance, CoinbasePro, OKX
from datetime import datetime, timedelta
from pydantic import BaseModel
from TWAPOrder import TWAPOrder
import uuid
from WebSocketManager import WebSocketManager
from typing import List, Optional

orders: List[TWAPOrder] = [] # List to store the active or closed TWAP orders

class Requester:

    def __init__(self):
        self.exchange = {
            "binance": Binance(),
            "okx": OKX(),
            "coinbasepro": CoinbasePro(),
        }

    def get_available_trading_pairs(self, exchange):
        return self.exchange[exchange].get_available_trading_pairs()
        
    async def get_historical_klines(self, exchange, symbol, interval, start_time, end_time):
        return await self.exchange[exchange].get_historical_klines(symbol, interval, start_time, end_time)

# Pydantic model for the request body
class TWAPOrderRequest(BaseModel):
    token_id: str
    exchange: str
    symbol: str
    quantity: float
    duration: int
    price: float
    start_time: str  # "YYYY-MM-DDTHH:MM:SS"
    end_time: str  # "YYYY-MM-DDTHH:MM:SS"
    interval: int  # Interval for the TWAP order (e.g., "5m", "1h")

class OrderResponse(BaseModel):
    token_id: str
    symbol: str
    side: str
    quantity: float
    limit_price: float
    status: str
    creation_time: str  # Timestamp as ISO string



# Initialize FastAPI app
app = FastAPI()
requester = Requester()

# Route for the root endpoint "/"
@app.get("/")
def read_root():
    return {"message": "Welcome to the Simple Multi Exchange API"}

# Route that returns all available stock symbols
@app.get("/{exchange}/symbols")
def get_symbols(exchange):
    
    pairs = requester.get_available_trading_pairs(exchange)
    return {"symbols": pairs}


@app.post("/orders/twap", response_model=List[OrderResponse])
async def submit_twap_order(requests: List[TWAPOrderRequest], background_tasks: BackgroundTasks):
    """
    Submit a TWAP (Time-Weighted Average Price) order.

    Args:
        request: TWAPOrderRequest, including token_id, exchange, symbol, quantity, price, start_time, and end_time.

    Returns:
        OrderResponse: status and message indicating the order was accepted or rejected.
    """
    try:
        order_responses = []
        tasks = []

        for request in requests:
            token_id = request.token_id if request.token_id else str(uuid.uuid4())
            exchange = request.exchange
            symbol = request.symbol
            quantity = request.quantity
            price = request.price
            start_time = request.start_time
            end_time = request.end_time
            interval = request.interval

            # Validate exchange name
            if exchange not in ["binance", "okx", "coinbasepro"]:
                raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange}")

            # Validate time format
            try:
                start_timestamp = int(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000)
                end_timestamp = int(datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DDTHH:MM:SS'.")

            # Validate symbol format
            if not re.match(r'^[A-Z0-9-_.]{1,20}$', symbol):
                raise HTTPException(status_code=400, detail="Invalid symbol format.")

            # Create TWAP Order
            exchange_instance = requester.exchange[exchange]
            ws_manager = WebSocketManager()

            twap_order = TWAPOrder(
                token_id=token_id,
                exchange=exchange_instance,
                symbol=symbol,
                side="buy" if price > 0 else "sell",  # Determine the side based on the price
                quantity=quantity,
                duration=request.duration,
                slice_interval=interval,
                limit_price=price,
                ws_manager=ws_manager
            )

            orders.append(twap_order)

            # Add task to background for execution
            # background_tasks.add_task(twap_order.execute_twap)
            # tasks.append(asyncio.create_task(twap_order.execute_twap()))

            # Add the response data to the list
            order_responses.append(OrderResponse(
                token_id=token_id,
                symbol=symbol,
                side=twap_order.side,
                quantity=quantity,
                limit_price=price,
                status="Accepted",
                creation_time=datetime.utcnow().isoformat()
            ))

            # await asyncio.gather(*tasks)
        # Serialize responses before returning
        return order_responses  # Convert the Pydantic models to dictionaries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting orders: {str(e)}")

@app.get("/orders", response_model=List[OrderResponse])
def list_orders(token_id: Optional[str] = None, status: Optional[str] = None):
    """
    Get all orders (can be filtered by token_id or status)
    """
    filtered_orders = orders

    if token_id:
        filtered_orders = [order for order in filtered_orders if order.token_id == token_id]

    if status:
        filtered_orders = [order for order in filtered_orders if order.status == status]

    if not filtered_orders:
        raise HTTPException(status_code=404, detail="No orders found.")

    return [OrderResponse(
        token_id=order.token_id,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        limit_price=order.limit_price,
        status=order.status,
        creation_time=order.creation_time.isoformat()
    ) for order in filtered_orders]


@app.get("/orders/{token_id}", response_model=OrderResponse)
def get_order_by_token_id(token_id: str):
    """
    Get a specific order by token_id.
    """
    order = next((order for order in orders if order.token_id == token_id), None)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    return OrderResponse(
        token_id=order.token_id,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        limit_price=order.limit_price,
        status=order.status,
        creation_time=order.creation_time.isoformat()
    )


# ...existing code...

import re
from fastapi import HTTPException

@app.get("/{exchange}/{symbol}")
async def get_klines(
    exchange: str,
    symbol: str,
    start_date: str = Query(None, description="Start date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
    end_date: str = Query(None, description="End date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
    interval: str = Query("1d", description="Candle interval, e.g., 1m, 5m, 1h")
):
    """
    Récupère les chandelles pour une paire de trading sur un échange spécifique.

    :param exchange: Nom de l'échange (ex: binance, kraken).
    :param symbol: Symbole de trading (ex: BTCUSDT).
    :param start_date: Date de début au format YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS.
    :param end_date: Date de fin au format YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS.
    :param interval: Intervalle des chandelles (par défaut: 1m).
    :return: Chandelles récupérées pour la paire.
    """
    def parse_date(date_str):
        """
        Tente de parser une date dans différents formats.
        
        :param date_str: Chaîne de la date.
        :return: Timestamp Unix (ms).
        """
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
            except ValueError:
                pass
        raise ValueError(f"Invalid date format: {date_str}. Supported formats are YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

    # Valider le symbole
    if not re.match(r'^[A-Z0-9-_.]{1,20}$', symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format. Legal range is '^[A-Z0-9-_.]{1,20}$'.")

    try:
        # Convertir les dates en timestamp
        if start_date:
            start_timestamp = parse_date(start_date)
        else:
            start_date = datetime.now() - timedelta(days=5)
            start_timestamp = int(start_date.timestamp() * 1000)  # Valeur par défaut

        if end_date:
            end_timestamp = parse_date(end_date)
        else:
            end_date
            end_timestamp = int(datetime.now().timestamp() * 1000)  # Valeur par défaut

        # Appeler la fonction pour récupérer les chandelles
        klines = await requester.get_historical_klines(exchange, symbol, interval, start_timestamp, end_timestamp)
        return {"klines": klines}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    

@app.get("/test")
async def do_test():
    req = Requester()

    start_date = int(datetime(2024, 1, 1).timestamp() * 1000)
    end_date = int(datetime(2024, 1, 10).timestamp() * 1000)
    try:
        # Utilisez await pour appeler la méthode asynchrone
        klines = await req.get_historical_klines("binance", "BTCUSDT", "1m", start_date, end_date)
    except Exception as e:
        return {"error": str(e)}
    return {"symbol": "BTC", "klines": klines}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
