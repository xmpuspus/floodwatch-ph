FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Makefile .
COPY floodwatch_ph/ floodwatch_ph/
COPY model/ model/
COPY scripts/ scripts/
COPY tests/ tests/

# Deterministic, no network, no GPU: reproduce the recurrence classifier
# from the committed embeddings cache and assert its canonical hash.
CMD ["make", "hash-verify"]
