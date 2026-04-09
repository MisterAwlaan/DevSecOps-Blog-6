FROM python:3.12-slim-bookworm 

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie uniquement ce qui est nécessaire
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]