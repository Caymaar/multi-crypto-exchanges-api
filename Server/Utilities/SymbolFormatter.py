class SymbolFormatter:
    # On définit ici les quotes courantes qui, lorsqu’on les reçoit, seront ramenées à "USD"
    standard_quotes = {"USDT", "USDC", "BUSD", "USD"}

    @staticmethod
    def parse_symbol(symbol: str) -> tuple[str, str]:
        """
        Extrait la partie "base" et "quote" d'un symbole.
        On essaie de détecter un séparateur ( '-' ou '/' ).
        Si aucun séparateur n'est trouvé, on tente de déterminer la quote en vérifiant si
        le symbole se termine par l'une des quotes connues.
        """
        symbol = symbol.strip()
        if '-' in symbol:
            parts = symbol.split('-')
            return parts[0].upper(), parts[1].upper()
        elif '/' in symbol:
            parts = symbol.split('/')
            return parts[0].upper(), parts[1].upper()
        else:
            symbol_upper = symbol.upper()
            # On cherche si le symbole se termine par l'une des quotes connues.
            for quote in SymbolFormatter.standard_quotes:
                if symbol_upper.endswith(quote):
                    base = symbol_upper[:-len(quote)]
                    return base, quote
            # Sinon, on effectue une division approximative.
            mid = len(symbol) // 2
            return symbol_upper[:mid], symbol_upper[mid:]

    @staticmethod
    def to_standard(symbol: str) -> str:
        """
        Convertit un symbole (peu importe son format d'origine) en format standard "BASE-QUOTE".
        Si la partie quote est "USDT", "USDC" ou "BUSD", on la transforme en "USD".
        Exemples :
          "BTC/USD"  -> "BTC-USD"
          "BTCUSDT"  -> "BTC-USD"
          "btc-usd"  -> "BTC-USD"
        """
        base, quote = SymbolFormatter.parse_symbol(symbol)
        if quote in {"USDT", "USDC", "BUSD"}:
            quote = "USD"
        return f"{base}-{quote}"

    @staticmethod
    def from_standard(standard_symbol: str, exchange: str) -> str:
        """
        Convertit un symbole standard ("BASE-QUOTE") en symbole spécifique à l'exchange.
        
        Pour chaque exchange, on applique la règle suivante :
          • Binance : symbole sans séparateur et si quote est "USD" alors on utilise "USDT"
          • OKX     : symbole avec un tiret, et pour "USD" on utilise "USDT"
          • Kraken  : symbole avec une barre oblique "/"
        
        Exemple :
          from_standard("BTC-USD", "binance") -> "BTCUSDT"
          from_standard("BTC-USD", "okx")     -> "BTC-USDT"
          from_standard("BTC-USD", "kraken")  -> "BTC/USD"
        """
        base, quote = standard_symbol.split('-')
        exchange = exchange.lower()
        if exchange == "binance":
            if quote == "USD":
                quote = "USDT"
            return f"{base}{quote}"
        elif exchange == "okx":
            if quote == "USD":
                quote = "USDT"
            return f"{base}-{quote}"
        elif exchange == "kraken":
            return f"{base}/{quote}"
        else:
            return standard_symbol

    @staticmethod
    def to_exchange(symbol: str, exchange: str) -> str:
        """
        Prend en entrée un symbole dans n'importe quel format et le convertit en symbole
        spécifique à l'exchange en question.
        """
        standard = SymbolFormatter.to_standard(symbol)
        return SymbolFormatter.from_standard(standard, exchange)


