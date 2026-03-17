FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le projet (y compris templates, static, app.py)
COPY . .

# Création de la base de données au démarrage si elle n'existe pas
EXPOSE 5000

CMD ["python", "app.py"]