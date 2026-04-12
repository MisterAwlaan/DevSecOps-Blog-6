
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

COPY requirements.txt .


RUN pip install --no-cache-dir --target=/app/libs -r requirements.txt

FROM gcr.io/distroless/python3-debian12

WORKDIR /app


COPY --from=builder /app/libs /app/libs


COPY . .


ENV PYTHONPATH=/app/libs

EXPOSE 5000

# On passe sur l'utilisateur sécurisé
USER nonroot

CMD ["app.py"]