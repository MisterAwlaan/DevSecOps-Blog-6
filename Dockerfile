FROM python:3.12-slim-bookworm AS builder

WORKDIR /app


COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM gcr.io/distroless/python3-debian12

WORKDIR /app


COPY --from=builder /root/.local /root/.local


COPY . .


ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.12/site-packages

EXPOSE 5000


USER nonroot

CMD ["app.py"]