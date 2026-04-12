FROM python:3.12-slim-bookworm 

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. CORRECTION (DS-0029) : Ajout de --no-install-recommends
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade \
      libssl3t64=3.5.5-1~deb13u2 \
      openssl=3.5.5-1~deb13u2 \
      openssl-provider-legacy=3.5.5-1~deb13u2 \
    && apt-get remove --purge -y \
      ncurses-bin \
      udev \
    2>/dev/null || true \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. CORRECTION (DS-0002) : Création d'un utilisateur sans privilèges
RUN useradd -m -r appuser

# On copie le code source en donnant la propriété des fichiers à notre nouvel utilisateur
COPY --chown=appuser:appuser . .

EXPOSE 5000

# On indique à Docker d'utiliser cet utilisateur pour la suite
USER appuser

CMD ["python", "app.py"]