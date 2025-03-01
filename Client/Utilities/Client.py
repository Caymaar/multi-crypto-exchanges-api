import requests

class Client:
    def __init__(self, server_url):
        self.server_url = server_url
        self.token = ""

    def login(self, username, password):
        url = f"{self.server_url}/login"
        data = {"username": username, "password": password}
        resp = requests.post(url, json=data)
        result = resp.json()
        self.token = result.get("access_token", "")
        return result

    def register(self, username, password):
        url = f"{self.server_url}/register"
        data = {"username": username, "password": password}
        resp = requests.post(url, json=data)
        return resp.json()

    def get_exchanges(self):
        url = f"{self.server_url}/exchanges"
        resp = requests.get(url)
        return resp.json()

    def get_symbols(self, exchange):
        url = f"{self.server_url}/{exchange}/symbols"
        resp = requests.get(url)
        return resp.json()

    def get_klines(self, exchange, symbol, start_date, end_date, interval):
        url = (f"{self.server_url}/klines/{exchange}/{symbol}"
               f"?start_date={start_date}&end_date={end_date}&interval={interval}")
        resp = requests.get(url)
        return resp.json()

    def submit_twap_order(self, order_id, symbol, side, total_quantity, limit_price, duration, interval):
        url = f"{self.server_url}/orders/twap"
        data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "total_quantity": total_quantity,
            "limit_price": limit_price,
            "duration": duration,
            "interval": interval
        }
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = requests.post(url, json=data, headers=headers)
        return resp.json()

    def list_orders(self, order_id_filter=None, order_status_filter=None):
        url = f"{self.server_url}/orders"
        params = {}
        if order_id_filter:
            params["order_id"] = order_id_filter
        if order_status_filter:
            params["order_status"] = order_status_filter
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = requests.get(url, params=params, headers=headers)
        return resp.json()

    def get_order_detail(self, order_id):
        url = f"{self.server_url}/orders/{order_id}"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = requests.get(url, headers=headers)
        return resp.json()