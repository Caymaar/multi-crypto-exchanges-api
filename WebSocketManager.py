import asyncio
import websockets
import json
import time
import hmac
import hashlib
import base64


class WebSocketManager:
    def __init__(self, binance_api_key=None, binance_api_secret=None, okx_api_key=None, okx_api_secret=None,
                 coinbase_api_key=None, coinbase_api_secret=None, coinbase_passphrase=None):
        self.connections = {}

        # Store API keys for authenticated connections
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.okx_api_key = okx_api_key
        self.okx_api_secret = okx_api_secret
        self.coinbase_api_key = coinbase_api_key
        self.coinbase_api_secret = coinbase_api_secret
        self.coinbase_passphrase = coinbase_passphrase

    async def connect_binance(self, symbol):
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth5"
        return await websockets.connect(url)

    async def connect_okx(self, symbol):
        url = f"wss://ws.okx.com:8443/ws/v5/public/market/depth?instId={symbol}"
        if self.okx_api_key and self.okx_api_secret:
            # Optional: Add authentication header for private channels if required
            headers = {
                'API-KEY': self.okx_api_key,
                'API-SECRET': self.okx_api_secret,
            }
        else:
            headers = {}

        return await websockets.connect(url, extra_headers=headers)

    async def connect_coinbase(self):
        url = "wss://ws-feed.pro.coinbase.com"

        if self.coinbase_api_key and self.coinbase_api_secret and self.coinbase_passphrase:
            # WebSocket authentication for Coinbase Pro
            timestamp = str(int(time.time()))
            message = timestamp + 'GET' + '/users/self/verify'
            signature = self._generate_coinbase_signature(message)

            headers = {
                'CB-ACCESS-KEY': self.coinbase_api_key,
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-PASSPHRASE': self.coinbase_passphrase,
            }
        else:
            headers = {}

        return await websockets.connect(url, extra_headers=headers)

    def _generate_coinbase_signature(self, message):
        """
        Generates a Coinbase signature.
        """
        message = message.encode('utf-8')
        key = self.coinbase_api_secret.encode('utf-8')
        return base64.b64encode(hmac.new(key, message, hashlib.sha256).digest()).decode()

    async def get_order_book_data(self, exchange_name, symbol):
        """
        Retourne les données du carnet d'ordres pour un exchange donné.
        """
        if exchange_name == "binance":
            ws = await self.connect_binance(symbol)
        elif exchange_name == "okx":
            ws = await self.connect_okx(symbol)
        elif exchange_name == "coinbase_pro":
            ws = await self.connect_coinbase()
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

        elif exchange_name == "okx":
            # Exemple de traitement des données pour OKX
            return {
                "bids": [{"price": float(bid[0]), "quantity": float(bid[1])} for bid in parsed_data["data"]["bids"]],
                "asks": [{"price": float(ask[0]), "quantity": float(ask[1])} for ask in parsed_data["data"]["asks"]]
            }

        elif exchange_name == "coinbase_pro":
            # Exemple de traitement des données pour Coinbase Pro
            return {
                "bids": [{"price": float(bid[0]), "quantity": float(bid[1])} for bid in parsed_data["bids"]],
                "asks": [{"price": float(ask[0]), "quantity": float(ask[1])} for ask in parsed_data["asks"]]
            }

        return {}


