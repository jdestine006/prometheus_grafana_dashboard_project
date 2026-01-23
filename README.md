# Ops Pulse – Local Observability (Prometheus + Grafana)

A self-hosted observability mini-project using Prometheus + Grafana to monitor a Python FastAPI app with RED metrics (Rate, Errors, Duration), SLO-style panels, and a basic alert.

## What this shows
- **Prometheus** scraping application metrics from `/metrics`
- **Grafana** dashboard with:
  - Requests/sec (RPS)
  - 5xx error rate %
  - Success rate %
  - Latency p95 / p99
  - RPS by status
- **Dashboard variable** to filter by endpoint path (`path`)
- **Alert** on p95 latency (threshold-based)

---

## Prerequisites (macOS)
- Homebrew
- Python 3
------------------------------------------------------------------------------------------------------------------------
Install services (skip if already installed):
```bash
brew install prometheus grafana
````
------------------------------------------------------------------------------------------------------------------------

Start Services
````
brew services start prometheus
brew services start grafana
````

Prometheus UI: http://localhost:9090
Grafana UI: http://localhost:3000
------------------------------------------------------------------------------------------------------------------------

App Setup

From the project folder
````
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn prometheus-client
````

Run the App
````
uvicorn app:app --host 127.0.0.1 --port 8000
````
App Health: http://localhost:8000/health
Metrics: http://localhost:8000/metrics
------------------------------------------------------------------------------------------------------------------------

Prometheus scrape config

Edit:

Intel: /usr/local/etc/prometheus.yml
Apple Silicon: /opt/homebrew/etc/prometheus.yml

Ensure you have:
````
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["127.0.0.1:9090"]

  - job_name: "ops-pulse-app"
    static_configs:
      - targets: ["127.0.0.1:8000"]
````
------------------------------------------------------------------------------------------------------------------------

Restart Prometheus:
````
brew services restart prometheus
````

Verify Targets are UP: http://localhost:9090/targets
------------------------------------------------------------------------------------------------------------------------

Generate test traffic

In a separate terminal:
````
for i in {1..800}; do curl -s http://127.0.0.1:8000/work > /dev/null; sleep 0.02; done
````
------------------------------------------------------------------------------------------------------------------------
Grafana setup

Login: http://localhost:3000

Add Prometheus datasource:

URL: http://localhost:9090

------------------------------------------------------------------------------------------------------------------------


Build/import the dashboard.

Recommended dashboard panels (PromQL)

RPS
````
sum(rate(http_requests_total{path=~"${path:regex}"}[5m]))

````
5xx Error Rate (%)
````
100 *
sum(rate(http_requests_total{status=~"5..", path=~"${path:regex}"}[5m]))
/
clamp_min(sum(rate(http_requests_total{path=~"${path:regex}"}[5m])), 1e-9)

````
Success Rate (%)
````
100 - (
  100 *
  sum(rate(http_requests_total{status=~"5..", path=~"${path:regex}"}[5m]))
  /
  clamp_min(sum(rate(http_requests_total{path=~"${path:regex}"}[5m])), 1e-9)
)

````
Latency p95
````
histogram_quantile(
  0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket{path=~"${path:regex}"}[5m]))
)

````
Latency p99
````
histogram_quantile(
  0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket{path=~"${path:regex}"}[5m]))
)

````
RPS by Status
````
sum by (status) (rate(http_requests_total{path=~"${path:regex}"}[5m]))

````
------------------------------------------------------------------------------------------------------------------------

Dashboard variable (path)

Create a Grafana variable:

Name: path

Type: Query

Query (recommended):

````
label_values(http_requests_total{job="ops-pulse-app"}, path)

````

Include All: ✅

Custom all value: .*

Use in queries as:

path=~"${path:regex}"
------------------------------------------------------------------------------------------------------------------------

Alert (example)

Create an alert rule on p95 latency:

Evaluate every: 1m

For: 5m

Trigger when p95 > 0.35s

Label: severity=warning

------------------------------------------------------------------------------------------------------------------------

Troubleshooting

Only Prometheus target shows up:

Confirm app is running and /metrics responds

Confirm Prometheus config includes ops-pulse-app

Restart Prometheus and re-check /targets

Grafana variable only shows All:

Ensure custom all value is set to .*

------------------------------------------------------------------------------------------------------------------------

Generate traffic so the label exists in the time window
````

---

## Optional: add a simple `run.sh` for one-command startup
Create `run.sh` at repo root:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Starting Prometheus + Grafana via Homebrew services..."
brew services start prometheus >/dev/null 2>&1 || true
brew services start grafana >/dev/null 2>&1 || true

echo "Starting app..."
source .venv/bin/activate
exec uvicorn app:app --host 127.0.0.1 --port 8000
````
Make it executable:
````
chmod +x run.sh

````

Run it:
````
./run.sh

````

