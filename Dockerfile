# Utilise une image Python légère
FROM python:3.10-slim

# Installer curl pour la healthcheck (et autres utilitaires si nécessaire)
RUN apt-get update && apt-get install -y curl && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier des dépendances et installer
# (Assurez-vous de créer un fichier requirements.txt avec vos dépendances, par exemple :
#  fastapi
#  uvicorn
#  pytest
#  requests
#  pandas
# )
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier l'ensemble du code dans le container
COPY . .

# Exposer le port utilisé par uvicorn
EXPOSE 8000

# Commande par défaut (utilisée si vous lancez le container seul)
CMD ["uvicorn", "Server.Server:app", "--host", "0.0.0.0", "--port", "8000"]