import pytest
import requests
from os import getenv

if getenv("IS_DOCKERIZED"):
    BASE_URL = "http://server"
else:
    BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def token_fixture():
    """
    Fixture qui s’occupe de créer un utilisateur (s’il n’existe pas) 
    et de récupérer un token pour les tests.
    """
    # 1) On tente de s’enregistrer (ignorer les éventuelles erreurs si déjà créé)
    register_url = f"{BASE_URL}/register"
    _ = requests.post(register_url, json={"username": "testuser", "password": "testpass"})
    # on ignore l'erreur si l'utilisateur existe déjà

    # 2) On se connecte pour récupérer le token
    login_url = f"{BASE_URL}/login"
    log_resp = requests.post(login_url, json={"username": "testuser", "password": "testpass"})
    assert log_resp.status_code == 200, f"Login failed: {log_resp.text}"
    data = log_resp.json()
    token = data["access_token"]
    return token


def test_ping():
    """Vérifie l'endpoint /ping"""
    url = f"{BASE_URL}/ping"
    resp = requests.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "pong", f"Unexpected ping response: {data}"


def test_info_unauthenticated():
    """Vérifie que /info sans token renvoie 403."""
    url = f"{BASE_URL}/info"
    resp = requests.get(url)
    assert resp.status_code == 403, f"Expecting 403, got {resp.status_code}"


def test_info_authenticated(token_fixture):
    """Teste l'endpoint /info avec token valide."""
    url = f"{BASE_URL}/info"
    headers = {"Authorization": f"Bearer {token_fixture}"}
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, f"Expecting 200, got {resp.status_code} - {resp.text}"
    data = resp.json()
    assert "message" in data and "Hello testuser" in data["message"], f"Unexpected info response: {data}"
    assert "timestamp" in data, "No timestamp returned"


def test_exchanges():
    """Teste le endpoint /exchanges"""
    url = f"{BASE_URL}/exchanges"
    resp = requests.get(url)
    assert resp.status_code == 200, f"Expecting 200, got {resp.status_code}"
    data = resp.json()
    assert "exchanges" in data, f"Response has no 'exchanges': {data}"


def test_symbols():
    """Teste le endpoint /{exchange}/symbols (ex: binance)."""
    exchange = "binance"
    url = f"{BASE_URL}/{exchange}/symbols"
    resp = requests.get(url)
    assert resp.status_code in [200, 404], f"Expecting 200 or 404, got {resp.status_code}"
    if resp.status_code == 200:
        data = resp.json()
        assert "symbols" in data, f"Response has no 'symbols': {data}"


def test_klines(token_fixture):
    """
    Teste l'endpoint /klines/{exchange}/{symbol} (ex: binance / BTCUSDT) 
    - On ne force pas de date, on récupère les 5 derniers jours par défaut.
    """
    exchange = "binance"
    symbol  = "BTC-USD"  # va être converti en BTCUSDT
    url = f"{BASE_URL}/klines/{exchange}/{symbol}"

    resp = requests.get(url)

    assert resp.status_code == 200, f"Expecting 200, got {resp.status_code}"
    data = resp.json()
    # data doit être une liste (liste de chandelles)
    assert isinstance(data, list), f"Expecting list of klines, got {type(data)}"



def test_orders_CRUD(token_fixture):
    """
    Test minimal sur l’API /orders/twap ou /orders 
    """
    # 1) Créer un ordre TWAP
    twap_url = f"{BASE_URL}/orders/twap"
    headers = {"Authorization": f"Bearer {token_fixture}"}
    req_body = {
        "order_id": "test_twap_001",
        "symbol": "BTC-USD",
        "side": "buy",
        "total_quantity": 1.0,
        "limit_price": 30000.0,
        "duration": 5,
        "interval": 1
    }
    resp = requests.post(twap_url, json=req_body, headers=headers)
    assert resp.status_code in [202, 400, 500], f"Expecting 202 or error, got {resp.status_code}"
    if resp.status_code == 202:
        data = resp.json()
        assert "message" in data, f"No 'message' in twap response: {data}"

    # 2) Lister les ordres
    list_url = f"{BASE_URL}/orders"
    resp = requests.get(list_url, headers=headers)
    assert resp.status_code == 200, f"Expecting 200, got {resp.status_code}"
    data = resp.json()
    assert isinstance(data, list), "Expecting a list of orders"
    # On peut essayer de trouver l'ordre test_twap_001
    assert any((o.get("order_id")=="test_twap_001") for o in data)
    # Ce n'est pas forcément certain, selon si la db est stable, 
    # on n'échoue pas le test s'il n'existe pas


def test_unregister_user(token_fixture):
    """
    Vérifie qu'on peut se désinscrire (si on n'est pas admin).
    Mais attention, si vous supprimez testuser, vous ne pourrez plus l'utiliser pour les autres tests...
    => On le commente souvent pour éviter ça, ou on le place en dernier test.
    """
    # On suppose que testuser n'est pas admin
    url = f"{BASE_URL}/unregister"
    headers = {"Authorization": f"Bearer {token_fixture}"}
    # On appelle
    resp = requests.delete(url, headers=headers)
    # Il risque de renvoyer 200 ou un autre code 
    print("Unregister response:", resp.status_code, resp.text)
    assert resp.status_code == 200, "Failed to unregister user"
    #pass