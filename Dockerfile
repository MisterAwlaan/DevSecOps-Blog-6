# --- BUILDER ---
FROM python:3.12-slim-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
# On installe les libs dans un dossier qu'on peut déplacer
RUN pip install --no-cache-dir --target=/app/libs -r requirements.txt

# --- RUNNER ---
FROM gcr.io/distroless/python3-debian12
WORKDIR /app

# IMPORTANT : On donne la propriété à l'utilisateur nonroot durant la copie
COPY --from=builder --chown=nonroot:nonroot /app/libs /app/libs
COPY --chown=nonroot:nonroot . .

# On configure Python pour qu'il voit les libs
ENV PYTHONPATH=/app/libs
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
USER nonroot

# Sur Distroless Debian 12, le chemin est souvent /usr/bin/python3
ENTRYPOINT ["python", "app.py"]