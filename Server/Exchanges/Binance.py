from Exchanges.Abstract import Exchange
import requests
import asyncio
import aiohttp
from datetime import datetime

class Binance(Exchange):

    name = "binance"
    
    def __init__(self):

        self.BASE_REST_SPOT_URL = "https://api.binance.com"
        self.KLINE_URL = "/api/v3/klines"
        self.SYMBOLE_URL = "/api/v3/exchangeInfo"
        self.limit = 1000
        self.ws_url = "wss://stream.binance.com:9443/ws"

        self.valid_intervals = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "2h": 7200,
            "4h": 14400,
            "6h": 21600,
            "8h": 28800,
            "12h": 43200,
            "1d": 86400,
            "3d": 259200,
            "1w": 604800,
            "1M": 2592000
        }

    def process_klines(self, klines):
        """
        Convertit les données
        """
        return [
            {
                "timestamp": int(kline[0]),
                "date": datetime.utcfromtimestamp(int(kline[0]) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),

            }
            for kline in klines
        ]

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

            return self.process_klines(klines)
    
    def get_available_trading_pairs(self):
        base_url = self.BASE_REST_SPOT_URL + self.SYMBOLE_URL
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.json()
            return [symbol_info['symbol'] for symbol_info in data['symbols']]
        else:
            raise Exception(f"Binance API error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    import pandas as pd
    from datetime import datetime
    def parse_date(date_str: str) -> int:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
            except ValueError:
                pass
        raise ValueError(f"Invalid date format: {date_str}. Supported formats are YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")


    start_date = "2021-01-01"
    end_date = "2021-12-31"

    if start_date:
        start_time = parse_date(start_date)
    else:
        start_time = pd.to_datetime("2021-01-01").timestamp() * 1000

    if end_date:
        end_time = parse_date(end_date)
    else:
        end_time = pd.to_datetime("today").timestamp() * 1000

    print(Binance().get_historical_klines("ETHBTC", "1d", start_time, end_time))