import asyncio
import websockets
import json
import threading
import sys
import keyboard

# URL de votre serveur WebSocket
WS_SERVER_URL = "ws://localhost:8000/ws"

# État pour contrôler l'exécution
is_streaming = True


async def send_message(ws, action, symbol):
    """Envoie une commande de souscription ou désouscription via WebSocket."""
    message = {"action": action, "symbol": symbol}
    await ws.send(json.dumps(message))
    print(f"Envoyé : {message}")


async def handle_messages(ws):
    """Écoute et affiche les messages du serveur en continu."""
    global is_streaming
    try:
        async for message in ws:
            if is_streaming:
                data = json.loads(message)
                print(f"Reçu : {data}")
    except websockets.ConnectionClosed as e:
        print(f"Connexion fermée : {e}")


async def interactive_menu(ws):
    """Permet à l'utilisateur de souscrire, désouscrire ou quitter."""
    global is_streaming
    while True:
        print("\nOptions :")
        print("1. Subscribe à un ticker")
        print("2. Unsubscribe d'un ticker")
        print("3. Quitter le menu et retourner au stream")
        print("4. Quitter le programme")

        choice = input("Choisissez une option : ").strip()

        if choice == "1":
            symbol = input("Entrez le ticker à souscrire (ex: BTCUSDT) : ").strip()
            await send_message(ws, "subscribe", symbol)
        elif choice == "2":
            symbol = input("Entrez le ticker à désouscrire (ex: BTCUSDT) : ").strip()
            await send_message(ws, "unsubscribe", symbol)
        elif choice == "3":
            print("Retour au stream des messages...")
            is_streaming = True
            break
        elif choice == "4":
            print("Déconnexion et arrêt...")
            await ws.close()
            sys.exit(0)
        else:
            print("Option invalide. Réessayez.")


async def websocket_client():
    """Maintient une connexion WebSocket et gère les interactions."""
    global is_streaming

    try:
        async with websockets.connect(WS_SERVER_URL) as ws:
            print(f"Connecté au WebSocket : {WS_SERVER_URL}")

            # Tâche pour écouter les messages en arrière-plan
            listen_task = asyncio.create_task(handle_messages(ws))

            while True:
                print("\n[Appuyez sur 'm' pour le menu ou laissez tourner pour continuer à streamer...]")

                if keyboard.is_pressed('m'):
                    is_streaming = False  # Pause du stream pendant le menu
                    await interactive_menu(ws)
                else:
                    print("Commande non reconnue, retour au stream...")

    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    asyncio.run(websocket_client())