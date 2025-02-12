# Multi Crypto Exchange API

**Version**: 1.0.0
**Auteurs**: Jules Mourgues-Haroche, Alexandre Remiat, Yann Merakeb, Ryhan Chebrek, Adrien Le Masne

---

## Description

Exchange API & Client Documentation

Ce projet se compose d’une API côté serveur et d’une application client (Streamlit et WebSocket) permettant d’interagir avec plusieurs exchanges. L’API offre divers endpoints pour obtenir des données historiques, gérer l’authentification, exécuter des ordres (TWAP), *streamer* des carnets d'ordres, et bien plus encore.

---

## Fonctionnalités principales

- **Multi-Exchanges**  
  Connexion à plusieurs exchanges (Binance, Kraken, CoinbasePro, OKX, etc.) grâce à des modules dédiés pour chaque plateforme, permettant d’accéder aux données et fonctionnalités spécifiques à chacun.

- **Formatage des Symboles**  
  Conversion automatique des symboles standards (ex. "BTC-USD") en formats propres à chaque exchange via un module avancé de formatage.

- **Données Historiques (Klines)**  
  Récupération des chandeliers (klines) pour un symbole donné, avec possibilité de spécifier des intervalles et des plages de dates, facilitant l’analyse technique et historique.

- **Authentification Sécurisée**  
  Gestion des utilisateurs via un système JWT avec des endpoints pour l’authentification (login, logoff), l’enregistrement et la suppression des utilisateurs, assurant un accès protégé aux ressources de l’API.

- **Ordres TWAP**  
  Soumission et simulation d’ordres TWAP pour répartir l'exécution d'une commande sur une période définie, permettant une exécution progressive et optimisée.

- **Communication en Temps Réel**  
  Support d’un endpoint WebSocket permettant aux clients de s’abonner aux mises à jour en temps réel des carnets d’ordres et d’autres données dynamiques.

- **Interface Client Interactive**  
  Application Streamlit fournie pour visualiser et interagir avec les données récupérées par l’API, avec possibilité d’ajouter des captures d’écran et des démonstrations interactives.

---

## Structure du projet

L’arborescence du projet est organisée de la manière suivante :

```
├── Client
│   ├── StreamlitClient.py           # Application Streamlit pour l'interface client
│   ├── Utilities
│   │   └── OrderBookApp.py          # Utilitaires liés à l'affichage des carnets d'ordres
│   └── WebsocketClient.py           # Client WebSocket pour la communication en temps réel
├── Server
│   ├── Exchanges                    # Modules gérant la connexion aux différents exchanges
│   │   ├── Abstract.py
│   │   ├── Binance.py
│   │   ├── CoinbasePro.py
│   │   ├── Exchange.py
│   │   ├── Kraken.py
│   │   ├── OKX.py
│   │   └── __init__.py
│   ├── Server.py                    # Point d'entrée de l'API (serveur FastAPI)
│   └── Utilities                    # Utilitaires internes du serveur
│       ├── Authentification.py      # Gestion de l'authentification et JWT
│       ├── DataBaseManager.py       # Gestion de la base de données
│       ├── SubscriptionManager.py   # Gestion des abonnements (websocket)
│       ├── SymbolFormatter.py       # Formatage des symboles pour différents exchanges
│       ├── TWAPOrder.py             # Simulation d'ordres TWAP
│       └── __init__.py
└── test
    └── test_server.py               # Tests de l'API
```

Voici également une représentation simplifiée et peut-être plus visuelle : 


![Structure](img/structure.png)

---

## Initialisation et lancement du serveur

### Prérequis
- **Python 3.11** (ou version compatible)
- Le gestionnaire de package`uv` doit être installé.
- Toutes les dépendances nécessaires doivent être installées, et le seront grâce à `uv`.

### Installation des dépendances

1. Installer le gestionnaire de package :
```bash
pip install uv
```

2. Installer les dépendances :
```bash
uv sync
```

## Lancement du serveur

Pour démarrer le serveur, assurez-vous que le répertoire de travail est correctement configuré (par exemple, /app dans votre Dockerfile) afin que les imports relatifs fonctionnent correctement.

Utilisez la commande suivante :
```bash
uv run Server/Server.py   
```

Cette commande démarre l’application FastAPI en écoutant sur toutes les interfaces réseau (0.0.0.0) au port 8000.

---

## Liste des endpoints

Voici une vue d’ensemble des principaux endpoints exposés par l’API :

### Endpoints de base
- **GET `/health`**  
  Vérifie l’état de l’API retourne  
  ```json
  { "status": "healthy" }
  ```
  
  *Exemple d'appel* :  
  ```bash
  GET /health
  ```
  
