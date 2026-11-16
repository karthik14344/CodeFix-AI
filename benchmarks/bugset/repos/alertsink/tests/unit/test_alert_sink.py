"""alert-sink webhook flattening, persistence and read-back."""

import importlib.util
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "services" / "alert-sink" / "alert_sink.py"
spec = importlib.util.spec_from_file_location("alert_sink", SCRIPT)
alert_sink = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alert_sink)

PAYLOAD = {
    "receiver": "alert-sink",
    "status": "firing",
    "groupKey": '{}:{alertname="ServiceDown"}',
    "alerts": [
        {
            "status": "firing",
            "labels": {"alertname": "ServiceDown", "severity": "critical", "job": "flask-app"},
            "annotations": {"summary": "Prediction service is not scrapeable"},
            "startsAt": "2026-09-22T10:00:00Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "fingerprint": "abc123",
            "generatorURL": "http://prometheus:9090/graph",
        },
        {
            "status": "resolved",
            "labels": {"alertname": "PredictionErrors", "severity": "critical"},
            "annotations": {},
            "fingerprint": "def456",
        },
    ],
}


def test_one_record_per_alert():
    records = alert_sink.records_from_webhook(PAYLOAD, received_at="t0")
    assert [r["alertname"] for r in records] == ["ServiceDown", "PredictionErrors"]
    assert records[0]["status"] == "firing"
    assert records[0]["severity"] == "critical"
    assert records[0]["received_at"] == "t0"
    assert records[1]["status"] == "resolved"


def test_http_round_trip(tmp_path, monkeypatch):
    alerts = tmp_path / "alerts.jsonl"
    deploys = tmp_path / "deploys.jsonl"
    deploys.write_text('{"git_sha": "a"}\n{"git_sha": "b"}\n')
    monkeypatch.setattr(alert_sink, "ALERTS_FILE", str(alerts))
    monkeypatch.setattr(alert_sink, "DEPLOYS_FILE", str(deploys))
    original_append = alert_sink.append_records
    monkeypatch.setattr(alert_sink, "append_records", lambda records: original_append(records, str(alerts)))

    server = ThreadingHTTPServer(("127.0.0.1", 0), alert_sink.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        request = urllib.request.Request(
            f"{base}/alertmanager", data=json.dumps(PAYLOAD).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        assert json.load(urllib.request.urlopen(request)) == {"stored": 2}

        lines = alerts.read_text().splitlines()
        assert len(lines) == 2 and json.loads(lines[0])["alertname"] == "ServiceDown"

        last = urllib.request.urlopen(f"{base}/alerts?limit=1").read().decode().splitlines()
        assert json.loads(last[0])["alertname"] == "PredictionErrors"

        deploy_lines = urllib.request.urlopen(f"{base}/deploys?limit=1").read().decode().splitlines()
        assert json.loads(deploy_lines[0]) == {"git_sha": "b"}
    finally:
        server.shutdown()
