import streamlit as st
import requests
from Utilities.OrderBookApp import OrderBookApp

# URL de base de votre serveur (ajustez si nécessaire)
SERVER_URL = "http://localhost:8000"
DEFAULT_WS_URL = "ws://localhost:8000/ws?token={token}"

# Set page to wide mode
st.set_page_config(layout="wide")

# Stocker le token dans la session Streamlit
if "token" not in st.session_state:
    st.session_state.token = ""

st.title("Test Client for Exchange API")

tabs = st.tabs([
    "Login/Register", 
    "Exchanges", 
    "Symbols", 
    "Historical Data", 
    "Submit TWAP Order", 
    "Orders", 
    "WebSocket"
])

# -----------------------------------------------------------------------------
# Onglet 1 : Login / Register
# -----------------------------------------------------------------------------
with tabs[0]:
    st.header("Login / Register")
    st.caption("You can login as 'admin' with password 'admin123' or register a new user.")
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", type="password", key="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            url = SERVER_URL + "/login"
            data = {"username": username, "password": password}
            try:
                resp = requests.post(url, json=data)
                result = resp.json()
                token = result.get("access_token", "")
                msg = result.get("detail", "")
                st.session_state.token = token
                if msg != "":
                    st.error(msg)
                else:
                    st.success("Logged in successfully")
            except Exception as e:
                st.error(f"Login error: {e}")
    with col2:
        if st.button("Register"):
            url = SERVER_URL + "/register"
            data = {"username": username, "password": password}
            try:
                resp = requests.post(url, json=data)
                result = resp.json()
                msg = result.get("message", "")
                detail = result.get("detail", "")
                if detail != "":
                    st.error(detail)
                else:
                    st.success(msg)
            except Exception as e:
                st.error(f"Registration error: {e}")

    if st.session_state.token != "":
        st.write("Current token:")
        st.code(st.session_state.token)

# -----------------------------------------------------------------------------
# Onglet 2 : Get Exchanges
# -----------------------------------------------------------------------------
with tabs[1]:
    st.header("Get Exchanges")
    if st.button("Fetch Exchanges"):
        url = SERVER_URL + "/exchanges"
        try:
            resp = requests.get(url)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# Onglet 3 : Get Symbols
# -----------------------------------------------------------------------------
with tabs[2]:
    st.header("Get Symbols for an Exchange")
    exch_input = st.text_input("Exchange", value="binance")
    if st.button("Fetch Symbols"):
        url = SERVER_URL + f"/{exch_input}/symbols"
        try:
            resp = requests.get(url)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# Onglet 4 : Get Historical Data (Klines)
# -----------------------------------------------------------------------------
with tabs[3]:
    st.header("Get Historical Data (Klines)")
    col1, col2 = st.columns(2)
    with col1:
        klines_exch = st.text_input("Exchange", value="binance", key="klines_exch")
        klines_symbol = st.text_input("Symbol", value="BTCUSDT", key="klines_symbol")
        klines_start = st.text_input("Start Date (YYYY-MM-DD)", value="2025-01-01", key="klines_start")
    with col2:
        klines_end = st.text_input("End Date (YYYY-MM-DD)", value="2025-02-01", key="klines_end")
        klines_interval = st.text_input("Interval", value="1d", key="klines_interval")
    if st.button("Fetch Kliness"):
        url = SERVER_URL + f"/klines/{klines_exch}/{klines_symbol}?start_date={klines_start}&end_date={klines_end}&interval={klines_interval}"
        try:
            resp = requests.get(url)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# Onglet 5 : Submit TWAP Order
# -----------------------------------------------------------------------------
with tabs[4]:
    st.header("Submit TWAP Order")
    col1, col2 = st.columns(2)
    with col1:
        order_id = st.text_input("Order ID", value="order123")
        twap_symbol = st.text_input("Symbol (e.g., ETH-USD)", value="ETH-USD")
        twap_side = st.text_input("Side (buy/sell)", value="buy")
    with col2:
        total_qty = st.number_input("Total Quantity", value=10.0)
        limit_price = st.number_input("Limit Price", value=2750.0)
        duration = st.number_input("Duration (sec)", value=60, step=1)
        interval = st.number_input("Interval (sec)", value=1, step=1)  # si nécessaire
    if st.button("Submit TWAP Order"):
        url = SERVER_URL + "/orders/twap"
        data = {
            "order_id": order_id,
            "symbol": twap_symbol,
            "side": twap_side,
            "total_quantity": total_qty,
            "limit_price": limit_price,
            "duration": duration,
            "interval": interval
        }
        headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
        try:
            resp = requests.post(url, json=data, headers=headers)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# Onglet 6 : Orders (List and Detail)
# -----------------------------------------------------------------------------
with tabs[5]:
    st.header("List Orders")
    col1, col2 = st.columns(2)
    with col1:
        order_id_filter = st.text_input("Filter by Order ID", key="order_filter")
    with col2:
        order_status_filter = st.text_input("Filter by Order Status", key="status_filter")
    if st.button("List Orders"):
        url = SERVER_URL + "/orders"
        params = {}
        if order_id_filter:
            params["order_id"] = order_id_filter
        if order_status_filter:
            params["order_status"] = order_status_filter
        headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
        try:
            resp = requests.get(url, params=params, headers=headers)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.header("Get Order Detail")
    detail_order_id = st.text_input("Order ID for Detail", key="detail_order")
    if st.button("Get Order Detail"):
        url = SERVER_URL + f"/orders/{detail_order_id}"
        headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
        try:
            resp = requests.get(url, headers=headers)
            result = resp.json()
            st.json(result)
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------------------------------------------------------
# Onglet 7 : WebSocket Test
# -----------------------------------------------------------------------------

# Pour stocker l'instance MyOrderBookApp
if "app" not in st.session_state:
    st.session_state.app = None

with tabs[6]:

    col1, col2 = st.columns(2) 
    
    with col1:
        selected_symbol = st.selectbox(
                "Select symbol",
                options=["BTC-USD", "ETH-USD"],
                index=0
            )

    with col2:
        ws_url = DEFAULT_WS_URL.format(token=st.session_state.token)

        if st.session_state.token != "":
            st.success("Authenticated")
        else:
            st.error("Not authenticated")

    websocket_on = False

    with col1:
        if st.button("Start"):
            st.write(f"Starting WebSocket for {selected_symbol}")
            websocket_on = True

    if websocket_on:
        if st.session_state.app is not None:
            st.session_state.app.stop()
        st.session_state.app = OrderBookApp(ws_url, selected_symbol, ["binance", "okx", "kraken"])
        # Lance la connexion WS en arrière-plan
        st.session_state.app.run()

    with col2:
        if st.button("Stop"):
            if st.session_state.app is not None:
                st.write("Stopping WebSocket...")
                st.session_state.app.stop()
            else:
                st.write("No active WebSocket to stop.")
        