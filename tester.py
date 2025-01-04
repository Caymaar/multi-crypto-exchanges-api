from abc import ABC, abstractmethod
import requests
import time
import asyncio
import json
import websockets
import aiohttp
from datetime import datetime, timedelta
import pandas as pd

BASE_REST_SPOT_URL = "https://api.binance.com"


class Exchange(ABC):
    """
    Interface pour les échanges.
    """

    @abstractmethod
    def get_candles(self, symbol, interval, limit=500, start_date=None, end_date=None):
        pass

    @abstractmethod
    def get_available_trading_pairs(self):
        pass


class Binance(Exchange):
    """
    Classe pour interagir avec l'API de Binance.
    """

    def get_candles(self, symbol, interval, limit=1000, start_date=None, end_date=None):
        """
        Récupère des données de chandelles depuis Binance, paginées si nécessaire.

        :param symbol: Le symbole de trading (ex: 'BTCUSDT').
        :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
        :param limit: Nombre maximum de chandelles par requête (par défaut: 1000).
        :param start_date: Timestamp de début (ms).
        :param end_date: Timestamp de fin (ms).
        :return: Liste complète des chandelles entre les deux dates.
        """
        base_url = "https://api.binance.com/api/v3/klines"
        all_candles = []
        current_start_time = start_date

        while current_start_time < end_date:
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": current_start_time,
                "endTime": end_date,
            }
            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                candles = response.json()
                if not candles:
                    break  # Aucun résultat, fin des données
                all_candles.extend(candles)

                # Avancer le `startTime` pour la prochaine requête
                current_start_time = candles[-1][0] + 1
            else:
                raise Exception(f"Binance API error: {response.status_code} - {response.text}")

        return all_candles

    async def get_historical_klines(self, symbol, interval, start_time, end_time, perpetual=False):
        """
        Récupère des chandelles historiques entre start_time et end_time.

        :param symbol: Symbole de trading (ex: 'BTCUSDT').
        :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
        :param start_time: Timestamp Unix (ms) de début.
        :param end_time: Timestamp Unix (ms) de fin.
        :param perpetual: Booléen indiquant si on utilise les données futures perpétuelles (par défaut: False).
        :return: DataFrame des chandelles.
        """
        async with aiohttp.ClientSession() as session:
            endpoint = f"{BASE_REST_SPOT_URL}/api/v3/klines" if not perpetual else f"{BASE_REST_SPOT_URL}/fapi/v1/klines"
            klines = []
            while start_time < end_time:
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time,
                    "limit": 1000  # Maximum autorisé par l'API Binance
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

            # Convertir les données en DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.drop_duplicates()
            return df

    def get_available_trading_pairs(self):
        base_url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.json()
            return [symbol_info['symbol'] for symbol_info in data['symbols']]
        else:
            raise Exception(f"Binance API error: {response.status_code} - {response.text}")


class Requester:

    def __init__(self):
        self.exchange = {
            "binance": Binance()
        }

    def get_candles(self, exchange, symbol, interval, limit=500, start_date=None, end_date=None):
        return self.exchange[exchange].get_candles(symbol, interval, limit, start_date, end_date)

    def get_available_trading_pairs(self, exchange):
        return self.exchange[exchange].get_available_trading_pairs()

    async def get_historical_klines(self, exchange, symbol, interval, start_time, end_time, perpetual=False):
        return await self.exchange[exchange].get_historical_klines(symbol, interval, start_time, end_time, perpetual)


# Exemple d'utilisation
if __name__ == "__main__":
    req = Requester()

    # Définir les paramètres
    symbol = "BTCUSDT"
    interval = "1m"
    start_date = int(datetime(2024, 1, 1).timestamp() * 1000)
    end_date = int(datetime(2024, 1, 10).timestamp() * 1000)

    # Récupération des chandelles
    # candles = req.get_candles("binance", symbol, interval, start_date=start_date, end_date=end_date)
    klines = req.get_historical_klines("binance", symbol, interval, start_date, end_date)
    print(f"Nombre total de chandelles récupérées : {len(candles)}")
