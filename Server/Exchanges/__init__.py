from Server.Exchanges.Binance import Binance, binance_order_books
from Server.Exchanges.OKX import OKX
from Server.Exchanges.CoinbasePro import CoinbasePro
from Server.Exchanges.Kraken import Kraken

__all__ = ["Binance", "OKX", "CoinbasePro", "Kraken", "binance_order_books"]

exchange_dict = {
    "binance": Binance(),
    "okx": OKX(),
    "coinbase_pro": CoinbasePro(),
    "kraken": Kraken()
}