class AdvancedSymbolFormatter(SymbolFormatter):
    def __init__(self, exchange_pairs: dict[str, list[str]]):
        """
        Initialise le formatter avancé en chargeant, pour chaque exchange, la liste des trading pairs
        disponibles (dans leur format natif) et en calculant l'ensemble des bases connues.

        :param exchange_pairs: dictionnaire avec comme clés les noms d'exchange (par ex. "binance", "okx", "kraken")
                               et comme valeurs la liste des trading pairs disponibles sur cet exchange.
        """
        self.exchange_pairs = {}  # mapping exchange -> set de symboles en format standard (ex: "BTC-USD")
        self.base_symbols = {}    # mapping exchange -> set des bases (ex: "BTC", "ETH", ...)
        for exchange, pairs in exchange_pairs.items():
            exchange_lower = exchange.lower()
            standard_pairs = set()
            for pair in pairs:
                try:
                    standard_pair = self.to_standard(pair)
                    standard_pairs.add(standard_pair)
                except Exception as e:
                    print(f"Error processing pair '{pair}' for exchange '{exchange}': {e}")
            self.exchange_pairs[exchange_lower] = standard_pairs
            # Extraire la base pour chaque pair standard (si le format "BASE-QUOTE" est respecté)
            bases = {pair.split('-')[0] for pair in standard_pairs if '-' in pair}
            self.base_symbols[exchange_lower] = bases

    def is_valid(self, symbol: str, exchange: str) -> bool:
        """
        Vérifie si le symbole, converti en format standard, figure dans la liste des trading pairs
        disponibles pour l'exchange donné.
        """
        exchange_lower = exchange.lower()
        standard_symbol = self.to_standard(symbol)
        return standard_symbol in self.exchange_pairs.get(exchange_lower, set())

    def format_input(self, symbol: str, exchange: str) -> str:
        """
        Convertit l'input de l'utilisateur (peu importe son format) en symbole de trading
        formaté pour l'exchange, en se basant sur la liste préchargée.
        
        Si la conversion standard donne un symbole présent dans la liste des trading pairs,
        on retourne sa version spécifique à l'exchange.
        Sinon, on tente d'identifier heuristiquement la base en se basant sur les bases connues.
        En dernier recours, on retourne la conversion standard.
        """
        exchange_lower = exchange.lower()
        standard_symbol = self.to_standard(symbol)
        if standard_symbol in self.exchange_pairs.get(exchange_lower, set()):
            return self.from_standard(standard_symbol, exchange_lower)
        # Tentative heuristique : si l'input commence par une base connue
        for base in self.base_symbols.get(exchange_lower, set()):
            if symbol.upper().startswith(base):
                quote_candidate = symbol.upper()[len(base):]
                if quote_candidate in self.standard_quotes:
                    candidate_standard = f"{base}-{quote_candidate}"
                    if candidate_standard in self.exchange_pairs[exchange_lower]:
                        return self.from_standard(candidate_standard, exchange_lower)
        # En dernier recours, retourne la conversion standard
        return self.from_standard(standard_symbol, exchange_lower)


# Exemple d'utilisation
if __name__ == "__main__":
    # Simulons des listes de trading pairs pour chaque exchange (exemples simplifiés)
    binance_pairs = ["BTCUSDT", "ETHUSDT", "LTCBTC", "XRPUSDT"]
    okx_pairs = ["BTC-USDT", "ETH-USDT", "LTC-BTC", "XRP-USDT"]
    kraken_pairs = ["BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD"]

    exchange_pairs = {
        "binance": binance_pairs,
        "okx": okx_pairs,
        "kraken": kraken_pairs
    }

    advanced_formatter = AdvancedSymbolFormatter(exchange_pairs)

    # Quelques tests
    test_inputs = [
        ("BTC/USD", "binance"),
        ("btc-usd", "okx"),
        ("BTCUSDT", "kraken"),
        ("ETHUSD", "kraken"),  # input sans séparateur explicite
        ("XRP/USDT", "binance")
    ]
    print("Conversion avancée avec validation sur les trading pairs chargés:")
    for inp, exch in test_inputs:
        formatted = advanced_formatter.format_input(inp, exch)
        print(f"  Input: {inp} pour {exch} -> {formatted}")