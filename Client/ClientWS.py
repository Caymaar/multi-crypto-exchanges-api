import asyncio
import aiohttp
import requests

def choose_exchange(exchanges: dict) -> tuple[str, float]:
    """
    Sélectionne l'exchange qui offre la quantité maximale pour un niveau donné.
    Renvoie un tuple (exchange, quantity).  
    Si le dictionnaire est vide, renvoie ("", 0).
    """
    if not exchanges:
        return "", 0.0
    best_exch = max(exchanges, key=lambda k: exchanges[k])
    return best_exch, exchanges[best_exch]

def print_order_book(aggregated: dict) -> None:
    """
    Affiche le carnet d'ordre agrégé dans un format propre.
    Le format reçu est supposé être :
    {
        "standard_symbol": "ETH-USD",
        "bids": [
            {"price": 2765.13, "exchanges": {"kraken": 15.18}, "total": 15.18},
            ...
        ],
        "asks": [
            {"price": 2751.25, "exchanges": {"binance": 33.88}, "total": 33.88},
            ...
        ]
    }
    Pour chaque rangée, on affiche le meilleur bid (exchange, prix, quantité)
    et le meilleur ask (prix, quantité, exchange).
    """
    standard_symbol = aggregated.get("standard_symbol", "N/A")
    bids = aggregated.get("bids", [])
    asks = aggregated.get("asks", [])
    
    print(f"\nAggregated Order Book for {standard_symbol}")
    header = f"{'Bid Exch':12s} | {'Bid Qty':10s} | {'Bid Price':10s} || {'Ask Price':10s} | {'Ask Qty':10s} | {'Ask Exch':12s}"
    print(header)
    print("-" * len(header))
    # On affiche autant de rangées que le maximum entre le nombre de bids et d'asks
    n_rows = max(len(bids), len(asks))
    for i in range(n_rows):
        if i < len(bids):
            bid_level = bids[i]
            bid_price = bid_level.get("price", 0.0)
            bid_exchanges = bid_level.get("exchanges", {})
            bid_exch, bid_qty = choose_exchange(bid_exchanges)
        else:
            bid_price, bid_qty, bid_exch = 0.0, 0.0, ""
        
        if i < len(asks):
            ask_level = asks[i]
            ask_price = ask_level.get("price", 0.0)
            ask_exchanges = ask_level.get("exchanges", {})
            ask_exch, ask_qty = choose_exchange(ask_exchanges)
        else:
            ask_price, ask_qty, ask_exch = 0.0, 0.0, ""
        
        # Formatage : on affiche les nombres avec 2 décimales
        row = f"{bid_exch:12s} | {bid_qty:10.2f} | {bid_price:10.2f} || {ask_price:10.2f} | {ask_qty:10.2f} | {ask_exch:12s}"
        print(row)
    print("-" * len(header), "\n")

async def ws_client():

    # username = "newuser"
    # password = "newpassword"

    response = requests.post(
        "http://localhost:8000/login",
        json={"username": "newuser", "password": "newpassword"}
    )

    # Try to parse response as JSON
    response_data = response.json()
    response_data["access_token"]

    # Adresse du WebSocket (ajustez le port et le token si nécessaire)
    url = f"ws://localhost:8000/ws?token={response_data['access_token']}"  # Remplacez VOTRE_TOKEN par votre token réel
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            # Envoyer des messages de souscription pour ETH-USD sur trois exchanges
            subscriptions = [
                {"action": "subscribe", "exchange": "binance", "symbol": "ETH-USD"},
                {"action": "subscribe", "exchange": "kraken", "symbol": "ETH-USD"},
                {"action": "subscribe", "exchange": "okx", "symbol": "ETH-USD"}
            ]
            for sub in subscriptions:
                await ws.send_json(sub)
                print(f"Sent subscription: {sub}")

            # Réception des messages agrégés
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    # On s'attend à recevoir un JSON de la forme :
                    # {
                    #     "standard_symbol": "ETH-USD",
                    #     "bids": [ ... ],
                    #     "asks": [ ... ]
                    # }
                    print_order_book(data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("WebSocket error")
                    break

if __name__ == "__main__":
    asyncio.run(ws_client())