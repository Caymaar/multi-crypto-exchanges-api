import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import json
import websocket  # pip install websocket-client


# Adresse de base de votre serveur
SERVER_URL = "http://localhost:8000"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Server Endpoints Tester")
        self.geometry("900x700")
        
        # On crée un Notebook (onglets) pour organiser les tests
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglets pour tester les différents endpoints
        self.login_frame = ttk.Frame(self.notebook)
        self.exchanges_frame = ttk.Frame(self.notebook)
        self.symbols_frame = ttk.Frame(self.notebook)
        self.klines_frame = ttk.Frame(self.notebook)
        self.twap_frame = ttk.Frame(self.notebook)
        self.orders_frame = ttk.Frame(self.notebook)
        self.ws_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.login_frame, text="Login/Register")
        self.notebook.add(self.exchanges_frame, text="Exchanges")
        self.notebook.add(self.symbols_frame, text="Symbols")
        self.notebook.add(self.klines_frame, text="Historical Data")
        self.notebook.add(self.twap_frame, text="Submit TWAP Order")
        self.notebook.add(self.orders_frame, text="Orders")
        self.notebook.add(self.ws_frame, text="WebSocket")
        
        # Créer les widgets pour chaque onglet
        self.create_login_widgets()
        self.create_exchanges_widgets()
        self.create_symbols_widgets()
        self.create_klines_widgets()
        self.create_twap_widgets()
        self.create_orders_widgets()
        self.create_ws_widgets()
        
        # Stocke le token (issu du login) pour les requêtes
        self.token = ""
    
    # ------------------ Login / Register ------------------ #
    def create_login_widgets(self):
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame, width=20)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, width=20, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        login_btn = ttk.Button(self.login_frame, text="Login", command=self.login)
        login_btn.grid(row=2, column=0, padx=5, pady=5)
        
        register_btn = ttk.Button(self.login_frame, text="Register", command=self.register)
        register_btn.grid(row=2, column=1, padx=5, pady=5)
        
        self.login_result = scrolledtext.ScrolledText(self.login_frame, width=80, height=10)
        self.login_result.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        url = SERVER_URL + "/login"
        data = {"username": username, "password": password}
        def task():
            try:
                resp = requests.post(url, json=data)
                result = resp.json()
                self.token = result.get("access_token", "")
                self.login_result.insert(tk.END, f"Login response: {result}\n")
            except Exception as e:
                self.login_result.insert(tk.END, f"Login error: {e}\n")
        threading.Thread(target=task).start()
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        url = SERVER_URL + "/register"
        data = {"username": username, "password": password}
        def task():
            try:
                resp = requests.post(url, json=data)
                result = resp.json()
                self.login_result.insert(tk.END, f"Register response: {result}\n")
            except Exception as e:
                self.login_result.insert(tk.END, f"Register error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ Get Exchanges ------------------ #
    def create_exchanges_widgets(self):
        btn = ttk.Button(self.exchanges_frame, text="Get Exchanges", command=self.get_exchanges)
        btn.pack(padx=5, pady=5)
        self.exchanges_result = scrolledtext.ScrolledText(self.exchanges_frame, width=80, height=10)
        self.exchanges_result.pack(padx=5, pady=5)
    
    def get_exchanges(self):
        url = SERVER_URL + "/exchanges"
        def task():
            try:
                resp = requests.get(url)
                result = resp.json()
                self.exchanges_result.insert(tk.END, f"Exchanges: {result}\n")
            except Exception as e:
                self.exchanges_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ Get Symbols ------------------ #
    def create_symbols_widgets(self):
        ttk.Label(self.symbols_frame, text="Exchange:").grid(row=0, column=0, padx=5, pady=5)
        self.symbols_exchange = ttk.Entry(self.symbols_frame, width=20)
        self.symbols_exchange.grid(row=0, column=1, padx=5, pady=5)
        btn = ttk.Button(self.symbols_frame, text="Get Symbols", command=self.get_symbols)
        btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.symbols_result = scrolledtext.ScrolledText(self.symbols_frame, width=80, height=10)
        self.symbols_result.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    
    def get_symbols(self):
        exch = self.symbols_exchange.get()
        url = SERVER_URL + f"/{exch}/symbols"
        def task():
            try:
                resp = requests.get(url)
                result = resp.json()
                self.symbols_result.insert(tk.END, f"Symbols for {exch}: {result}\n")
            except Exception as e:
                self.symbols_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ Get Historical Data (Klines) ------------------ #
    def create_klines_widgets(self):
        ttk.Label(self.klines_frame, text="Exchange:").grid(row=0, column=0, padx=5, pady=5)
        self.klines_exchange = ttk.Entry(self.klines_frame, width=20)
        self.klines_exchange.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.klines_frame, text="Symbol:").grid(row=1, column=0, padx=5, pady=5)
        self.klines_symbol = ttk.Entry(self.klines_frame, width=20)
        self.klines_symbol.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.klines_frame, text="Start Date:").grid(row=2, column=0, padx=5, pady=5)
        self.klines_start = ttk.Entry(self.klines_frame, width=20)
        self.klines_start.insert(0, "2025-01-01")
        self.klines_start.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.klines_frame, text="End Date:").grid(row=3, column=0, padx=5, pady=5)
        self.klines_end = ttk.Entry(self.klines_frame, width=20)
        self.klines_end.insert(0, "2025-02-01")
        self.klines_end.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.klines_frame, text="Interval:").grid(row=4, column=0, padx=5, pady=5)
        self.klines_interval = ttk.Entry(self.klines_frame, width=20)
        self.klines_interval.insert(0, "1d")
        self.klines_interval.grid(row=4, column=1, padx=5, pady=5)
        
        btn = ttk.Button(self.klines_frame, text="Get Kliness", command=self.get_klines)
        btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        self.klines_result = scrolledtext.ScrolledText(self.klines_frame, width=80, height=10)
        self.klines_result.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
    
    def get_klines(self):
        exch = self.klines_exchange.get()
        sym = self.klines_symbol.get()
        start = self.klines_start.get()
        end = self.klines_end.get()
        interval = self.klines_interval.get()
        url = SERVER_URL + f"/klines/{exch}/{sym}?start_date={start}&end_date={end}&interval={interval}"
        def task():
            try:
                resp = requests.get(url)
                result = resp.json()
                self.klines_result.insert(tk.END, f"Klines: {json.dumps(result, indent=2)}\n")
            except Exception as e:
                self.klines_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ Submit TWAP Order ------------------ #
    def create_twap_widgets(self):
        ttk.Label(self.twap_frame, text="Order ID:").grid(row=0, column=0, padx=5, pady=5)
        self.twap_order_id = ttk.Entry(self.twap_frame, width=20)
        self.twap_order_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Symbol:").grid(row=1, column=0, padx=5, pady=5)
        self.twap_symbol = ttk.Entry(self.twap_frame, width=20)
        self.twap_symbol.insert(0, "ETH-USD")
        self.twap_symbol.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Side (buy/sell):").grid(row=2, column=0, padx=5, pady=5)
        self.twap_side = ttk.Entry(self.twap_frame, width=20)
        self.twap_side.insert(0, "buy")
        self.twap_side.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Total Quantity:").grid(row=3, column=0, padx=5, pady=5)
        self.twap_qty = ttk.Entry(self.twap_frame, width=20)
        self.twap_qty.insert(0, "10")
        self.twap_qty.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Limit Price:").grid(row=4, column=0, padx=5, pady=5)
        self.twap_limit = ttk.Entry(self.twap_frame, width=20)
        self.twap_limit.insert(0, "2750")
        self.twap_limit.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Duration (sec):").grid(row=5, column=0, padx=5, pady=5)
        self.twap_duration = ttk.Entry(self.twap_frame, width=20)
        self.twap_duration.insert(0, "60")
        self.twap_duration.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(self.twap_frame, text="Interval (if applicable):").grid(row=6, column=0, padx=5, pady=5)
        self.twap_interval = ttk.Entry(self.twap_frame, width=20)
        self.twap_interval.insert(0, "1d")
        self.twap_interval.grid(row=6, column=1, padx=5, pady=5)
        
        btn = ttk.Button(self.twap_frame, text="Submit TWAP Order", command=self.submit_twap)
        btn.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        self.twap_result = scrolledtext.ScrolledText(self.twap_frame, width=80, height=10)
        self.twap_result.grid(row=8, column=0, columnspan=2, padx=5, pady=5)
    
    def submit_twap(self):
        order_id = self.twap_order_id.get()
        symbol = self.twap_symbol.get()
        side = self.twap_side.get()
        total_qty = self.twap_qty.get()
        limit_price = self.twap_limit.get()
        duration = self.twap_duration.get()
        interval = self.twap_interval.get()
        url = SERVER_URL + "/orders/twap"
        data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "total_quantity": float(total_qty),
            "limit_price": float(limit_price),
            "duration": int(duration),
            "interval": interval
        }
        def task():
            try:
                resp = requests.post(url, json=data)
                result = resp.json()
                self.twap_result.insert(tk.END, f"TWAP order response: {result}\n")
            except Exception as e:
                self.twap_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ Orders ------------------ #
    def create_orders_widgets(self):
        ttk.Label(self.orders_frame, text="Order ID (optional):").grid(row=0, column=0, padx=5, pady=5)
        self.orders_order_id = ttk.Entry(self.orders_frame, width=20)
        self.orders_order_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.orders_frame, text="Order Status (optional):").grid(row=1, column=0, padx=5, pady=5)
        self.orders_status = ttk.Entry(self.orders_frame, width=20)
        self.orders_status.grid(row=1, column=1, padx=5, pady=5)
        
        list_btn = ttk.Button(self.orders_frame, text="List Orders", command=self.list_orders)
        list_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        self.orders_result = scrolledtext.ScrolledText(self.orders_frame, width=80, height=10)
        self.orders_result.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Label(self.orders_frame, text="Order ID for details:").grid(row=4, column=0, padx=5, pady=5)
        self.orders_detail_id = ttk.Entry(self.orders_frame, width=20)
        self.orders_detail_id.grid(row=4, column=1, padx=5, pady=5)
        
        detail_btn = ttk.Button(self.orders_frame, text="Get Order Detail", command=self.get_order_detail)
        detail_btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        self.order_detail_result = scrolledtext.ScrolledText(self.orders_frame, width=80, height=10)
        self.order_detail_result.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
    
    def list_orders(self):
        order_id = self.orders_order_id.get()
        status = self.orders_status.get()
        url = SERVER_URL + "/orders"
        params = {}
        if order_id:
            params["order_id"] = order_id
        if status:
            params["order_status"] = status
        def task():
            try:
                resp = requests.get(url, params=params)
                result = resp.json()
                self.orders_result.insert(tk.END, f"Orders: {json.dumps(result, indent=2)}\n")
            except Exception as e:
                self.orders_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    def get_order_detail(self):
        order_id = self.orders_detail_id.get()
        url = SERVER_URL + f"/orders/{order_id}"
        def task():
            try:
                resp = requests.get(url)
                result = resp.json()
                self.order_detail_result.insert(tk.END, f"Order Detail: {json.dumps(result, indent=2)}\n")
            except Exception as e:
                self.order_detail_result.insert(tk.END, f"Error: {e}\n")
        threading.Thread(target=task).start()
    
    # ------------------ WebSocket ------------------ #
    def create_ws_widgets(self):
        ttk.Label(self.ws_frame, text="WebSocket URL:").grid(row=0, column=0, padx=5, pady=5)
        self.ws_url_entry = ttk.Entry(self.ws_frame, width=50)
        self.ws_url_entry.insert(0, "ws://localhost:8000/ws?token=VOTRE_TOKEN")
        self.ws_url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ws_connect_btn = ttk.Button(self.ws_frame, text="Connect WebSocket", command=self.connect_ws)
        ws_connect_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        self.ws_result = scrolledtext.ScrolledText(self.ws_frame, width=80, height=15)
        self.ws_result.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    
    def connect_ws(self):
        ws_url = self.ws_url_entry.get()
        def run_ws():
            def on_message(ws, message):
                self.ws_result.insert(tk.END, f"Message: {message}\n")
            def on_error(ws, error):
                self.ws_result.insert(tk.END, f"Error: {error}\n")
            def on_close(ws, close_status_code, close_msg):
                self.ws_result.insert(tk.END, "WebSocket closed\n")
            def on_open(ws):
                self.ws_result.insert(tk.END, "WebSocket connected\n")
                # Exemple: envoyer une subscription pour Kraken/ BTC-USD
                sub_message = {"action": "subscribe", "exchange": "kraken", "symbol": "BTC-USD"}
                ws.send(json.dumps(sub_message))
            ws_app = websocket.WebSocketApp(ws_url,
                                            on_message=on_message,
                                            on_error=on_error,
                                            on_close=on_close)
            ws_app.on_open = on_open
            ws_app.run_forever()
        threading.Thread(target=run_ws).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()