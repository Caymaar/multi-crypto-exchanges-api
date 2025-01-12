# main.py
import asyncio
from Exchange import Binance, OKX, CoinbasePro
from WebSocketManager import WebSocketManager
from TWAPOrder import TWAPOrder


async def main():
    # Crée une instance de WebSocketManager
    ws_manager = WebSocketManager()

    # Clés API pour les échanges
    binance_api_key = "ncFKb1E23hEOrpQFrcMfj6nTVJuBBIRWE3sVQHCfsaiqubo37fzjBNW3w2nhIV4s"
    binance_api_secret = "YOUR_BINANCE_API_SECRET"

    okx_api_key = "YOUR_OKX_API_KEY"
    okx_api_secret = "YOUR_OKX_API_SECRET"

    coinbase_api_key = "YOUR_COINBASE_API_KEY"
    coinbase_api_secret = "YOUR_COINBASE_API_SECRET"
    coinbase_passphrase = "YOUR_COINBASE_PASSPHRASE"

    # Crée des instances des exchanges avec authentification
    exchange_instances = {
        "binance": Binance(binance_api_key, binance_api_secret),
        "okx": OKX(okx_api_key, okx_api_secret),
        "coinbase_pro": CoinbasePro(coinbase_api_key, coinbase_api_secret, coinbase_passphrase)
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
