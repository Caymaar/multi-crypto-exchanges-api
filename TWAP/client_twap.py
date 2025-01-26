import requests
import time
import asyncio
from WebSocketManager import WebSocketManager  # Import the WebSocketManager class
import sys
import nest_asyncio

# Fix "RuntimeError: This event loop is already running" error on Jupyter Notebook
nest_asyncio.apply()

# Constants for API
API_URL = "http://localhost:8005"  # Change if API is hosted elsewhere
API_KEY = "dd8aa84526f720a9b4f73456b98eaa1ec49e5718e2b59b38a12331b6c2b1bef4"  # Your API key here

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Client:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.session = None  # This will hold the authenticated session (if any)
        self.ws_manager = WebSocketManager()  # WebSocket manager instance for order book data

    def authenticate(self):
        """
        Authenticate and start a session by sending the API key to the server.
        This will check the API key with the database on the server.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.get(f"{self.api_url}/", headers=headers)
        if response.status_code == 200:
            print("Authentication successful.")
            self.session = response.cookies
        else:
            print(f"Authentication failed: {response.text}")
            self.session = None

    def submit_twap_order(self, order_data):
        """
        Submit a TWAP order via the REST API.
        order_data: dict containing order details like token_id, exchange, symbol, etc.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(f"{self.api_url}/orders/twap", json=order_data, headers=headers)
        if response.status_code == 200:
            print(f"Order submitted: {response.json()}")
            return response.json()
        else:
            print(f"Order submission failed: {response.text}")
            return None


    def check_order_status(self, token_id):
        """
        Check the status of a TWAP order.
        token_id: The unique ID of the order.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.get(f"{self.api_url}/orders/{token_id}", headers=headers)
        if response.status_code == 200:
            print(f"Order status: {response.json()}")
            return response.json()
        else:
            print(f"Failed to check order status: {response.text}")
            return None

    async def monitor_order_book(self, exchange_name, symbol):
        """
        Connect to the WebSocket and monitor the order book data for the specified exchange and symbol.
        """
        print(f"Connecting to WebSocket for {exchange_name} - {symbol}...")
        order_book_data = await self.ws_manager.get_order_book_data(exchange_name, symbol)
        print(f"Received order book data: {order_book_data}")

    async def start_websocket_and_monitor(self, exchange_name, symbol):
        """
        Start the WebSocket connection to monitor real-time order book updates.
        """
        await self.monitor_order_book(exchange_name, symbol)

async def run_client_operations():
    client = Client(api_url=API_URL, api_key=API_KEY)

    # Step 1: Authenticate
    client.authenticate()

    # Step 2: Submit a TWAP Order
    order_data = [
        {
            "token_id": "12345",
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "quantity": 0.5,
            "duration": 50,
            "price": 110000,
            "start_time": "2025-01-25T00:00:00",
            "end_time": "2025-01-25T01:00:00",
            "interval": 10
        }
    ]

    order_response = client.submit_twap_order(order_data)

    # Step 3: Track the order status with REST API calls
    if order_response:
        token_id = order_response[0]["token_id"]
        print("Checking order status...")
        time.sleep(5)  # Delay to simulate checking periodically
        client.check_order_status(token_id)

    # Step 4: Monitor the order book via WebSocket connection (real-time updates)
    print("Connecting to WebSocket for real-time updates...")
    await client.start_websocket_and_monitor("binance", "BTCUSDT")

if __name__ == "__main__":
    asyncio.run(run_client_operations())