- **GET `/ping`**  
  Endpoint de test qui retourne  
  ```json
  { "message": "pong" }
  ```
  
  *Exemple d'appel* :  
  ```bash
  GET /ping
  ```
  
### Endpoints liés aux exchanges et symboles
- **GET `/exchanges`**  
  Retourne la liste des exchanges disponibles.
  
  *Exemple d'appel* :  
  ```bash
  GET /exchanges
  ```
  
  *Exemple de sortie* :  
  ```json
  { "exchanges": ["binance", "kraken", "coinbasepro", "okx"] }
  ```
  
- **GET `/{exchange}/symbols`**  
  Retourne la liste des paires de trading disponibles pour l’exchange spécifié.
  
  *Exemple d'appel* :  
  ```bash
  GET /binance/symbols
  ```
  
  *Exemple de sortie* :  
  ```json
  { "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"] }
  ```
  
- **GET `/klines/{exchange}/{symbol}`**  
  Retourne les données historiques (candlesticks) pour un symbole donné sur un exchange.  
  Paramètres optionnels : `start_date`, `end_date`, `interval`.
  
  *Exemple d'appel* :  
  ```bash
  GET /klines/binance/BTC-USD?start_date=2025-01-01&end_date=2025-01-07&interval=1d
  ```
  
  *Exemple de sortie* :  
  ```json
  [
    {
        "timestamp": 1735689600000, 
        "date": "2025-01-01 00:00:00", 
        "open": 93576, 
        "high": 95151.15, 
        "low": 92888, 
        "close": 94591.79, 
        "volume": 10373.32613
    }
    ...
  ]
  ```
  
### Endpoints d’authentification et gestion des utilisateurs
- **POST `/login`**  
  Authentifie l’utilisateur et retourne un token JWT.
  
  *Exemple d'input* :  
  ```json
  { "username": "alice", "password": "secret" }
  ```
  
  *Exemple de sortie* :  
  ```json
  { "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
  ```
  
- **POST `/logoff`**  
  Invalide le token (déconnexion).
  
  *Exemple d'appel* :  
  ```bash
  POST /logoff
  ```
  
- **POST `/register`**  
  Enregistre un nouvel utilisateur avec le rôle `user`.
  
  *Exemple d'input* :  
  ```json
  { "username": "bob", "password": "mypassword" }
  ```
  
  *Exemple de sortie* :  
  ```json
  { "message": "User registered successfully" }
  ```
  
- **DELETE `/unregister`**  
  Supprime un utilisateur (non-admin uniquement).
  
  *Exemple d'appel* :  
  ```bash
  DELETE /unregister
  ```
  
- **GET `/info`**  
  Endpoint protégé qui retourne des informations basiques sur l’utilisateur connecté.
  
  *Exemple de sortie* :  
  ```json
  { "message": "Hello alice! This is info data", "timestamp": "2025-01-07T12:00:00" }
  ```
  
- **GET `/users`**  
  (Section Admin) Retourne la liste de tous les utilisateurs. Accessible uniquement aux administrateurs.
  
  *Exemple de sortie* :  
  ```json
  [
    { "username": "alice", "role": "user" },
    { "username": "admin", "role": "admin" }
  ]
  ```
  
### Endpoints relatifs aux ordres TWAP
- **POST `/orders/twap`**  
  Soumet un ordre TWAP. La simulation de l’ordre est lancée en tâche de fond.
  
  *Exemple d'input* :  
  ```json
  [
    {
    "order_id": "twap_001",
    "symbol": "BTC-USD",
    "side": "buy",
    "total_quantity": 1.0,
    "limit_price": 30000.0,
    "duration": 5,
    "interval": 1
    },
    ...
  ]
  ```
  
  *Exemple de sortie* :  
  ```json
  { "message": "TWAP order accepted", "order_id": "twap_001" }
  ```
  
- **GET `/orders`**  
  Liste les ordres existants, avec options de filtrage par ID ou statut.
  
  *Exemple d'appel* :  
  ```bash
  GET /orders
  ```
  
  *Exemple de sortie* :  
  ```json
  [
    {"order_id": "order123", "username": "admin", "symbol": "ETH-USD", "duration": 60, "interval": 1, "order_status": "closed"}
  ]
  ```
  
- **GET `/orders/{order_id}`**  
  Détail d’un ordre spécifique.
  
  *Exemple d'appel* :  
  ```bash
  GET /orders/twap_001
  ```
  
  *Exemple de sortie* :  
  ```json
    { 
      "order_id": "twap_001",
      "username": "admin",
      "symbol": "ETH-USD", 
      "side": "buy", 
      "duration": 60,
      "interval": 1,
      "total_quantity": 1.0, 
      "limit_price": 2615.0, 
      "status": "open",
      "executions": [
        {
          "price": 2611.01,
          "quantity": 0.16666666666666666,
          "timestamp": "2025-02-11T21:22:55.756847"
        },
        {
          "price": 2610.76,
          "quantity": 0.16666666666666666,
          "timestamp": "2025-02-11T21:22:56.841897"
        },
        ...
      ]
    }
  ```
  
