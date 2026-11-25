#!/usr/bin/env python3
"""Validação rápida da stack de monitoramento (localhost)."""
from __future__ import annotations

import json
import sys
import urllib.request

BASE_PROM = "http://127.0.0.1:9090"
BASE_GRAF = "http://127.0.0.1:3000"
BASE_ZBX = "http://127.0.0.1:8081"


def get(url: str, auth: tuple[str, str] | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url)
    if auth:
        import base64

        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []

    code, body = get(f"{BASE_PROM}/-/healthy")
    print(f"prometheus_healthy={code} {body.strip()}")
    if code != 200:
        errors.append("prometheus unhealthy")

    code, body = get(f"{BASE_PROM}/api/v1/targets")
    data = json.loads(body)
    targets = data["data"]["activeTargets"]
    for t in targets:
        job = t["labels"].get("job")
        health = t["health"]
        err = (t.get("lastError") or "")[:120]
        print(f"target job={job} health={health} err={err}")
        if health != "up":
            errors.append(f"target down: {job}")

    for q in (
        "up",
        "pg_up",
        "node_memory_MemTotal_bytes",
        "probe_success",
        "count(container_cpu_usage_seconds_total)",
    ):
        code, body = get(f"{BASE_PROM}/api/v1/query?query={urllib.request.quote(q)}")
        result = json.loads(body)["data"]["result"]
        print(f"query {q} series={len(result)}")
        if not result:
            errors.append(f"empty query: {q}")

    code, body = get(f"{BASE_GRAF}/api/health")
    print(f"grafana_health={code} {body.strip()}")
    if code != 200:
        errors.append("grafana unhealthy")

    code, body = get(f"{BASE_GRAF}/api/datasources", auth=("admin", "grafana_lab_change_me"))
    ds = json.loads(body)
    print(f"grafana_datasources={[d['name'] for d in ds]}")
    if not any(d.get("type") == "prometheus" for d in ds):
        errors.append("grafana missing prometheus datasource")

    code, body = get(f"{BASE_GRAF}/api/search?type=dash-db", auth=("admin", "grafana_lab_change_me"))
    dashes = json.loads(body)
    titles = sorted(d["title"] for d in dashes)
    print(f"grafana_dashboards={titles}")
    expected = {
        "Host Debian",
        "Containers Docker",
        "WarehouseFlow",
        "PostgreSQL",
        "Monitoramento",
    }
    missing = expected - set(titles)
    if missing:
        errors.append(f"missing dashboards: {missing}")

    code, _ = get(BASE_ZBX + "/")
    print(f"zabbix_web={code}")
    if code != 200:
        errors.append("zabbix web not 200")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
