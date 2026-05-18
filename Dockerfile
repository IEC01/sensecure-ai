FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ml/ ./ml/
COPY capture/ ./capture/
COPY data/ ./data/

ENV BASE=/app

CMD ["python3", "backend/api.py"]
