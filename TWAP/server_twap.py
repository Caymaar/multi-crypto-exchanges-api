from fastapi import FastAPI, Query, BackgroundTasks, Header, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import re
import secrets
import asyncio
from typing import List, Optional
from Exchange import Binance, CoinbasePro, OKX
from TWAPOrder import TWAPOrder
from WebSocketManager import WebSocketManager
from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI app
app = FastAPI()

# List to store active or closed TWAP orders
orders: List[TWAPOrder] = []
# Global set to store all unique token_ids across requests
used_token_ids = set()

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Authenticates the user based on the API key passed in the request header
async def authenticate_user(request: Request, authorization: str = Header(None), db: Session = Depends(get_db)):
    """
    Authenticates the user using an API key.

    Args:
        request: FastAPI Request object.
        authorization: The Authorization header with the API key.
        db: Database session.

    Raises:
        HTTPException: If authentication fails.
    """
    if not authorization:
        raise HTTPException(status_code=400, detail="Authorization header is missing.")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format.")

    api_key = authorization.split("Bearer ")[-1]
    user = db.query(User).filter(User.api_key == api_key).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key.")

    return user


# Requester class to handle interactions with multiple exchanges
class Requester:
    def __init__(self):
        self.exchange = {
            "binance": Binance(),
            "okx": OKX(),
            "coinbasepro": CoinbasePro(),
        }

    def get_available_trading_pairs(self, exchange: str):
        return self.exchange[exchange].get_available_trading_pairs()

    async def get_historical_klines(self, exchange: str, symbol: str, interval: str, start_time: int, end_time: int):
        return await self.exchange[exchange].get_historical_klines(symbol, interval, start_time, end_time)


# Pydantic model for the TWAP order request body
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


# Pydantic model for order response
class OrderResponse(BaseModel):
    token_id: str
    symbol: str
    side: str
    quantity: float
    limit_price: float
    status: str
    creation_time: str  # Timestamp as ISO string


requester = Requester()


@app.get("/")
def read_root():
    """
    Root endpoint that provides information about the API.

    Returns:
        dict: Welcome message and API description.
    """
    return {
        "message": "Welcome to the Simple Multi Exchange API. This API allows you to place TWAP orders across multiple exchanges."
    }


@app.get("/{exchange}/symbols")
def get_symbols(exchange: str):
    """
    Endpoint to get available trading pairs for an exchange.

    Args:
        exchange (str): Name of the exchange (binance, okx, coinbasepro).

    Returns:
        dict: Available trading pairs for the specified exchange.
    """
    pairs = requester.get_available_trading_pairs(exchange)
    return {"symbols": pairs}


