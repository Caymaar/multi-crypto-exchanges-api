import requests
import time

def get_candles(symbol, interval, limit=500, start_date=None, end_date=None):
    """
    Récupère des données de chandelles depuis Binance.
    
    :param symbol: Le symbole de trading (ex: 'BTCUSDT').
    :param interval: Intervalle des chandelles (ex: '1m', '5m', '1h', '1d').
    :param limit: Nombre maximum de chandelles à récupérer (par défaut: 500).
    :param start_date: Date de début au format timestamp (ms).
    :param end_date: Date de fin au format timestamp (ms).
    :return: Liste de chandelles.
    """
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_date,
        "endTime": end_date,
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erreur lors de la requête : {response.status_code} - {response.text}")


def get_available_trading_pairs():
    """
    Récupère la liste des paires de trading disponibles sur Binance.
    
    :return: Liste des symboles de trading.
    """
    base_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(base_url)
    
    if response.status_code == 200:
        data = response.json()
        return [symbol_info['symbol'] for symbol_info in data['symbols']]
    else:
        raise Exception(f"Erreur lors de la requête : {response.status_code} - {response.text}")


# Exemple d'utilisation
# Obtenir les paires de trading disponibles
trading_pairs = get_available_trading_pairs()
print(f"Nombre de paires disponibles : {len(trading_pairs)}")
print("Quelques exemples :", trading_pairs[:10])

# Définir les paramètres pour récupérer les chandelles
symbol = "BTCUSDT"
interval = "1h"
limit = 100
start_date = int(time.mktime(time.strptime("2024-01-01", "%Y-%m-%d"))) * 1000
end_date = int(time.mktime(time.strptime("2024-12-01", "%Y-%m-%d"))) * 1000

# Obtenir les données de chandelles
try:
    candles = get_binance_candles(symbol, interval, limit, start_date, end_date)
    print(f"Chandelles récupérées pour {symbol} ({len(candles)} entrées).")
    for candle in candles[:5]:  # Affiche les 5 premières chandelles
        print(candle)
except Exception as e:
    print(f"Erreur : {e}")