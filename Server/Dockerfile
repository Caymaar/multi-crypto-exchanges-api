# Utilisation d'une image légère avec Python et uv
FROM python:3.11-slim

# Installer uv
RUN pip install uv

# Copier les fichiers du serveur
WORKDIR /app
COPY . /app

# Installer les dépendances avec uv
RUN uv pip venv

# Exposer le port du serveur (ajustez si nécessaire)
EXPOSE 8000

# Lancer le serveur avec uv
CMD ["uv", "run", "Server.py"]
