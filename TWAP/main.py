from client_twap import Client
import nest_asyncio
import sys
import asyncio
import time

nest_asyncio.apply()

# Constants for API
API_URL = "http://localhost:8005"  # Change if API is hosted elsewhere
API_KEY = "a25bf8c6d290050d59e9501188bf6efd66aea9166a694bb2320ed0ed384ffbcb65E"  # Your API key here

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
            "duration": 10,
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
        time.sleep(10)  # Delay to simulate checking periodically
        client.check_order_status(token_id)

    # Step 4: Monitor the order book via WebSocket connection (real-time updates)
    print("Connecting to WebSocket for real-time updates...")
    await client.start_websocket_and_monitor("binance", "BTCUSDT")

if __name__ == "__main__":
    asyncio.run(run_client_operations())