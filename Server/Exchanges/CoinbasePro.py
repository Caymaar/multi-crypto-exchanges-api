from Exchanges.Abstract import Exchange
import requests
import asyncio
import aiohttp
from datetime import datetime

class CoinbasePro(Exchange):
    """
    Classe pour interagir avec l'API de Coinbase Pro.
    """

    name = "coinbase_pro"
    def __init__(self):
        self.BASE_REST_URL = "https://api.exchange.coinbase.com"
        self.KLINE_URL = "/products/{symbol}/candles"
        self.SYMBOL_URL = "/products"
        self.limit = 300  # Coinbase Pro limite à 300 chandelles par requête

        # Mapping des intervalles acceptés par Coinbase Pro
        self.valid_intervals = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "6h": 21600,
            "1d": 86400
        }
    
    def process_klines(self, klines):
        """
        Convertit les données
        """
        klines = klines[::-1]
        
        return [
            {
                "timestamp": kline[0] * 1000,
                "date": datetime.utcfromtimestamp(kline[0]).strftime('%Y-%m-%d %H:%M:%S'),
                "open": kline[3],
                "high": kline[2],
                "low": kline[1],
                "close": kline[4],
                "volume": ""
            }
            for kline in klines
        ]

    async def get_historical_klines(self, symbol, interval, start_time, end_time):
        """
        Récupère des chandelles historiques entre start_time et end_time.

        :param symbol: Symbole de trading (ex: 'BTC-USD').
        :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
        :param start_time: Timestamp Unix (ms) de début.
        :param end_time: Timestamp Unix (ms) de fin.
        :return: Liste des chandelles.
        """
        # Vérifier si l'intervalle est valide
        if interval not in self.valid_intervals:
            raise ValueError(f"Invalid interval '{interval}'. Valid intervals are: {', '.join(self.valid_intervals.keys())}")

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            endpoint = f"{self.BASE_REST_URL}{self.KLINE_URL.format(symbol=symbol)}"
            klines = []

            # Convertir les timestamps en secondes (Coinbase Pro utilise des timestamps en secondes)
            start_time = start_time // 1000
            end_time = end_time // 1000
            granularity = self.valid_intervals[interval]
            max_data_points = 300

            while start_time < end_time - granularity:
                
                # Calculer la fin de la plage de temps pour cette requête
                request_end_time = min(end_time, start_time + granularity * max_data_points)
                print(datetime.utcfromtimestamp(start_time).isoformat(), datetime.utcfromtimestamp(request_end_time).isoformat())

                params = {
                    "start": datetime.utcfromtimestamp(start_time).isoformat(),
                    "end": datetime.utcfromtimestamp(request_end_time).isoformat(),
                    "granularity": granularity
                }

                async with session.get(endpoint, params=params) as response:
                    data = await response.json()

                    if isinstance(data, list):
                        if not len(data):
                            break
                        klines.extend(data)

                        # Avance le start_time à la fin de la dernière chandelle récupérée
                        last_candle_time = int(data[1][0])
                        start_time = last_candle_time + granularity
                        await asyncio.sleep(0.1)  # Petite pause pour éviter les limitations d'API
                    else:
                        print(data, "Error, retrying...")
                        await asyncio.sleep(5)  # Pause plus longue en cas d'erreur

            return self.process_klines(klines)
        
    # async def get_historical_klines(self, symbol, interval, start_time, end_time):
    #     """
    #     Récupère des chandelles historiques entre start_time et end_time.

    #     :param symbol: Symbole de trading (ex: 'BTC-USD').
    #     :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
    #     :param start_time: Timestamp Unix (ms) de début.
    #     :param end_time: Timestamp Unix (ms) de fin.
    #     :return: Liste des chandelles.
    #     """
    #     # Vérifier si l'intervalle est valide
    #     if interval not in self.valid_intervals:
    #         raise ValueError(f"Invalid interval '{interval}'. Valid intervals are: {', '.join(self.valid_intervals.keys())}")

    #     async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
    #         endpoint = f"{self.BASE_REST_URL}{self.KLINE_URL.format(symbol=symbol)}"
    #         klines = []

    #         # Convertir les timestamps en secondes (Coinbase Pro utilise des timestamps en secondes)
    #         start_time = start_time // 1000
    #         end_time = end_time // 1000
    #         granularity = self.valid_intervals[interval]
    #         print(granularity)

    #         while start_time < end_time:
    #             params = {
    #                 "start": datetime.utcfromtimestamp(start_time).isoformat(),
    #                 "end": datetime.utcfromtimestamp(end_time).isoformat(),
    #                 "granularity": granularity
    #             }

    #             async with session.get(endpoint, params=params) as response:
    #                 data = await response.json()

    #                 if isinstance(data, list):
    #                     if not len(data):
    #                         break
    #                     klines.extend(data)

    #                     # Avance le start_time à la fin de la dernière chandelle récupérée
    #                     last_candle_time = int(data[-1][0])
    #                     start_time = last_candle_time + granularity
    #                     await asyncio.sleep(0.1)  # Petite pause pour éviter les limitations d'API
    #                 else:
    #                     print(data, "Error, retrying...")
    #                     await asyncio.sleep(5)  # Pause plus longue en cas d'erreur

    #         return klines
        
    def get_available_trading_pairs(self):
        """
        Récupère la liste des paires de trading disponibles sur Coinbase Pro.
        """
        response = requests.get(self.BASE_REST_URL + self.SYMBOL_URL)
        if response.status_code == 200:
            data = response.json()
            return [product['id'] for product in data]
        else:
            raise Exception(f"Coinbase Pro API error: {response.status_code} - {response.text}")
