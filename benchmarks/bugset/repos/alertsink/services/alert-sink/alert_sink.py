"""alert-sink: the incident trigger log.

Receives Alertmanager webhooks and appends every alert in the payload as one
JSON line to /data/alerts.jsonl (a named Docker volume). That file is what the
incident-diagnosis phase reads to know *that* something went wrong and when.

Also serves, read-only, for the diagnosis machine on the LAN:
  GET /alerts?limit=N   last N alert lines (default: all), application/x-ndjson
  GET /deploys?limit=N  last N lines of the deploy log written by scripts/deploy.sh
  GET /health

Standard library only, so the image stays tiny.
"""

import json
import os
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DATA_DIR = os.getenv("ALERT_SINK_DATA_DIR", "/data")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.jsonl")
DEPLOYS_FILE = os.getenv("DEPLOYS_FILE", "/deploys/deploys.jsonl")
PORT = int(os.getenv("ALERT_SINK_PORT", "9095"))
MAX_BODY = 5 * 1024 * 1024

_write_lock = threading.Lock()


def _now():
    return datetime.now(timezone.utc).isoformat()


def log(event, **fields):
    print(json.dumps({"ts": _now(), "service": "alert-sink", "event": event, **fields}), flush=True)


def records_from_webhook(payload, received_at=None):
    """Flatten one Alertmanager webhook payload into one record per alert."""
    received_at = received_at or _now()
    records = []
    for alert in payload.get("alerts", []):
        labels = alert.get("labels", {})
        records.append({
            "received_at": received_at,
            "status": alert.get("status"),
            "alertname": labels.get("alertname"),
            "severity": labels.get("severity"),
            "starts_at": alert.get("startsAt"),
            "ends_at": alert.get("endsAt"),
            "fingerprint": alert.get("fingerprint"),
            "labels": labels,
            "annotations": alert.get("annotations", {}),
            "generator_url": alert.get("generatorURL"),
            "group_key": payload.get("groupKey"),
            "receiver": payload.get("receiver"),
        })
    return records


def append_records(records, path=ALERTS_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _write_lock, open(path, "a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def tail_lines(path, limit=None):
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except FileNotFoundError:
        return []
    return lines[-limit:] if limit else lines


class Handler(BaseHTTPRequestHandler):
    server_version = "alert-sink/1.0"

    def _send(self, status, body, content_type="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlparse(self.path).path != "/alertmanager":
            return self._send(404, '{"error": "not found"}')
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._send(400, '{"error": "bad content length"}')
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return self._send(400, '{"error": "invalid json"}')
        records = records_from_webhook(payload)
        append_records(records)
        for record in records:
            log("alert_stored", alertname=record["alertname"], status=record["status"],
                fingerprint=record["fingerprint"])
        return self._send(200, json.dumps({"stored": len(records)}))

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/health":
            return self._send(200, '{"status": "ok"}')
        files = {"/alerts": ALERTS_FILE, "/deploys": DEPLOYS_FILE}
        if url.path not in files:
            return self._send(404, '{"error": "not found"}')
        try:
            limit = int(parse_qs(url.query).get("limit", ["0"])[0]) or None
        except ValueError:
            return self._send(400, '{"error": "limit must be an integer"}')
        return self._send(200, "".join(tail_lines(files[url.path], limit)), "application/x-ndjson")

    def log_message(self, fmt, *args):
        # Health probes every few seconds would drown the useful lines.
        if "/health" not in (str(args[0]) if args else ""):
            log("http", line=fmt % args)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log("startup", port=PORT, alerts_file=ALERTS_FILE, deploys_file=DEPLOYS_FILE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
