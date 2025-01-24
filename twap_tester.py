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
    duration = 5  # Durée totale en secondes
    slice_interval = 1  # Intervalle entre les tranches en secondes
    limit_price = 105580  # Prix limite facultatif

    # Crée une instance de TWAPOrder avec les nouveaux paramètres
    twap_order = TWAPOrder(
        token_id="order123",  # Assurez-vous que le token_id est unique pour chaque ordre
        exchange=exchange,
        symbol=symbol,
        side=side,
        quantity=quantity,
        duration=duration,
        slice_interval=slice_interval,
        limit_price=limit_price,
        ws_manager=ws_manager
    )

    # Exécute l'ordre TWAP
    await twap_order.execute_twap()



# Exécution principale
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