@app.post("/orders/twap", response_model=List[OrderResponse])
async def submit_twap_order(requests: List[TWAPOrderRequest], background_tasks: BackgroundTasks,
                            api_key: str = Depends(authenticate_user)):
    """
    Submit a TWAP (Time-Weighted Average Price) order.

    Args:
        requests (List[TWAPOrderRequest]): List of TWAP order requests.
        background_tasks (BackgroundTasks): For running tasks in the background.
        api_key (str): The API key used for user authentication.

    Returns:
        List[OrderResponse]: The response with order status and details.
    """
    try:
        order_responses = []
        token_ids = []

        for request in requests:
            token_id = request.token_id if request.token_id else str(uuid.uuid4())

            # Validate unique token_id
            if token_id in token_ids:
                raise HTTPException(status_code=400, detail=f"Duplicate token_id: {token_id}. Use a unique token_id.")

            token_ids.append(token_id)
            used_token_ids.add(token_id)
            # Validate time format
            try:
                start_timestamp = int(datetime.strptime(request.start_time, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000)
                end_timestamp = int(datetime.strptime(request.end_time, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DDTHH:MM:SS'.")

            # Validate symbol format
            if not re.match(r'^[A-Z0-9-_.]{1,20}$', request.symbol):
                raise HTTPException(status_code=400, detail="Invalid symbol format.")

            # Create TWAP order
            exchange_instance = requester.exchange[request.exchange]
            ws_manager = WebSocketManager()

            twap_order = TWAPOrder(
                token_id=token_id,
                exchange=exchange_instance,
                symbol=request.symbol,
                side="buy" if request.price > 0 else "sell",  # Determine the side based on the price
                quantity=request.quantity,
                duration=request.duration,
                slice_interval=request.interval,
                limit_price=request.price,
                ws_manager=ws_manager
            )
            await twap_order.execute_twap()
            twap_order.report()
            orders.append(twap_order)

            # Add order response
            order_responses.append(OrderResponse(
                token_id=token_id,
                symbol=request.symbol,
                side=twap_order.side,
                quantity=request.quantity,
                limit_price=request.price,
                status="Accepted",
                creation_time=datetime.utcnow().isoformat()
            ))

        return order_responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting orders: {str(e)}")


@app.get("/orders", response_model=List[OrderResponse])
def list_orders(token_id: Optional[str] = None, status: Optional[str] = None,
                api_key: str = Depends(authenticate_user)):
    """
    Get all orders (can be filtered by token_id or status).

    Args:
        token_id (Optional[str]): Filter orders by token_id.
        status (Optional[str]): Filter orders by status.

    Returns:
        List[OrderResponse]: List of orders matching the criteria.
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
def get_order_by_token_id(token_id: str, api_key: str = Depends(authenticate_user)):
    """
    Get a specific order by token_id.

    Args:
        token_id (str): The token_id of the order to retrieve.

    Returns:
        OrderResponse: The order with the specified token_id.
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


@app.get("/klines/{exchange}/{symbol}")
async def get_klines(
        exchange: str,
        symbol: str,
        start_date: str = Query(None, description="Start date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
        end_date: str = Query(None, description="End date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
        interval: str = Query("1d", description="Candle interval, e.g., 1m, 5m, 1h"),
        limit: int = Query(100, le=1000, description="Limit the number of candlesticks returned (max 1000)")
):
    """
    Get historical candlestick data for a trading pair.

    Args:
        exchange (str): The exchange to fetch data from.
        symbol (str): The trading symbol (e.g., BTCUSDT).
        start_date (str, optional): The start date for the data.
        end_date (str, optional): The end date for the data.
        interval (str): The candlestick interval.
        limit (int): The number of candlesticks to return (max 1000).

    Returns:
        dict: The historical candlesticks.
    """

    def parse_date(date_str):
        """
        Parse a date string into a timestamp.

        Args:
            date_str (str): The date string to parse.

        Returns:
            int: The Unix timestamp in milliseconds.
        """
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
            except ValueError:
                pass
        raise ValueError(f"Invalid date format: {date_str}. Supported formats are YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

    if not re.match(r'^[A-Z0-9-_.]{1,20}$', symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format.")

    try:
        start_timestamp = parse_date(start_date) if start_date else int(
            (datetime.now() - timedelta(days=5)).timestamp() * 1000)
        end_timestamp = parse_date(end_date) if end_date else int(datetime.now().timestamp() * 1000)

        klines = await requester.get_historical_klines(exchange, symbol, interval, start_timestamp, end_timestamp)
        klines = klines[:limit]  # Apply the limit

        return {"klines": klines}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database setup for User model
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    api_key = Column(String, unique=True, nullable=False)


# Configuration for SQLite database
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@app.post("/generate_api_key")
def generate_api_key(username: str = Query(...)):
    """
    Generates a unique API key for a user.

    Args:
        username (str): The username for which the API key is generated.

    Returns:
        dict: The generated API key for the user.
    """
    db = SessionLocal()
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists. Use the existing API key.")

    api_key = secrets.token_hex(32)
    new_user = User(username=username, api_key=api_key)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {"username": username, "api_key": api_key}


@app.get("/test")
async def do_test():
    """
    Test endpoint to fetch historical data for a test symbol.

    Returns:
        dict: The fetched candlesticks for a test symbol.
    """
    req = Requester()

    start_date = int(datetime(2024, 1, 1).timestamp() * 1000)
    end_date = int(datetime(2024, 1, 10).timestamp() * 1000)

    try:
        klines = await req.get_historical_klines("binance", "BTCUSDT", "1m", start_date, end_date)
    except Exception as e:
        return {"error": str(e)}

    return {"symbol": "BTC", "klines": klines}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server_twap:app", host="0.0.0.0", port=8001)
