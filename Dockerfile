
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.12-slim-bookworm

WORKDIR /app


RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --only-upgrade \
      libssl3t64=3.5.5-1~deb13u2 \
      openssl=3.5.5-1~deb13u2 \
      openssl-provider-legacy=3.5.5-1~deb13u2 \
    && apt-get remove --purge -y \
      ncurses-bin \
      udev \
    2>/dev/null || true \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*


RUN useradd -m -r appuser


COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .


ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/home/appuser/.local/lib/python3.12/site-packages
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000


USER appuser

CMD ["python", "app.py"]