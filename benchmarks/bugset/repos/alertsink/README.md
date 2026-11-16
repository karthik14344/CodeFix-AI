# alertsink

The incident-trigger log from **MLOps-Incident-Diagnosis**, one of the team's own MLOps
projects, vendored here as a third sample repository alongside `pyshop` and `textkit`.

Unlike those two — which were written for this benchmark — this is production code that already
existed, with the test file carried over verbatim. It is included because a bug set made only of
purpose-built repositories is open to the objection that the agents are being graded on code
shaped to suit them.

## What it does

`alert_sink.py` receives Alertmanager webhooks over HTTP and appends every alert in the payload
as one JSON line to `alerts.jsonl`. It also serves that file, and a deploy log, read-only:

| Route | Purpose |
|---|---|
| `POST /alertmanager` | Store every alert in the webhook payload |
| `GET /alerts?limit=N` | The last N stored alerts, as `application/x-ndjson` |
| `GET /deploys?limit=N` | The last N deploy records |
| `GET /health` | Liveness probe |

## Why this module

It is **standard library only** — its own docstring says so, to keep the container image small.
That makes it runnable here with no extra dependencies, unlike the rest of the project, whose
tests pull in `mlflow`, `scikit-learn`, `numpy` and a live Flask app. The directory layout is
preserved (`services/alert-sink/`, `tests/unit/`) because the test locates the module by relative
path, so the file is unmodified from the original project.

## Tests

`tests/unit/test_alert_sink.py`, also verbatim: it checks webhook flattening, and runs a real
`ThreadingHTTPServer` on a loopback port to exercise the round trip through POST and both GET
routes.

```bash
pytest tests/unit/test_alert_sink.py
```

Source: `MLOps-Incident-Diagnosis/services/alert-sink/` and `tests/unit/`.
