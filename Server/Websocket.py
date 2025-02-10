import asyncio
from Exchanges import exchange_dict  # assuming your exchange_dict includes the instantiated exchanges

def print_order_book(data):
    print(f"[{data['exchange']}] {data['symbol']} order book update:")
    print("Bids:", data["bids"])
    print("Asks:", data["asks"])
    print("Timestamp:", data["timestamp"])
    print("-" * 40)

async def main():
    # For example, subscribe to BTCUSDT on Binance
    asyncio.create_task(exchange_dict["binance"].subscribe_order_book("BTCUSDT", print_order_book))
    # Subscribe to BTC-USDT on OKX
    asyncio.create_task(exchange_dict["okx"].subscribe_order_book("BTC-USD", print_order_book))
    # Subscribe to BTC-USD on Coinbase Pro
    #asyncio.create_task(exchange_dict["coinbase_pro"].subscribe_order_book("BTCUSD", print_order_book))
    # Subscribe to XBT/USD on Kraken
    asyncio.create_task(exchange_dict["kraken"].subscribe_order_book("XBT/USD", print_order_book))
    # Keep the main loop alive.
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())