### Endpoint WebSocket
- **WebSocket `/ws`**  
  Permet aux clients de se connecter pour recevoir en temps réel des mises à jour des carnets d’ordres.
  
  *Exemple d'input* (message envoyé par le client) :  
  ```json
  { "action": "subscribe", "exchange": "kraken", "symbol": "BTC-USD" }
  ```
  
  *Exemple de sortie* (message reçu par le client) :  
  ```json
  { "message": "Subscribed to kraken BTC-USD" }
  ```

---

# Client et Tests

## Application Client
Le dossier **Client** contient l’application client basée sur **Streamlit**, qui permet d’afficher visuellement certaines données issues de l’API.  
Les principaux fichiers sont :
- **StreamlitClient.py** : Point d’entrée de l’application Streamlit.
- **WebsocketClient.py** : Client pour se connecter au WebSocket et recevoir les mises à jour en temps réel.

## Lancement du Client Streamlit
Pour lancer l’application Streamlit, exécutez la commande suivante :

```bash
uv run streamlit run Client/StreamlitClient.py
```

Le client permet de s'authentifier, de s'enregistrer, de tester les différents endpoints ainsi que de visualiser en temps réel les données de carnets d'ordres des différents exchanges.

Voici un exemple visuel : 

![Exemple Streamlit](img/animated.gif)

## Lancement du Client Websocket Only
Pour lancer le client Websocket, exécutez la commande suivante :

```bash
uv run Client/WebsocketClient.py
```

Ce client s'authentifie directement, et va présenter en temps réel le carnet d'ordre de l'ETH-USD sur OKX, Binance et Kraken.

Le résultat ressemblera à ceci dans la console :

```
Aggregated Order Book for ETH-USD
Bid Exch     | Bid Qty    | Bid Price  || Ask Price  | Ask Qty    | Ask Exch    
--------------------------------------------------------------------------------
okx          |       0.00 |    2620.60 ||    2620.50 |      77.54 | binance     
okx          |       0.22 |    2620.50 ||    2620.51 |       3.97 | binance     
binance      |      17.70 |    2620.49 ||    2620.52 |       2.99 | binance     
binance      |       0.00 |    2620.46 ||    2620.53 |       0.00 | binance     
binance      |       0.00 |    2620.44 ||    2620.54 |       3.21 | kraken      
binance      |       0.04 |    2620.43 ||    2620.57 |       0.00 | binance     
okx          |       0.01 |    2620.42 ||    2620.60 |       1.82 | binance     
kraken       |       0.00 |    2620.41 ||    2620.61 |       4.70 | okx         
kraken       |       3.70 |    2620.40 ||    2620.62 |       8.40 | binance     
binance      |       0.67 |    2620.39 ||    2620.63 |       3.17 | binance     
binance      |      13.36 |    2620.38 ||    2620.65 |      31.29 | kraken      
binance      |       2.80 |    2620.36 ||    2620.66 |       0.05 | okx         
kraken       |       4.77 |    2620.35 ||    2620.67 |       0.80 | okx         
binance      |       0.05 |    2620.34 ||    2620.68 |       0.76 | okx         
kraken       |      16.03 |    2620.05 ||    2620.69 |       0.80 | binance     
kraken       |      54.59 |    2620.04 ||    2620.70 |       1.06 | binance     
kraken       |      41.98 |    2619.97 ||    2620.74 |       6.41 | kraken      
kraken       |       5.50 |    2619.91 ||    2620.88 |       3.70 | kraken      
kraken       |      33.59 |    2619.81 ||    2620.99 |       4.77 | kraken      
kraken       |       3.21 |    2619.80 ||    2621.08 |       5.50 | kraken      
kraken       |       0.79 |    2619.66 ||    2621.09 |       3.21 | kraken      
             |       0.00 |       0.00 ||    2621.13 |       1.00 | kraken      
             |       0.00 |       0.00 ||    2621.23 |       0.78 | kraken      
             |       0.00 |       0.00 ||    2621.35 |       0.82 | kraken      
--------------------------------------------------------------------------------
```
---

## Tests
Les tests de l’API se trouvent dans le dossier **test**. Pour exécuter les tests (par exemple, avec pytest) :

```bash
uv run pytest
```

> **Warning**  
> Les tests unitaires nécessitent une connexion Internet active pour accéder aux API des différents exchanges.  
> Une version des tests utilisant des mocks et ne nécessitant pas de connexion est prévue pour une prochaine mise à jour.