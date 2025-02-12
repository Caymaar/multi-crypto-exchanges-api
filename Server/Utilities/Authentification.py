import json
import os
import time
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

SECRET_KEY = "42"
security = HTTPBearer()

# Fichier pour stocker les tokens invalidés
INVALIDATED_TOKENS_FILE = "Server/Utilities/invalidated_tokens.json"

# Vérifier si le fichier existe, sinon le créer
if not os.path.exists(INVALIDATED_TOKENS_FILE):
    with open(INVALIDATED_TOKENS_FILE, "w") as f:
        json.dump({}, f)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_token(username: str) -> str:
    """Create a simple JWT token with expiration"""
    expiration = datetime.utcnow() + timedelta(minutes=30)
    token = jwt.encode(
        {
            "username": username,
            "exp": expiration 
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

def load_invalidated_tokens():
    """Load invalidated tokens from JSON file"""
    with open(INVALIDATED_TOKENS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_invalidated_token(token: str, expiration: int):
    """Save an invalidated token to JSON file"""
    tokens = load_invalidated_tokens()
    tokens[token] = expiration  # Stocker le timestamp d'expiration
    with open(INVALIDATED_TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted"""
    tokens = load_invalidated_tokens()
    
    # Nettoyer les tokens expirés
    current_time = time.time()
    tokens = {t: exp for t, exp in tokens.items() if exp > current_time}

    # Sauvegarder la liste propre
    with open(INVALIDATED_TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

    return token in tokens

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been invalidated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload["username"]
        if not username:
            raise Exception("Missing username in token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def verify_ws_token(token: str) -> str:
    """
    Vérifie le token JWT fourni sous forme de chaîne.
    Renvoie le nom d'utilisateur (ou un autre champ) extrait du token.
    Lève une exception si le token est invalide.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("username")
        if not username:
            raise Exception("Missing username in token")
        return username
    except (jwt.InvalidTokenError, Exception) as e:
        raise Exception("Invalid token") from e
    
async def invalidate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Invalidate a JWT token by adding it to the blacklist"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expiration = payload.get("exp")

        if expiration:
            save_invalidated_token(token, expiration)
        return {"message": "Token has been invalidated"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token already expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")