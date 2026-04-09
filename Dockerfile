FROM python:3.12-slim-bookworm 

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN apt-get update && apt-get install -y --only-upgrade \
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

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]