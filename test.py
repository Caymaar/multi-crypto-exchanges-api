import asyncio
import websockets
import json

async def connect_to_okx():
    url = "wss://ws.okx.com:8443/ws/v5/public"  # URL WebSocket correcte pour OKX

    # Message de souscription avec le bon canal 'spot/orderBook' et instId
    subscribe_message = {
        "op": "subscribe",
        "args": [{"channel": "spot/orderBook", "instId": "BTC-USDT"}]
    }

    try:
        # Connexion WebSocket
        async with websockets.connect(url) as ws:
            print("Connexion WebSocket réussie.")
            await ws.send(json.dumps(subscribe_message))
            while True:
                message = await ws.recv()  # Recevoir les données du WebSocket
                print(message)  # Afficher les données reçues du WebSocket
    except Exception as e:
        print(f"Erreur lors de la connexion WebSocket : {e}")

# Lancer la connexion WebSocket
asyncio.run(connect_to_okx())