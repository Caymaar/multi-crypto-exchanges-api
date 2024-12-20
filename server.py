from fastapi import FastAPI, Query
import asyncio
from Exchange import Binance, CoinbasePro, OKX
from datetime import datetime, timedelta

class Requester:

    def __init__(self):
        self.exchange = {
            "binance": Binance(),
            "okx": OKX(),
            "coinbasepro": CoinbasePro(),
        }

    def get_available_trading_pairs(self, exchange):
        return self.exchange[exchange].get_available_trading_pairs()
        
    async def get_historical_klines(self, exchange, symbol, interval, start_time, end_time):
        return await self.exchange[exchange].get_historical_klines(symbol, interval, start_time, end_time)

# Initialize FastAPI app
app = FastAPI()
requester = Requester()

# Route for the root endpoint "/"
@app.get("/")
def read_root():
    return {"message": "Welcome to the Simple Multi Exchange API"}

# Route that returns all available stock symbols
@app.get("/{exchange}/symbols")
def get_symbols(exchange):
    
    pairs = requester.get_available_trading_pairs(exchange)
    return {"symbols": pairs}


# ...existing code...

import re
from fastapi import HTTPException

@app.get("/{exchange}/{symbol}")
async def get_klines(
    exchange: str,
    symbol: str,
    start_date: str = Query(None, description="Start date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
    end_date: str = Query(None, description="End date in format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"),
    interval: str = Query("1d", description="Candle interval, e.g., 1m, 5m, 1h")
):
    """
    Récupère les chandelles pour une paire de trading sur un échange spécifique.

    :param exchange: Nom de l'échange (ex: binance, kraken).
    :param symbol: Symbole de trading (ex: BTCUSDT).
    :param start_date: Date de début au format YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS.
    :param end_date: Date de fin au format YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS.
    :param interval: Intervalle des chandelles (par défaut: 1m).
    :return: Chandelles récupérées pour la paire.
    """
    def parse_date(date_str):
        """
        Tente de parser une date dans différents formats.
        
        :param date_str: Chaîne de la date.
        :return: Timestamp Unix (ms).
        """
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
            except ValueError:
                pass
        raise ValueError(f"Invalid date format: {date_str}. Supported formats are YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")

    # Valider le symbole
    if not re.match(r'^[A-Z0-9-_.]{1,20}$', symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format. Legal range is '^[A-Z0-9-_.]{1,20}$'.")

    try:
        # Convertir les dates en timestamp
        if start_date:
            start_timestamp = parse_date(start_date)
        else:
            start_date = datetime.now() - timedelta(days=5)
            start_timestamp = int(start_date.timestamp() * 1000)  # Valeur par défaut

        if end_date:
            end_timestamp = parse_date(end_date)
        else:
            end_date
            end_timestamp = int(datetime.now().timestamp() * 1000)  # Valeur par défaut

        # Appeler la fonction pour récupérer les chandelles
        klines = await requester.get_historical_klines(exchange, symbol, interval, start_timestamp, end_timestamp)
        return {"klines": klines}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    

@app.get("/test")
async def do_test():
    req = Requester()

    start_date = int(datetime(2024, 1, 1).timestamp() * 1000)
    end_date = int(datetime(2024, 1, 10).timestamp() * 1000)
    try:
        # Utilisez await pour appeler la méthode asynchrone
        klines = await req.get_historical_klines("binance", "BTCUSDT", "1m", start_date, end_date)
    except Exception as e:
        return {"error": str(e)}
    return {"symbol": "BTC", "klines": klines}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)