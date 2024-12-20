from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import asyncio
import json
import websockets
import ssl
import certifi

app = FastAPI()

ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(certifi.where())

# Stockage des données du carnet d'ordres
order_book_data = {}

class WebSocketManager:
    """
    Gère les connexions WebSocket des clients et leurs abonnements.
    """
    def __init__(self):
        self.active_connections: dict[WebSocket, set] = {}  # Associe chaque connexion à ses abonnements

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()  # Initialise sans abonnement

    def disconnect(self, websocket: WebSocket):
        # Supprime les abonnements du client
        if websocket in self.active_connections:
            subscribed_symbols = self.active_connections[websocket]
            for subs in self.active_connections.values():
                print(subs)
            for symbol in subscribed_symbols:
                if symbol in order_book_data:
                    # check if any other client is subscribed to the symbol
                    if not any(symbol in subs for subs in self.active_connections.values()):
                        del order_book_data[symbol]
            del self.active_connections[websocket]
        print(f"Client déconnecté, connexions restantes : {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, symbol: str):
        if websocket in self.active_connections:
            self.active_connections[websocket].add(symbol)

    def unsubscribe(self, websocket: WebSocket, symbol: str):
        if websocket in self.active_connections:
            self.active_connections[websocket].discard(symbol)
            # Supprime le symbole de order_book_data s'il n'est plus surveillé
            if symbol in order_book_data:
                if not any(symbol in subs for subs in self.active_connections.values()):
                    del order_book_data[symbol]

    async def broadcast(self, message: dict):
        for connection in self.active_connections.keys():
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)


manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket pour les clients.
    """
    await manager.connect(websocket)
    print("Client connecté.")
    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            if action == "subscribe":
                symbol = message.get("symbol")
                if symbol:
                    print(f"Client abonné au symbole : {symbol}")
                    # Ajouter le symbole à la liste de surveillance
                    manager.subscribe(websocket, symbol)
                    if symbol not in order_book_data:
                        order_book_data[symbol] = {"bids": [], "asks": []}
            elif action == "unsubscribe":
                symbol = message.get("symbol")
                if symbol:
                    print(f"Client désabonné du symbole : {symbol}")
                    manager.unsubscribe(websocket, symbol)
    except WebSocketDisconnect:
        print("Client déconnecté.")
        manager.disconnect(websocket)


async def fetch_binance_order_book():
    """
    Collecte les données de carnets d'ordres depuis Binance.
    """
    url = "wss://stream.binance.com:9443/ws"
    while True:
        try:
            async with websockets.connect(url, ssl=ssl_context) as websocket:
                print("Connecté à Binance WebSocket")
                while True:
                    # Obtenir les symboles à surveiller
                    for symbol in order_book_data.keys():
                        stream_name = f"{symbol.lower()}@depth10"
                        subscribe_message = {
                            "method": "SUBSCRIBE",
                            "params": [stream_name],
                            "id": 1
                        }
                        await websocket.send(json.dumps(subscribe_message))
                        print(f"Abonnement envoyé pour {symbol} sur Binance.")

                    # Écoute des messages
                    message = await websocket.recv()
                    data = json.loads(message)
                    print("Message reçu Binance:", data)  # Debugging
                    if "b" in data and "a" in data:  # Vérifie le carnet d'ordres
                        symbol = data.get("s", "").upper()
                        if symbol in order_book_data:
                            order_book_data[symbol] = {
                                "bids": [{"price": bid[0], "quantity": bid[1]} for bid in data["b"][:10]],
                                "asks": [{"price": ask[0], "quantity": ask[1]} for ask in data["a"][:10]],
                                "timestamp": datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"Erreur WebSocket Binance : {e}")
            await asyncio.sleep(1)

async def fetch_kraken_order_book():
    """
    Collecte les données de carnets d'ordres depuis Kraken.
    """
    url = "wss://ws.kraken.com"
    while True:
        try:
            async with websockets.connect(url, ssl=ssl_context) as websocket:
                print("Connecté à Kraken WebSocket")
                subscribe_message = {
                    "event": "subscribe",
                    "pair": list(order_book_data.keys()),  # Paires dynamiques
                    "subscription": {"name": "book"}
                }
                await websocket.send(json.dumps(subscribe_message))
                print(f"Abonnement envoyé pour les paires sur Kraken: {list(order_book_data.keys())}")

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print("Message reçu Kraken:", data)  # Debugging
                    if isinstance(data, list) and len(data) > 1:
                        pair = data[-1]
                        book_data = data[1]
                        if pair in order_book_data:
                            order_book_data[pair] = {
                                "bids": [{"price": bid[0], "quantity": bid[1]} for bid in book_data.get("b", [])[:10]],
                                "asks": [{"price": ask[0], "quantity": ask[1]} for ask in book_data.get("a", [])[:10]],
                                "timestamp": datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"Erreur WebSocket Kraken : {e}")
            await asyncio.sleep(1)

async def broadcast_order_book_updates():
    """
    Envoie les mises à jour des carnets d'ordres à tous les clients connectés.
    """
    while True:
        for symbol, data in order_book_data.items():
            await manager.broadcast({symbol: data})
        await asyncio.sleep(1)

async def update_subscriptions():
    """
    Met à jour dynamiquement les abonnements pour Binance et Kraken.
    """
    while True:
        # Récupérer la liste des symboles à surveiller
        symbols = list(order_book_data.keys())
        print(f"Symboles surveillés : {symbols}")

        # Relancer les abonnements si nécessaire (à implémenter si les exchanges le nécessitent)
        await asyncio.sleep(5)  # Vérification périodique

@app.get("/")
def read_root():
    return {"message": "WebSocket API for Market Data"}

@app.on_event("startup")
async def startup_event():
    """
    Démarre les tâches asynchrones au démarrage de l'application.
    """
    app.state.binance_task = asyncio.create_task(fetch_binance_order_book())
    app.state.kraken_task = asyncio.create_task(fetch_kraken_order_book())
    app.state.broadcast_task = asyncio.create_task(broadcast_order_book_updates())
    app.state.subscription_task = asyncio.create_task(update_subscriptions())

@app.on_event("shutdown")
async def shutdown_event():
    """
    Annule les tâches à l'arrêt de l'application.
    """
    app.state.binance_task.cancel()
    app.state.kraken_task.cancel()
    app.state.broadcast_task.cancel()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)