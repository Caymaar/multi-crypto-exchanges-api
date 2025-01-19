import asyncio
import websockets
import json
import time
import hmac
import hashlib
import base64


class WebSocketManager:
    def __init__(self):
        self.connections = {}


    async def connect_binance(self, symbol):
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth5"
        return await websockets.connect(url)


    async def get_order_book_data(self, exchange_name, symbol):
        """
        Retourne les données du carnet d'ordres pour un exchange donné.
        """
        if exchange_name == "binance":
            ws = await self.connect_binance(symbol)
        else:
            raise ValueError("Exchange non supporté.")

        # Attendre la réponse du WebSocket
        order_book_data = await ws.recv()
        return self.parse_order_book_data(exchange_name, order_book_data)

    def parse_order_book_data(self, exchange_name, data):
        """
        Parse les données du carnet d'ordres selon l'exchange.
        """
        parsed_data = json.loads(data)

        if exchange_name == "binance":
            # Exemple de traitement des données pour Binance
            return {
                "bids": [{"price": float(bid[0]), "quantity": float(bid[1])} for bid in parsed_data["bids"]],
                "asks": [{"price": float(ask[0]), "quantity": float(ask[1])} for ask in parsed_data["asks"]]
            }

        return {}


