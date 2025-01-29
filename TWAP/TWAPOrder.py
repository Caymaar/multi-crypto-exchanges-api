from datetime import datetime
import asyncio
from typing import Optional, Union, List, Dict
import uuid


class TWAPOrder:
    orders = []

    def __init__(self, token_id: str, exchange: object, symbol: str, side: str, quantity: Union[int, float], duration: int, slice_interval: int = 10, limit_price: Optional[Union[int, float]] = None, ws_manager: Optional[object] = None, status: str = "open"):
        self.token_id = token_id
        self.exchange: object = exchange
        self.symbol: str = symbol.upper()
        self.side: str = side.lower()
        self.quantity: Union[int, float] = quantity
        self.duration: int = duration
        self.slice_interval: int = slice_interval
        self.limit_price: Optional[Union[int, float]] = limit_price
        self.remaining_quantity: Union[int, float] = quantity
        self.executed_quantity: Union[int, float] = 0
        self.execution_logs: List[Dict[str, Union[str, float]]] = []
        self.ws_manager: Optional[object] = ws_manager
        self.order_book_data: Dict[str, List[Dict[str, Union[str, float]]]] = {"bids": [], "asks": []}
        self.status = status
        self.creation_time = datetime.now()

        self.execute_twap()

    def to_dict(self):
        """
        Convert TWAPOrder instance to a dictionary for serialization.
        """
        return {
            "token_id": self.token_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "duration": self.duration,
            "slice_interval": self.slice_interval,
            "limit_price": self.limit_price,
            "status": self.status,
            "creation_time": self.creation_time.isoformat(),
        }

    async def connect_websocket(self) -> None:
        """
        Connect to the WebSocket using WebSocketManager and fetch real-time order book data.
        """
        self.symbol = self.format_symbol_for_exchange(self.exchange.name, self.symbol)
        print(f"Connecting WebSocket for {self.exchange.name} with {self.symbol}...")

        # Get order book data using WebSocketManager
        self.order_book_data = await self.ws_manager.get_order_book_data(self.exchange.name, self.symbol)
        print(f"WebSocket connected for {self.symbol} on {self.exchange.name}")

    def close_order(self):
        self.status = "filled"  # Update status when the order is closed

    def get_order_details(self):
        return {
            "token_id": self.token_id,
            "exchange": self.exchange.name,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "duration": self.duration,
            "slice_interval": self.slice_interval,
            "limit_price": self.limit_price,
            "status": self.status,
            "creation_time": self.creation_time.isoformat(),
        }


    async def execute_twap(self) -> None:
        """
        Execute the TWAP order using real-time order book data.

        The order is divided into slices based on the specified duration and slice interval.
        """

        slices: int = self.duration // self.slice_interval  # Number of slices
        if slices == 0:
            raise ValueError("Duration should be greater than slice interval.")
        slice_quantity: Union[int, float] = self.quantity / slices

        for i in range(slices):
            if self.remaining_quantity <= 0:
                break

            await self.connect_websocket()

            print(f"Executing slice {i + 1}/{slices} on {self.exchange.name}...")
            try:
                # Retrieve the best price from the order book
                best_price: Optional[float] = None
                if self.side == "buy":
                    best_price = float(self.order_book_data["asks"][0]["price"])  # Best ask price
                elif self.side == "sell":
                    best_price = float(self.order_book_data["bids"][0]["price"])  # Best bid price

                # Check limit price conditions
                if self.limit_price is None or (
                    (self.side == "buy" and best_price <= self.limit_price) or
                    (self.side == "sell" and best_price >= self.limit_price)
                ):
                    executed_now: Union[int, float] = min(slice_quantity, self.remaining_quantity)
                    self.remaining_quantity -= executed_now
                    self.executed_quantity += executed_now
                    self.execution_logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "price": best_price,
                        "quantity": executed_now
                    })
                    print(f"Executed {executed_now:.4f} at a price of {best_price}")
                else:
                    print(
                        f"Slice {i + 1} skipped: limit price not met. "
                        f"Desired price: {self.limit_price}, Current price: {best_price}"
                    )

            except Exception as e:
                print(f"Error during slice execution: {e}")

            await asyncio.sleep(self.slice_interval)  # Wait before the next slice

        print(f"TWAP order execution completed on {self.exchange.name}")
        if self.remaining_quantity < 1e-6:
            self.remaining_quantity = 0

        self.close_order()
        self.report()

    def format_symbol_for_exchange(self, exchange_name: str, symbol: str) -> str:
        """
        Adjust the trading symbol format for the specified exchange.

        Args:
            exchange_name (str): Name of the exchange (e.g., "Binance").
            symbol (str): Trading symbol to format.

        Returns:
            str: Formatted trading symbol.
        """
        if exchange_name.lower() == "binance":
            return symbol.replace("-", "").replace("/", "")
        elif exchange_name.lower() == "okx":
            if "-" not in symbol:
                return f"{symbol[:-4]}-{symbol[-4:]}"
            return symbol
        elif exchange_name.lower() == "coinbase_pro":
            if "-" not in symbol:
                symbol = f"{symbol[:-4]}-{symbol[-4:]}"
            return symbol.replace("USDT", "USD")
        else:
            raise ValueError(f"Exchange {exchange_name} not supported.")

    def report(self) -> None:
        """
        Generate a summary report of the TWAP execution.
        """
        print("\nExecution Report:")
        print(f"Exchange: {self.exchange.name}")
        print(f"Symbol: {self.symbol}")
        print(f"Side: {self.side}")
        print(f"Total Quantity: {self.quantity}")
        print(f"Executed Quantity: {self.executed_quantity}")

        print(f"Remaining Quantity: {self.remaining_quantity}")
        print(f"Execution Logs:")
        for log in self.execution_logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f" - {timestamp}: {log['quantity']} @ {log['price']}")
