import asyncio
import json
import streamlit as st
import aiohttp

# Configuration de la page
st.set_page_config(page_title="WebSocket Client", layout="wide")

# Variables d'état
status = st.empty()
messages_container = st.container()
subscription_input = st.text_input("Symbole à souscrire (ex: BTCUSDT)", key="subscribe_input")
unsubscribe_input = st.text_input("Symbole à désouscrire (ex: BTCUSDT)", key="unsubscribe_input")
is_connected = st.checkbox("Connecter au WebSocket", value=False)
send_subscription = st.button("Envoyer souscription", key="subscribe_button")
send_unsubscription = st.button("Envoyer désouscription", key="unsubscribe_button")
received_messages = st.empty()

# URL du serveur WebSocket
WS_SERVER_URL = "ws://localhost:8000/ws"

# Session WebSocket globale
ws_connection = None


async def websocket_client():
    """Maintient une connexion WebSocket ouverte."""
    global ws_connection

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_SERVER_URL) as ws:
                ws_connection = ws  # Enregistre la connexion principale
                status.write(f"Connecté au serveur WebSocket : {WS_SERVER_URL}")

                # Écouter les messages WebSocket
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        with messages_container:
                            st.write(f"Message reçu : {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        st.error(f"Erreur WebSocket : {msg.data}")
                        break

    except Exception as e:
        st.error(f"Erreur WebSocket : {str(e)}")
    finally:
        ws_connection = None
        status.write("Déconnecté.")


async def send_message(action, symbol):
    """Envoie un message via la connexion WebSocket existante."""
    global ws_connection

    if ws_connection is not None and not ws_connection.closed:
        try:
            await ws_connection.send_json({"action": action, "symbol": symbol})
            status.write(f"{action.capitalize()} envoyé pour {symbol}")
        except Exception as e:
            st.error(f"Erreur lors de l'envoi du message : {str(e)}")
    else:
        st.error("WebSocket non connecté. Connectez-vous avant d'envoyer un message.")


# Gestion de la connexion WebSocket
if is_connected:
    if ws_connection is None:  # Lancer la connexion si elle n'existe pas
        asyncio.run(websocket_client())
else:
    status.write("Déconnecté. Cochez la case pour vous connecter.")

# Gestion des souscriptions
if send_subscription and subscription_input:
    asyncio.run(send_message("subscribe", subscription_input))

# Gestion des désabonnements
if send_unsubscription and unsubscribe_input:
    asyncio.run(send_message("unsubscribe", unsubscribe_input))