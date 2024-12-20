from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import websockets
import json
from datetime import datetime
import ssl
import certifi

app = FastAPI()

ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(certifi.where())


class SubscriptionManager:
    def __init__(self):
        self.clients = {}  # {websocket: set(symbols)}
        self.symbol_subscriptions = {}  # {symbol: set(websockets)}
        self.exchange_connections = {}  # {symbol: asyncio.Task}

    async def connect_client(self, websocket: WebSocket):
        """Connecte un nouveau client."""
        await websocket.accept()
        self.clients[websocket] = set()  # Le client commence sans abonnement
        print(f"Client connecté : {len(self.clients)} clients connectés.")

    def disconnect_client(self, websocket: WebSocket):
        """Déconnecte un client et nettoie les abonnements."""
        if websocket in self.clients:
            # Supprimer les abonnements du client
            subscribed_symbols = self.clients.pop(websocket)
            for symbol in subscribed_symbols:
                self.remove_subscription(symbol, websocket)

        print(f"Client déconnecté : {len(self.clients)} clients restants.")

    def add_subscription(self, symbol: str, websocket: WebSocket):
        """Ajoute une souscription pour un client à un symbole."""
        self.clients[websocket].add(symbol)

        # Ajouter le client à la liste des abonnés au symbole
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()
            # Démarrer une connexion à l'exchange pour ce symbole
            self.exchange_connections[symbol] = asyncio.create_task(self.fetch_symbol_data(symbol))
    
        self.symbol_subscriptions[symbol].add(websocket)
        print(f"Client abonné à {symbol}. Total abonnés : {len(self.symbol_subscriptions[symbol])}.")

    def remove_subscription(self, symbol: str, websocket: WebSocket):
        """Supprime une souscription pour un client à un symbole."""
        if websocket in self.clients and symbol in self.clients[websocket]:
            self.clients[websocket].remove(symbol)

        if symbol in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol].discard(websocket)

            # Si aucun client n'est abonné, arrêter la connexion
            if not self.symbol_subscriptions[symbol]:
                del self.symbol_subscriptions[symbol]
                # Annuler la tâche de connexion à l'exchange
                if symbol in self.exchange_connections:
                    self.exchange_connections[symbol].cancel()
                    del self.exchange_connections[symbol]
                print(f"Connexion à l'exchange arrêtée pour {symbol}.")

    async def fetch_symbol_data(self, symbol: str):
        """Connexion WebSocket à l'exchange pour récupérer les données d'un symbole."""
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth10"
        try:
            async with websockets.connect(url, ssl=ssl_context) as websocket:
                print(f"Connexion à Binance pour {symbol}.")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if symbol in self.symbol_subscriptions:
                        # Diffuser les données aux abonnés
                        for client in self.symbol_subscriptions[symbol]:
                            try:
                                await client.send_json({symbol: data})
                            except WebSocketDisconnect:
                                self.disconnect_client(client)
        except asyncio.CancelledError:
            print(f"Connexion WebSocket annulée pour {symbol}.")
        except Exception as e:
            print(f"Erreur avec {symbol} : {e}")


manager = SubscriptionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Gère la connexion WebSocket d'un client."""
    await manager.connect_client(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            symbol = message.get("symbol")

            if action == "subscribe" and symbol:
                manager.add_subscription(symbol, websocket)
            elif action == "unsubscribe" and symbol:
                manager.remove_subscription(symbol, websocket)
    except WebSocketDisconnect:
        manager.disconnect_client(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)