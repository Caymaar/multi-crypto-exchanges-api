import websockets
import json
from typing import Dict, List, Any
import ssl
import asyncio

ssl_context = ssl._create_default_https_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class WebSocketManager:
    """
    A class to manage WebSocket connections to different exchanges and retrieve order book data.

    This class supports connecting to Binance WebSocket streams to fetch order book data.
    """

    def __init__(self) -> None:
        """
        Initializes the WebSocketManager instance, setting up a dictionary to store connections.
        """
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}

    async def connect_binance(self, symbol: str) -> websockets.WebSocketClientProtocol:
        """
        Establishes a WebSocket connection to Binance for a specific trading pair.

        Args:
            symbol (str): The trading pair symbol, e.g., "BTCUSDT".

        Returns:
            websockets.WebSocketClientProtocol: The WebSocket connection object.
        """
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth5"
        return await websockets.connect(url, ssl=ssl_context)

    async def get_order_book_data(self, exchange_name: str, symbol: str) -> Dict[str, List[Dict[str, float]]]:
        """
        Retrieves the order book data from a specified exchange.

        Args:
            exchange_name (str): The exchange name, e.g., "binance".
            symbol (str): The trading pair symbol, e.g., "BTCUSDT".

        Returns:
            Dict[str, List[Dict[str, float]]]: A dictionary containing the bids and asks with their prices and quantities.

        Raises:
            ValueError: If the provided exchange is not supported.
        """
        if exchange_name == "binance":
            ws = await self.connect_binance(symbol)
        else:
            raise ValueError("Unsupported exchange.")

        # Wait for the response from the WebSocket
        order_book_data = await ws.recv()
        return self.parse_order_book_data(exchange_name, order_book_data)

    def parse_order_book_data(self, exchange_name: str, data: str) -> Dict[str, List[Dict[str, float]]]:
        """
        Parses the order book data based on the exchange.

        Args:
            exchange_name (str): The exchange name, e.g., "binance".
            data (str): The raw order book data received from the WebSocket.

        Returns:
            Dict[str, List[Dict[str, float]]]: A dictionary containing bids and asks with prices and quantities.

        Notes:
            This method specifically handles Binance order book data format.
        """
        parsed_data: Dict[str, Any] = json.loads(data)

        if exchange_name == "binance":
            return {
                "bids": [{"price": float(bid[0]), "quantity": float(bid[1])} for bid in parsed_data["bids"]],
                "asks": [{"price": float(ask[0]), "quantity": float(ask[1])} for ask in parsed_data["asks"]]
            }

        return {}

async def main():
    manager = WebSocketManager()
    order_book = await manager.get_order_book_data("binance", "BTCUSDT")
    print(order_book)

# Use asyncio.run() to run the event loop (recommended over get_event_loop())
if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())