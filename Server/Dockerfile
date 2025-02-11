# Utilisation d'une image légère avec Python
FROM python:3.11-slim

# Installer uv
RUN pip install uv

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du serveur
COPY . /app

# Installer les dépendances
RUN uv pip install --system pyproject.toml

# Exposer le port du serveur
EXPOSE 8000

# Lancer le serveur avec uvicorn
CMD ["uvicorn", "Server:app", "--host", "0.0.0.0", "--port", "8000"]