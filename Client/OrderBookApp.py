import websocket
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import streamlit as st

class OrderBookApp:
    def __init__(self, ws_url: str, symbol: str, exchanges: list) -> None:
        self.ws_url = ws_url
        self.symbol = symbol
        self.exchanges = exchanges
        self._ws = None
        self.chart = st.empty()
        self._data = {"bids": [], "asks": []}
        

    @staticmethod
    def _on_open(ws):
        print("WebSocket connection opened")
        for exchange in ws.exchanges:
            sub_message = {
            "action": "subscribe",
            "exchange": exchange,
            "symbol": ws.symbol
            }
            ws.send(json.dumps(sub_message))


    @staticmethod
    def _on_error(ws, error):
        print("WebSocket error:", error)

    @staticmethod
    def _on_close(ws, close_status_code, close_msg):
        print("WebSocket closed", close_status_code, close_msg)
        for exchange in ws.exchanges:
            sub_message = {
            "action": "unsubscribe",
            "exchange": exchange,
            "symbol": ws.symbol
            }
            ws.send(json.dumps(sub_message))

    def _on_message(self, ws, message):
        print("Received message:", message)
        data = json.loads(message)

        if "bids" in data and "asks" in data:
            # Convertir le nouveau format
            new_bids = []
            for item in data["bids"]:
                new_bids.append({
                    "price": float(item["price"]),
                    "exchanges": {ex: float(v) for ex, v in item["exchanges"].items()},
                    "total": float(item["total"])
                })
            new_asks = []
            for item in data["asks"]:
                new_asks.append({
                    "price": float(item["price"]),
                    "exchanges": {ex: float(v) for ex, v in item["exchanges"].items()},
                    "total": float(item["total"])
                })

            self._data["bids"] = new_bids
            self._data["asks"] = new_asks

            self._update_chart()

    def _update_chart(self):
        """Crée un subplot par exchange, tracant la depth (bids en vert, asks en rouge)."""
        bids = self._data["bids"]
        asks = self._data["asks"]
        if not bids and not asks:
            return

        # 1) Récupérer la liste de tous les exchanges
        all_exchanges = set()
        for item in bids + asks:
            all_exchanges.update(item["exchanges"].keys())
        all_exchanges = sorted(all_exchanges)

        # Créer un subplot pour chaque exchange (vertical)
        fig = sp.make_subplots(
            rows=1,
            cols=len(all_exchanges),
            shared_xaxes=False,
            shared_yaxes=False,
            vertical_spacing=0.15,
            subplot_titles=[f"{exch}" for exch in all_exchanges]
        )

        # Helper pour trier + cumul (side="bid"/"ask")
        def prepare_data_for_exchange(exchange, side):
            """
            Retourne un DF avec les colonnes price, cum_qty
            pour l'exchange donné et le side (bid/ask).
            """
            if side == "bid":
                # Extraire [price, qty], tri décroissant + cumul
                relevant = []
                for item in bids:
                    qty = item["exchanges"].get(exchange, 0.0)
                    if qty > 0:
                        relevant.append((item["price"], qty))
                if not relevant:
                    return pd.DataFrame()
                relevant.sort(key=lambda x: x[0], reverse=True)
            else:
                # side == "ask"
                relevant = []
                for item in asks:
                    qty = item["exchanges"].get(exchange, 0.0)
                    if qty > 0:
                        relevant.append((item["price"], qty))
                if not relevant:
                    return pd.DataFrame()
                relevant.sort(key=lambda x: x[0])

            df = pd.DataFrame(relevant, columns=["price", "qty"])
            # Ajouter la ligne initiale
            if not df.empty:
                df = pd.concat([
                    pd.DataFrame([[df["price"].iloc[0], 0]], columns=["price", "qty"]),
                    df
                ], ignore_index=True)
                df["cum_qty"] = df["qty"].cumsum()
            return df

        # Pour chaque exchange, on ajoute 2 traces (bids en vert, asks en rouge) dans le subplot (row=i).
        col_index = 1
        for exch in all_exchanges:
            # Bids
            df_bids = prepare_data_for_exchange(exch, side="bid")
            if not df_bids.empty:
                fig.add_trace(go.Scatter(
                    x=df_bids["price"],
                    y=df_bids["cum_qty"],
                    name=f"Bid {exch}",
                    line=dict(color="green", shape='hv'),
                    fill='tozeroy',
                    fillcolor='rgba(0,255,0,0.2)',
                    mode='lines'
                ), row=1, col=col_index)

            # Asks
            df_asks = prepare_data_for_exchange(exch, side="ask")
            if not df_asks.empty:
                fig.add_trace(go.Scatter(
                    x=df_asks["price"],
                    y=df_asks["cum_qty"],
                    name=f"Ask {exch}",
                    line=dict(color="red", shape='hv'),
                    fill='tozeroy',
                    fillcolor='rgba(255,0,0,0.2)',
                    mode='lines'
                ), row=1, col=col_index)

            col_index += 1

        fig.update_layout(
            title="Order Book per Exchange",
            showlegend=True,
            template="plotly_white"
        )

        # Mettre à jour les titres d'axe, par exemple
        for i in range(1, len(all_exchanges)+1):
            fig.update_xaxes(title_text="Price", row=1, col=i)
            fig.update_yaxes(title_text="Cumulative Qty", row=1, col=i)

        self.chart.plotly_chart(fig, use_container_width=True)

    def run(self):

        print("Connecting to WebSocket:", self.ws_url)
        self._ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self._ws.symbol = self.symbol
        self._ws.exchanges = self.exchanges
        
        self._ws.run_forever()

    def stop(self):
        if self._ws is not None:
            self._ws.on_close(self._ws, 1000, "Stopped by user")
            self._ws.close()
            self._ws = None
