import asyncio
from datetime import datetime
from Exchange import CoinbasePro, Binance, OKX

class TWAPOrder:
    def __init__(self, exchange, symbol, side, quantity, duration, limit_price=None):
        self.exchange = exchange  # Instance de l'exchange (e.g., Binance(), OKX(), CoinbasePro())
        self.symbol = symbol.upper()
        self.side = side.lower()  # 'buy' ou 'sell'
        self.quantity = quantity
        self.duration = duration
        self.limit_price = limit_price
        self.remaining_quantity = quantity
        self.executed_quantity = 0
        self.execution_logs = []


    async def execute_twap(self):
        """
        Exécute l'ordre TWAP.
        """
        slices = self.duration // 10  # Divise la durée en tranches de 10 secondes
        slice_quantity = self.quantity / slices

        for i in range(slices):
            if self.remaining_quantity <= 0:
                break  # L'ordre est entièrement exécuté

            print(f"Execution de la tranche {i + 1}/{slices} sur {self.exchange.name}...")
            try:
                order_book = await self.exchange.fetch_order_book(self.symbol)
                best_price = None

                if self.side == "buy":
                    best_price = float(order_book["asks"][0][0])  # Meilleur prix d'achat
                elif self.side == "sell":
                    best_price = float(order_book["bids"][0][0])  # Meilleur prix de vente

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

if __name__ == "__main__":
    async def main():
        # Exemple d'utilisation
        exchange_instances = {
            "binance": Binance(),
            "okx": OKX(),
            "coinbase_pro": CoinbasePro()
        }

        # Configuration de l'ordre
        exchange_name = "binance"  # Changez pour "okx" ou "coinbase_pro" si nécessaire
        exchange = exchange_instances[exchange_name]
        symbol = "BTCUSDT"  # Adaptez pour Coinbase Pro si nécessaire (e.g., "BTC-USD")
        side = "buy"
        quantity = 0.01
        duration = 60  # Durée totale en secondes
        limit_price = 40000  # Prix limite facultatif

        twap_order = TWAPOrder(exchange, symbol, side, quantity, duration, limit_price)
        await twap_order.execute_twap()

    asyncio.run(main())
