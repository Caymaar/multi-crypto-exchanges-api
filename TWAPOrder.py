from datetime import datetime
import asyncio


class TWAPOrder:
    def __init__(self, exchange, symbol, side, quantity, duration, limit_price=None, ws_manager=None):
        self.exchange = exchange  # Instance de l'exchange (e.g., Binance(), OKX(), CoinbasePro())
        self.symbol = symbol.upper()
        self.side = side.lower()  # 'buy' ou 'sell'
        self.quantity = quantity
        self.duration = duration
        self.limit_price = limit_price
        self.remaining_quantity = quantity
        self.executed_quantity = 0
        self.execution_logs = []
        self.ws_manager = ws_manager  # Instance de WebSocketManager
        self.order_book_data = {"bids": [], "asks": []}  # Pour stocker les données du carnet d'ordres en temps réel

    async def connect_websocket(self):
        """
        Utilise WebSocketManager pour se connecter et récupérer les données du carnet d'ordres en temps réel.
        """
        self.symbol = self.format_symbol_for_exchange(self.exchange.name, self.symbol)
        print(f"Connexion WebSocket pour {self.exchange.name} avec {self.symbol}")

        # Get order book data using WebSocketManager
        self.order_book_data = await self.ws_manager.get_order_book_data(self.exchange.name, self.symbol)
        print(f"WebSocket connecté pour {self.symbol} sur {self.exchange.name}")

    async def execute_twap(self):
        """
        Exécute l'ordre TWAP en utilisant les données du carnet d'ordres en temps réel.
        """
        slices = self.duration // 10  # Divise la durée en tranches de 10 secondes
        slice_quantity = self.quantity / slices

        # Connexion WebSocket pour récupérer les données du carnet d'ordres
        await self.connect_websocket()

        for i in range(slices):
            if self.remaining_quantity <= 0:
                break

            print(f"Execution de la tranche {i + 1}/{slices} sur {self.exchange.name}...")
            try:
                # Utilisation des données du carnet d'ordres en temps réel
                best_price = None
                if self.side == "buy":
                    best_price = float(self.order_book_data["asks"][0]["price"])  # Meilleur prix d'achat
                elif self.side == "sell":
                    best_price = float(self.order_book_data["bids"][0]["price"])  # Meilleur prix de vente

                # Si un prix limite est défini, on vérifie si le prix actuel respecte la condition
                if self.limit_price is None or (
                        (self.side == "buy" and best_price <= self.limit_price) or
                        (self.side == "sell" and best_price >= self.limit_price)
                ):
                    executed_now = min(slice_quantity, self.remaining_quantity)
                    self.remaining_quantity -= executed_now
                    self.executed_quantity += executed_now
                    self.execution_logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "price": best_price,
                        "quantity": executed_now
                    })
                    print(f"Exécuté {executed_now} à un prix de {best_price}")
                else:
                    print(f"Tranche {i + 1} ignorée : prix limite non atteint.")

            except Exception as e:
                print(f"Erreur pendant l'exécution de la tranche : {e}")

            await asyncio.sleep(10)  # Attend avant la tranche suivante

        print(f"Exécution de l'ordre TWAP terminée sur {self.exchange.name}")
        self.report()

    def format_symbol_for_exchange(self, exchange_name, symbol):
        """
        Ajuste le format du symbole en fonction de l'exchange.
        """
        if exchange_name.lower() == "binance":
            return symbol.replace("-", "").replace("/", "")
        elif exchange_name.lower() == "okx":
            if "-" not in symbol:
                return f"{symbol[:-4]}-{symbol[-4:]}"
            return symbol
        elif exchange_name.lower() == "coinbase_pro":
            if "-" not in symbol:
                symbol = f"{symbol[:-4]}-{symbol[-4:]}"
            return symbol.replace("USDT", "USD")
        else:
            raise ValueError(f"Exchange {exchange_name} non supporté.")

    def report(self):
        """
        Génère un rapport récapitulatif de l'exécution.
        """
        print("\nRapport d'exécution :")
        print(f"Exchange : {self.exchange.name}")
        print(f"Symbole : {self.symbol}")
        print(f"Type : {self.side}")
        print(f"Quantité totale : {self.quantity}")
        print(f"Quantité exécutée : {self.executed_quantity}")
        print(f"Quantité restante : {self.remaining_quantity}")
        print(f"Logs d'exécution :")
        for log in self.execution_logs:
            print(f" - {log['timestamp']}: {log['quantity']} @ {log['price']}")

