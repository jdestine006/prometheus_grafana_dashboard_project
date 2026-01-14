from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = FastAPI()

# RED-style metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/work")
def work():
    method = "GET"
    path = "/work"

    with HTTP_LATENCY.labels(method=method, path=path).time():
        # simulate work
        time.sleep(random.uniform(0.02, 0.25))

        # simulate occasional server error
        if random.random() < 0.08:
            HTTP_REQUESTS.labels(method=method, path=path, status="500").inc()
            return Response(content='{"error":"simulated"}', media_type="application/json", status_code=500)

        HTTP_REQUESTS.labels(method=method, path=path, status="200").inc()
        return {"result": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
