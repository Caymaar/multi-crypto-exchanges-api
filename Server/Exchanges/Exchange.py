from abc import ABC, abstractmethod
import requests
import asyncio
import aiohttp
from datetime import datetime

class Exchange(ABC):
    @abstractmethod
    async def get_historical_klines(self, symbol, interval, start_date=None, end_date=None):
        pass

    @abstractmethod
    def get_available_trading_pairs(self):
        pass


class Binance(Exchange):

    name = "binance"
    def __init__(self):

        self.BASE_REST_SPOT_URL = "https://api.binance.com"
        self.KLINE_URL = "/api/v3/klines"
        self.SYMBOLE_URL = "/api/v3/exchangeInfo"
        self.limit = 1000
        self.ws_url = "wss://stream.binance.com:9443/ws"

    async def get_historical_klines(self, symbol, interval, start_time, end_time):
        """
        Récupère des chandelles historiques entre start_time et end_time.

        :param symbol: Symbole de trading (ex: 'BTCUSDT').
        :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
        :param start_time: Timestamp Unix (ms) de début.
        :param end_time: Timestamp Unix (ms) de fin.
        :param perpetual: Booléen indiquant si on utilise les données futures perpétuelles (par défaut: False).
        :return: DataFrame des chandelles.
        """
        if "-" in symbol:
            symbol = symbol.replace("-", "")

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            endpoint = f"{self.BASE_REST_SPOT_URL}{self.KLINE_URL}"
            klines = []
            while start_time < end_time:
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time,
                    "limit": self.limit
                }
                async with session.get(endpoint, params=params) as response:
                    data = await response.json()
                    if isinstance(data, list):
                        if not len(data):
                            break
                        klines.extend(data)

                        # Avance le start_time à la fin de la dernière chandelle récupérée
                        start_time = data[-1][0] + 1
                        await asyncio.sleep(0.1)  # Petite pause pour éviter les limitations d'API
                    else:
                        print(data, "Error, retrying...")
                        await asyncio.sleep(5)  # Pause plus longue en cas d'erreur

            return klines
    
    def get_available_trading_pairs(self):
        base_url = self.BASE_REST_SPOT_URL + self.SYMBOLE_URL
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.json()
            return [symbol_info['symbol'] for symbol_info in data['symbols']]
        else:
            raise Exception(f"Binance API error: {response.status_code} - {response.text}")


class OKX(Exchange):
    """
    Classe pour interagir avec l'API de OKX.
    """
    name = "okx"
    def __init__(self):
        self.BASE_REST_URL = "https://www.okx.com"
        self.KLINE_URL = "/api/v5/market/candles"
        self.SYMBOLE_URL = "/api/v5/public/instruments"
        self.limit = 100  # OKX limite à 100 chandelles par requête

    async def get_historical_klines(self, symbol, interval, start_time, end_time):
        """
        Récupère des chandelles historiques entre start_time et end_time.

        :param symbol: Symbole de trading (ex: 'BTC-USDT').
        :param interval: Intervalle des chandelles (ex: '1m', '5m', '1H', '1D').
        :param start_time: Timestamp Unix (ms) de début.
        :param end_time: Timestamp Unix (ms) de fin.
        :return: Liste des chandelles.
        """


        # upper the interval to match OKX API
        if "m" not in interval:
            interval = interval.upper()

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            endpoint = f"{self.BASE_REST_URL}{self.KLINE_URL}"
            klines = []
            while start_time < end_time:
                params = {
                    "instId": symbol,  # Instrument ID
                    "bar": interval,   # Intervalle
                    "after": start_time,  # Temps de début
                    "limit": self.limit  # Maximum par requête
                }
                async with session.get(endpoint, params=params) as response:
                    data = await response.json()

                    print(data)
                    if "data" in data:
                        if not len(data["data"]):
                            break
                        klines.extend(data["data"])

                        # Avance le start_time à la fin de la dernière chandelle récupérée
                        last_candle_time = int(data["data"][-1][0])  # Timestamp de la dernière chandelle
                        start_time = last_candle_time + 1
                        await asyncio.sleep(0.1)  # Petite pause pour éviter les limitations d'API
                    else:
                        print(data, "Error, retrying...")
                        await asyncio.sleep(5)  # Pause plus longue en cas d'erreur

            return klines

    def get_available_trading_pairs(self):
        """
        Récupère la liste des paires de trading disponibles sur OKX.
        """
        base_url = f"{self.BASE_REST_URL}{self.SYMBOLE_URL}"
        params = {"instType": "SPOT"}  # Exemple pour récupérer uniquement les instruments Spot
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return [instrument["instId"] for instrument in data["data"]]
            else:
                raise Exception("OKX API error: No data found in response.")
        else:
            raise Exception(f"OKX API error: {response.status_code} - {response.text}")

    
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
            print(granularity)

            while start_time < end_time:
                params = {
                    "start": datetime.utcfromtimestamp(start_time).isoformat(),
                    "end": datetime.utcfromtimestamp(end_time).isoformat(),
                    "granularity": granularity
                }

                async with session.get(endpoint, params=params) as response:
                    data = await response.json()

                    if isinstance(data, list):
                        if not len(data):
                            break
                        klines.extend(data)

                        # Avance le start_time à la fin de la dernière chandelle récupérée
                        last_candle_time = int(data[-1][0])
                        start_time = last_candle_time + granularity
                        await asyncio.sleep(0.1)  # Petite pause pour éviter les limitations d'API
                    else:
                        print(data, "Error, retrying...")
                        await asyncio.sleep(5)  # Pause plus longue en cas d'erreur

            return klines
        
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
