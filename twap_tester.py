# main.py
import asyncio
from Exchange import Binance, OKX, CoinbasePro
from WebSocketManager import WebSocketManager
from TWAPOrder import TWAPOrder


async def main():
    # Crée une instance de WebSocketManager
    ws_manager = WebSocketManager()

    # Crée des instances des exchanges avec authentification
    exchange_instances = {
        "binance": Binance(),
    }

    # Configuration de l'ordre
    exchange_name = "binance"  # Changez pour "okx" ou "binance" si nécessaire
    exchange = exchange_instances[exchange_name]
    symbol = "BTCUSDT"
    side = "buy"
    quantity = 0.01
    duration = 60  # Durée totale en secondes
    limit_price = 40000  # Prix limite facultatif

    # Crée une instance de TWAPOrder
    twap_order = TWAPOrder(exchange, symbol, side, quantity, duration, limit_price, ws_manager)

    # Exécute l'ordre TWAP
    await twap_order.execute_twap()


# Exécution principale
if __name__ == "__main__":
    asyncio.run(main())
