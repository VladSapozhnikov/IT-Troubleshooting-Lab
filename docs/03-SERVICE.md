# Incident 03: Service reachable but unavailable

**Practice ticket:** The application returns an error even though the network connection succeeds. Determine whether the failure is at the connection or application layer.

## Establish the baseline

With the local server running, make sure incident 01 is repaired:

```powershell
py lab.py fix connection
py lab.py fix service
py lab.py check
```

Expected: `PASS` with HTTP 200.

## Introduce the application fault

```powershell
py lab.py break service
py lab.py check
```

Expected: TCP connects, but the application responds with **HTTP 503 (maintenance)**. The script intentionally changed the lab's maintenance setting. It did not stop the server process.

## Compare network and application evidence

```powershell
Test-NetConnection 127.0.0.1 -Port 8765 -InformationLevel Quiet
Get-Content .\.lab\service-state.json
Get-Content .\.lab\events.jsonl -Tail 8
```

Use your selected server port if you changed the default. Expected: the TCP test returns `True`, the configuration says `"maintenance": true`, and a recent `http.response` event records `"status": 503` with `"state": "maintenance"`.

You can also refresh [the local page](http://127.0.0.1:8765) to see the service state. The log timestamps use UTC. Capture the HTTP failure, successful TCP check, and relevant configuration/log entry.

## Repair and verify

```powershell
py lab.py fix service
py lab.py check
Get-Content .\.lab\events.jsonl -Tail 4
```

Expected: HTTP 200 returns, and a new log entry records the healthy response. The server reads the setting for each request, so this repair does not need a restart.

## Explain the diagnosis

The successful TCP check established that the local listener was reachable. It did not establish that the application was healthy. The HTTP 503 response, maintenance setting, and matching log entry identified the simulated application-level cause.

These are synthetic application logs, not real Windows Event Viewer records. Record your actual observations and the before/after UTC timestamps in [the incident report](../cases/03-SERVICE.md).
