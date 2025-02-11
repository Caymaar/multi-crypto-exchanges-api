from pydantic import BaseModel
from Utilities.DataBaseManager import dbm
import asyncio
from Exchanges import exchange_dict, binance_order_books
from Utilities.SymbolFormatter import SymbolFormatter

# --- Modèle Pydantic pour la soumission d'un TWAP order ---
class TWAPOrderRequest(BaseModel):
    order_id: str
    symbol: str         # Ex : "ETH-USD"
    side: str           # "buy" ou "sell"
    total_quantity: float
    limit_price: float
    duration: int       # Durée en secondes
    interval: int = 1   # Intervalle entre chaque slice en secondes

def update_binance_order_book(key: str, data: dict):
    # On met à jour le carnet global pour le symbole "key"
    print(f"Updating order book for {key}")
    binance_order_books[key] = data

# --- Simulation TWAP Order ---
async def simulate_twap_order(order_id: str, username: str, symbol: str, side: str, total_quantity: float, limit_price: float, duration: int, interval: int = 1):
    """
    Simule l'exécution d'un TWAP order en se basant sur le carnet d'ordre de Binance.
    Le symbole est passé au format standard (ex: "ETH-USD"), mais pour accéder au carnet,
    on doit utiliser le format Binance. Ici, nous supposons que la conversion est simple :
    par exemple, pour "ETH-USD" on utilise "ETHUSDT".
    """
    # Conversion simple : si le symbole standard est "ETH-USD", on remplace '-' par '' et "USD" par "USDT"
    # (dans une application réelle, utilisez un formatter avancé)
    binance_symbol = SymbolFormatter.from_standard(symbol, "binance")
    
    # On démarre une souscription Binance pour mettre à jour le carnet d'ordre global
    # Si ce n'est pas déjà fait, lancez la souscription (en tâche de fond)
    if symbol not in binance_order_books:
        asyncio.create_task(exchange_dict['binance'].subscribe_order_book(binance_symbol, lambda data: update_binance_order_book(symbol, data)))
    await asyncio.sleep(2)  # Laisser le temps de récupérer les premières données
    slice_qty = total_quantity / (duration // interval)
    executed = 0.0
    for i in range(0, duration, interval):
        await asyncio.sleep(interval)
        order_book = binance_order_books.get(symbol)
        if not order_book:
            print(f"Slice {i // interval}: no order book data for {symbol}")
            continue
        
        if side.lower() == "buy":
            asks = order_book.get("asks", [])
            if asks:
                best_ask = min(asks, key=lambda x: x[0])
                current_price = best_ask[0]
                condition_met = current_price <= limit_price
            else:
                condition_met = False
        elif side.lower() == "sell":
            bids = order_book.get("bids", [])
            if bids:
                best_bid = max(bids, key=lambda x: x[0])
                current_price = best_bid[0]
                condition_met = current_price >= limit_price
            else:
                condition_met = False
        else:
            condition_met = False

        if condition_met:
            executed += slice_qty
            dbm.add_order_token(order_id, username, symbol, side, slice_qty, current_price)
        else:
            print(f"Slice {i // interval}: price condition not met for {symbol}")

    dbm.close_order(order_id)
    exchange_dict["binance"].unsubscribe_order_book(binance_symbol)