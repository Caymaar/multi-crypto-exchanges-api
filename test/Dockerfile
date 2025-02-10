# Utilisation d'une image légère avec Python et uv
FROM python:3.11-slim

# Installer uv
RUN pip install uv

# Copier les fichiers de tests
WORKDIR /tests
COPY . /tests

# Installer les dépendances de test
RUN uv venv

# Attendre que le serveur soit prêt, puis exécuter les tests
CMD ["sh", "-c", "sleep 5 && uv run pytest --maxfail=5 --disable-warnings"]