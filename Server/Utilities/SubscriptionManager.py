import asyncio
from fastapi import WebSocket
from Exchanges import exchange_dict  # Nos instances d'exchanges (Binance, OKX, Kraken, etc.)

class AggregatedSubscription:
    def __init__(self, standard_symbol: str):
        self.standard_symbol = standard_symbol  # ex: "BTC-USD"
        self.exchange_data = {}   # mapping : exchange -> dernière donnée (order book)
        self.feed_tasks = {}      # mapping : exchange -> tâche asynchrone du flux
        self.clients = set()      # ensemble des WebSocket abonnés à ce symbole agrégé
        self.broadcast_task = None

    async def add_exchange(self, exchange: str, exchange_specific_symbol: str):
        # Si nous sommes déjà abonnés à cet exchange, on ne fait rien
        if exchange in self.feed_tasks:
            return

        # Définir une fonction callback qui met à jour self.exchange_data pour cet exchange
        def callback(data, exchange=exchange):
            self.exchange_data[exchange] = data

        # Démarrer le flux de l'exchange en passant la callback
        task = asyncio.create_task(
            exchange_dict[exchange].subscribe_order_book(exchange_specific_symbol, callback)
        )
        self.feed_tasks[exchange] = task

    async def remove_exchange(self, exchange: str):
        if exchange in self.feed_tasks:
            self.feed_tasks[exchange].cancel()
            del self.feed_tasks[exchange]
            if exchange in self.exchange_data:
                del self.exchange_data[exchange]

    async def run(self):
        try:
            while True:
                await asyncio.sleep(1)
                if self.exchange_data:
                    # On va créer deux dictionnaires d'agrégation pour les bids et les asks.
                    aggregated_bids = {}
                    aggregated_asks = {}
                    # Parcours de chaque flux provenant d'un exchange
                    for exch, data in self.exchange_data.items():
                        # On suppose que 'data' est un dictionnaire avec les clés "bids" et "asks"
                        # et que chacune est une liste de [price, quantity].
                        for bid in data.get("bids", []):
                            price, qty = bid[0], bid[1]
                            # Ajout dans aggregated_bids
                            if price in aggregated_bids:
                                aggregated_bids[price][exch] = qty
                            else:
                                aggregated_bids[price] = {exch: qty}
                        for ask in data.get("asks", []):
                            price, qty = ask[0], ask[1]
                            if price in aggregated_asks:
                                aggregated_asks[price][exch] = qty
                            else:
                                aggregated_asks[price] = {exch: qty}
                    
                    # Conversion des dictionnaires en listes de niveaux triées.
                    bids_list = []
                    for price, exch_data in aggregated_bids.items():
                        total = sum(exch_data.values())
                        bids_list.append({
                            "price": price,
                            "exchanges": exch_data,
                            "total": total
                        })
                    # Les bids sont triées par prix décroissant (meilleur bid en premier)
                    bids_list.sort(key=lambda x: x["price"], reverse=True)
                    
                    asks_list = []
                    for price, exch_data in aggregated_asks.items():
                        total = sum(exch_data.values())
                        asks_list.append({
                            "price": price,
                            "exchanges": exch_data,
                            "total": total
                        })
                    # Les asks sont triées par prix croissant (meilleur ask en premier)
                    asks_list.sort(key=lambda x: x["price"])
                    
                    # Construction du JSON agrégé final
                    aggregated = {
                        "standard_symbol": self.standard_symbol,
                        "bids": bids_list,
                        "asks": asks_list
                    }
                    
                    # Diffusion à tous les clients abonnés
                    for client in list(self.clients):
                        try:
                            await client.send_json(aggregated)
                        except Exception:
                            self.clients.remove(client)
        except asyncio.CancelledError:
            for task in self.feed_tasks.values():
                task.cancel()
            raise

class AggregatedSubscriptionManager:
    def __init__(self):
        # Clé: symbole standard (ex: "BTC-USD")
        # Valeur: instance d'AggregatedSubscription
        self.subscriptions = {}

    async def subscribe(self, client: WebSocket, exchange: str, symbol: str, formatter) -> None:
        """
        Ajoute le client à l'abonnement agrégé pour le symbole standard obtenu depuis l'input.
        La méthode ajoute aussi le flux de l'exchange (au format spécifique) s'il n'est pas déjà présent.
        """
        # On convertit l'input en format standard, ex: "BTC-USD"
        standard_symbol = formatter.to_standard(symbol)
        # On obtient le symbole propre à l'exchange (par exemple "BTCUSDT" pour Binance)
        exchange_specific_symbol = formatter.format_input(symbol, exchange)
        if standard_symbol not in self.subscriptions:
            agg_sub = AggregatedSubscription(standard_symbol)
            agg_sub.clients.add(client)
            self.subscriptions[standard_symbol] = agg_sub
            await agg_sub.add_exchange(exchange, exchange_specific_symbol)
            agg_sub.broadcast_task = asyncio.create_task(agg_sub.run())
        else:
            agg_sub = self.subscriptions[standard_symbol]
            agg_sub.clients.add(client)
            await agg_sub.add_exchange(exchange, exchange_specific_symbol)

    async def unsubscribe(self, client: WebSocket, exchange: str, symbol: str, formatter) -> None:
        """
        Retire le client de l'abonnement agrégé pour le symbole standard.
        Si plus aucun client n'est abonné, l'abonnement est annulé.
        """
        standard_symbol = formatter.to_standard(symbol)
        if standard_symbol in self.subscriptions:
            agg_sub = self.subscriptions[standard_symbol]
            if client in agg_sub.clients:
                agg_sub.clients.remove(client)
            # Optionnel : on peut retirer le flux de l'exchange en cas de désabonnement individuel
            # (selon votre logique métier)
            if not agg_sub.clients:
                if agg_sub.broadcast_task:
                    agg_sub.broadcast_task.cancel()
                for task in agg_sub.feed_tasks.values():
                    task.cancel()
                del self.subscriptions[standard_symbol]

