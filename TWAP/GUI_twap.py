import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import json
import requests  # To make HTTP requests to the backend
from datetime import datetime, timedelta
import uuid


class OrderBookGUI:
    """
    A graphical interface for interacting with order books and generating API keys.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Order Book GUI")

        # FastAPI server URL
        self.api_url = "http://127.0.0.1:8005"  # Update with your actual FastAPI server URL

        # Initialize API key variable
        self.api_key = ""

        # Create the main interface
        self.create_widgets()

    def create_widgets(self):
        """Create and arrange all GUI elements"""

        # Get Symbols frame
        symbols_frame = ttk.LabelFrame(self.root, text="Get Available Symbols", padding="5")
        symbols_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(symbols_frame, text="Exchange:").pack(side="left", padx=5)
        self.symbols_exchange_var = tk.StringVar()
        self.symbols_exchange_entry = ttk.Entry(symbols_frame, textvariable=self.symbols_exchange_var, width=20)
        self.symbols_exchange_entry.pack(side="left", padx=5)

        ttk.Button(symbols_frame, text="Get Symbols", command=self.get_symbols).pack(side="left", padx=5)

        self.symbols_result_text = scrolledtext.ScrolledText(symbols_frame, height=5, width=60)
        self.symbols_result_text.pack(fill="both", expand=True)

        # Klines fetch frame
        klines_frame = ttk.LabelFrame(self.root, text="Klines Fetch", padding="5")
        klines_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(klines_frame, text="Exchange:").pack(side="left", padx=5)
        self.exchange_var = tk.StringVar()
        self.exchange_entry = ttk.Entry(klines_frame, textvariable=self.exchange_var, width=20)
        self.exchange_entry.pack(side="left", padx=5)

        ttk.Label(klines_frame, text="Symbol:").pack(side="left", padx=5)
        self.symbol_var = tk.StringVar()
        self.symbol_entry = ttk.Entry(klines_frame, textvariable=self.symbol_var, width=20)
        self.symbol_entry.pack(side="left", padx=5)

        ttk.Label(klines_frame, text="Start Date (YYYY-MM-DD):").pack(side="left", padx=5)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(klines_frame, textvariable=self.start_date_var, width=20)
        self.start_date_entry.pack(side="left", padx=5)

        ttk.Label(klines_frame, text="End Date (YYYY-MM-DD):").pack(side="left", padx=5)
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(klines_frame, textvariable=self.end_date_var, width=20)
        self.end_date_entry.pack(side="left", padx=5)

        ttk.Label(klines_frame, text="Interval:").pack(side="left", padx=5)
        self.interval_var = tk.StringVar()
        self.interval_entry = ttk.Entry(klines_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.insert(0, "1d")  # Default value
        self.interval_entry.pack(side="left", padx=5)

        ttk.Label(klines_frame, text="Limit:").pack(side="left", padx=5)
        self.limit_var = tk.IntVar()
        self.limit_entry = ttk.Entry(klines_frame, textvariable=self.limit_var, width=10)
        self.limit_entry.insert(0, "100")  # Default value
        self.limit_entry.pack(side="left", padx=5)

        ttk.Button(klines_frame, text="Fetch Klines", command=self.fetch_klines).pack(side="left", padx=5)

        # API Key generation frame
        api_key_frame = ttk.LabelFrame(self.root, text="API Key Management", padding="5")
        api_key_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(api_key_frame, text="Username:").pack(side="left", padx=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(api_key_frame, textvariable=self.username_var, width=20)
        self.username_entry.pack(side="left", padx=5)

        self.api_key_var = tk.StringVar()
        ttk.Label(api_key_frame, text="Generated API Key:").pack(side="left", padx=5)
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key_var, state="readonly", width=40)
        self.api_key_entry.pack(side="left", padx=5)

        ttk.Button(api_key_frame, text="Generate API Key", command=self.generate_api_key).pack(side="left", padx=5)

        # Button to set the API Key manually
        ttk.Label(api_key_frame, text="Enter API Key:").pack(side="left", padx=5)
        self.manual_api_key_var = tk.StringVar()
        self.manual_api_key_entry = ttk.Entry(api_key_frame, textvariable=self.manual_api_key_var, width=40)
        self.manual_api_key_entry.pack(side="left", padx=5)

        ttk.Button(api_key_frame, text="Set API Key", command=self.set_api_key).pack(side="left", padx=5)

        # TWAP order frame
        twap_frame = ttk.LabelFrame(self.root, text="Place TWAP Order (Need authentication)", padding="5")
        twap_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(twap_frame, text="Token ID (Optional):").pack(side="left", padx=5)
        self.token_id_var = tk.StringVar()
        self.token_id_entry = ttk.Entry(twap_frame, textvariable=self.token_id_var, width=20)
        self.token_id_entry.pack(side="left", padx=5)


        ttk.Label(twap_frame, text="Symbol: (ex BTCUSDT)").pack(side="left", padx=5)
        self.twap_symbol_var = tk.StringVar()
        self.twap_symbol_combo = ttk.Combobox(twap_frame, textvariable=self.twap_symbol_var)
        self.twap_symbol_combo.pack(side="left", padx=5)

        ttk.Label(twap_frame, text="Quantity:").pack(side="left", padx=5)
        self.quantity_var = tk.DoubleVar()
        self.quantity_entry = ttk.Entry(twap_frame, textvariable=self.quantity_var, width=10)
        self.quantity_entry.pack(side="left", padx=5)

        ttk.Label(twap_frame, text="Duration (seconds):").pack(side="left", padx=5)
        self.duration_var = tk.IntVar()
        self.duration_entry = ttk.Entry(twap_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.pack(side="left", padx=5)

        ttk.Label(twap_frame, text="Side (buy/sell):").pack(side="left", padx=5)
        self.side_var = tk.StringVar()
        self.side_combo = ttk.Combobox(twap_frame, textvariable=self.side_var, values=["buy", "sell"])
        self.side_combo.pack(side="left", padx=5)

        ttk.Label(twap_frame, text="Slice Interval (seconds):").pack(side="left", padx=5)
        self.slice_interval_var = tk.IntVar()
        self.slice_interval_entry = ttk.Entry(twap_frame, textvariable=self.slice_interval_var, width=10)
        self.slice_interval_entry.pack(side="left", padx=5)

        ttk.Label(twap_frame, text="Limit Price:").pack(side="left", padx=5)
        self.limit_price_var = tk.DoubleVar()
        self.limit_price_entry = ttk.Entry(twap_frame, textvariable=self.limit_price_var, width=10)
        self.limit_price_entry.pack(side="left", padx=5)

        ttk.Button(twap_frame, text="Place TWAP Order", command=self.place_twap_order).pack(side="left", padx=5)

        # Order viewing frame
        order_frame = ttk.LabelFrame(self.root, text="Order Book (Need authentication)", padding="5")
        order_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(order_frame, text="Token ID (Optional) :").pack(side="left", padx=5)
        self.token_id_var = tk.StringVar()
        self.token_id_entry = ttk.Entry(order_frame, textvariable=self.token_id_var, width=20)
        self.token_id_entry.pack(side="left", padx=5)

        ttk.Label(order_frame, text="Status:").pack(side="left", padx=5)
        self.status_var = tk.StringVar()
        self.status_entry = ttk.Entry(order_frame, textvariable=self.status_var, width=20)
        self.status_entry.pack(side="left", padx=5)

        ttk.Button(order_frame, text="Fetch Orders", command=self.fetch_orders).pack(side="left", padx=5)

        # Results display frame
        result_frame = ttk.LabelFrame(self.root, text="Results", padding="5")
        result_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.result_text = scrolledtext.ScrolledText(result_frame, height=15)
        self.result_text.pack(fill="both", expand=True)


    def get_symbols(self):
        """Fetch available trading pairs from the API."""
        exchange_name = self.symbols_exchange_var.get()

        available_exchanges = ["binance", "okx", "coinbase"]

        if not exchange_name:
            self.show_result("Please enter an exchange name.")
            return
        if exchange_name not in available_exchanges:
            self.show_result("Exchange name not supported. Please enter one of the following: binance, okx, coinbase")
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}"  # Include API Key in headers
        }

        try:
            response = requests.get(f"{self.api_url}/{exchange_name}/symbols", headers=headers)
            if response.status_code == 200:
                symbols = response.json().get("symbols", [])
                symbols_list = "\n".join(symbols) if symbols else "No symbols found."
                self.symbols_result_text.delete('1.0', tk.END)
                self.symbols_result_text.insert(tk.END, symbols_list)
            else:
                self.show_result(f"Error fetching symbols: {response.json()}")
        except requests.exceptions.RequestException as e:
            self.show_result(f"Error connecting to API: {e}")

    def fetch_klines(self):
        """Fetch and display historical candlesticks data (klines)."""
        exchange = self.exchange_var.get()
        symbol = self.symbol_var.get()
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        interval = self.interval_var.get()
        limit = self.limit_var.get()

        # Validate inputs
        if not exchange or not symbol:
            self.show_result("Please provide valid inputs for exchange and symbol.")
            return

        # start_date = int(datetime(2024, 1, 1).timestamp() * 1000)
        # end_date = int(datetime(2024, 1, 10).timestamp() * 1000)
        # Prepare the query parameters
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "limit": limit
        }

        try:
            response = requests.get(f"{self.api_url}/klines/{exchange}/{symbol}", params=params)
            if response.status_code == 200:
                klines = response.json().get("klines", [])
                self.display_klines(klines)
            else:
                self.show_result(f"Error fetching klines: {response.json().get('detail')}")
        except requests.exceptions.RequestException as e:
            self.show_result(f"Error connecting to API: {e}")

    def display_klines(self, klines):
        """Display the klines in the result text area."""
        if not klines:
            self.show_result("No klines found.")
        else:
            klines_list = "\n".join([json.dumps(kline, indent=2) for kline in klines])
            self.show_result(klines_list)


    def generate_api_key(self):
        """Generate a new API key for the provided username."""
        username = self.username_var.get()
        if not username:
            self.show_result("Please enter a username to generate an API key.")
            return

        try:
            response = requests.post(f"{self.api_url}/generate_api_key", params={"username": username})
            if response.status_code == 200:
                api_key = response.json().get("api_key", "")
                self.api_key_var.set(api_key)
                self.show_result(f"API Key generated successfully for {username}:\n{api_key}")
            else:
                error_message = response.json().get("detail", "Failed to generate API key.")
                self.show_result(f"Error: {error_message}")
        except requests.exceptions.RequestException as e:
            self.show_result(f"Error connecting to API: {e}")

    def set_api_key(self):
        """Set the API key manually from the user's input."""
        api_key = self.manual_api_key_var.get()
        if not api_key:
            self.show_result("Please enter a valid API key.")
            return
        self.api_key = api_key
        self.show_result(f"API Key set successfully: {api_key}")


    def place_twap_order(self):
        """Place a TWAP order."""
        # Fetch inputs from the GUI
        token_id = self.token_id_var.get()  # Fetch token_id
        symbol = self.twap_symbol_var.get()
        quantity = self.quantity_var.get()
        duration = self.duration_var.get()
        side = self.side_var.get()
        slice_interval = self.slice_interval_var.get()
        limit_price = self.limit_price_var.get()

        # Validate inputs
        if not self.api_key:
            self.show_result("Please set an API key first.")
            return


        if not symbol or quantity <= 0 or duration <= 0 or side not in ["buy",
                                                                        "sell"] or slice_interval <= 0 or limit_price <= 0:
            self.show_result("Please provide valid input for all fields.")
            return

        start_time = datetime.utcnow()  # Start time is the current time
        end_time = start_time + timedelta(seconds=duration)  # End time is based on the duration

        # Convert start_time and end_time to ISO string format 'YYYY-MM-DDTHH:MM:SS'
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

        if not token_id:
            token_id = str(uuid.uuid4())  # Generate a new token ID if not provided
            self.show_result(f"Generated token ID (to keep track of your order: {token_id}")

        # Prepare the TWAP order request
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = [{
            "token_id": token_id,  # Use provided token_id or generate a new one
            "exchange": "binance",  # Add exchange field
            "symbol": symbol,
            "quantity": quantity,
            "duration": duration,
            "price": limit_price,
            "start_time": start_time_str,  # Start time is the current time
            "end_time": end_time_str,  # End time is based on the duration
            "side": side,
            "interval": slice_interval,
        }]

        try:
            response = requests.post(f"{self.api_url}/orders/twap", json=data, headers=headers)
            if response.status_code == 200:
                self.show_result(f"TWAP Order placed successfully. \n Generating token ID : {token_id}")
            else:
                self.show_result(f"Error placing TWAP order: {response.json()}")
        except requests.exceptions.RequestException as e:
            self.show_result(f"Error connecting to API: {e}")


    def fetch_orders(self):
        """Fetch and display orders based on token_id or status filter."""
        token_id = self.token_id_var.get()
        status = self.status_var.get()

        # Build the filter parameters
        params = {}
        if token_id:
            params["token_id"] = token_id
        if status:
            params["status"] = status

        # Make the request to fetch orders
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(f"{self.api_url}/orders", params=params, headers=headers)
            if response.status_code == 200:
                orders = response.json()
                self.display_orders(orders)
            else:
                self.show_result(f"Error fetching orders: {response.json().get('detail')}")
        except requests.exceptions.RequestException as e:
            self.show_result(f"Error connecting to API: {e}")

    def display_orders(self, orders):
        """Display orders in the result text area."""
        if not orders:
            self.show_result("No orders found.")
        else:
            order_list = "\n".join([json.dumps(order, indent=2) for order in orders])
            self.show_result(order_list)

    def show_result(self, result_text):
        """Display result in the scrolled text area."""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = OrderBookGUI(root)
    root.mainloop()
    # apikey
    # dd8aa84526f720a9b4f73456b98eaa1ec49e5718e2b59b38a12331b6c2b1bef4
    # b358e983c5168810bd9de11e8c3e1b04b55529dfc474b9420aade14ee4750ddf