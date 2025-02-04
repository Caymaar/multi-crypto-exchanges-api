from Exchanges.Binance import Binance
from Exchanges.OKX import OKX
from Exchanges.CoinbasePro import CoinbasePro

__all__ = ["Binance", "OKX", "CoinbasePro"]

exchange_dict = {
    "binance": Binance(),
    "okx": OKX(),
    "coinbase_pro": CoinbasePro()
}