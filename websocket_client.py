import asyncio
import websockets
import json
from tabulate import tabulate

def print_order_book(data):
    """
    Affiche les données du carnet d'ordres au format tableau.

    :param data: Dictionnaire contenant les données du carnet d'ordres.
    """
    for symbol, order_book in data.items():
        if "bids" in order_book and "asks" in order_book:
            bids = order_book["bids"]
            asks = order_book["asks"]

            # Préparer les données pour l'affichage
            table_data = []
            for i in range(max(len(bids), len(asks))):
                bid = bids[i] if i < len(bids) else ["", ""]
                ask = asks[i] if i < len(asks) else ["", ""]
                table_data.append([bid[0], bid[1], ask[0], ask[1]])

            # Afficher les données au format tableau
            print(f"Order Book for {symbol}:")
            print(tabulate(table_data, headers=["Bid Price", "Bid Quantity", "Ask Price", "Ask Quantity"], tablefmt="pretty"))


async def websocket_client():
    uri = "ws://localhost:8000/ws"  # URL du serveur WebSocket

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server.")

        async def send_commands():
            for _ in range(3):
                # Lire la commande depuis le terminal
                command = input("Enter command (e.g., sub BTCUSDT or unsub BTCUSDT): ").strip()
                if command.lower().startswith("sub "):
                    symbol = command.split(" ")[1].strip().upper()
                    await websocket.send(json.dumps({"action": "subscribe", "symbol": symbol}))
                    print(f"Subscribed to {symbol}.")
                elif command.lower().startswith("unsub "):
                    symbol = command.split(" ")[1].strip().upper()
                    await websocket.send(json.dumps({"action": "unsubscribe", "symbol": symbol}))
                    print(f"Unsubscribed from {symbol}.")
                else:
                    print("Invalid command. Use 'sub SYMBOL' to subscribe or 'unsub SYMBOL' to unsubscribe.")

        async def receive_messages():
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print_order_book(data)
                except websockets.ConnectionClosed:
                    print("Connection closed.")
                    break

        # Démarre les tâches en parallèle
        await asyncio.gather(
            send_commands(),
            receive_messages()
        )


if __name__ == "__main__":
    asyncio.run(websocket_client())