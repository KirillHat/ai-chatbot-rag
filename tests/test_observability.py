"""Observability middleware behavior."""

from __future__ import annotations


def test_request_id_is_echoed(client):
    res = client.get("/health", headers={"X-Request-ID": "test-rid-123"})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == "test-rid-123"


def test_metrics_endpoint_exposes_counters(client):
    client.get("/health")
    res = client.get("/metrics")
    assert res.status_code == 200
    body = res.text
    assert "app_http_requests_total" in body
    assert 'path="/health"' in body
