# Incident 01: Client cannot connect

**Practice ticket:** A local support application was working, but its client now cannot connect. Determine which setting changed and restore access.

## Establish the baseline

Keep `py lab.py serve` running in terminal 1. In terminal 2:

```powershell
py lab.py check
```

Expected: `PASS` with HTTP 200. If this already fails, resolve setup before introducing the exercise fault.

## Introduce the fault and observe it

```powershell
py lab.py break connection
py lab.py check
```

Expected: `FAIL`, usually reporting a refused connection on port 8766. Only the client configuration changed. If another application uses that port, you may see a timeout or an unexpected-response message instead; record the actual result.

## Investigate before repairing

```powershell
Get-Content .\.lab\client.json
Get-Content .\.lab\server.json
Test-NetConnection 127.0.0.1 -Port 8766 -InformationLevel Quiet
Test-NetConnection 127.0.0.1 -Port 8765 -InformationLevel Quiet
```

The default client now uses 8766 while the service listens on 8765. A TCP check on the server's actual port should return `True`. The wrong port usually returns `False`. A successful TCP check alone does not identify the application listening there.

If you selected a different setup port, use that port and its next number instead. Take a screenshot showing the configuration mismatch and connection checks.

## Fix and verify

```powershell
py lab.py fix connection
py lab.py check
```

The fix copies the configured server port back into the client's configuration. Expected: `PASS` with HTTP 200, without restarting the server.

## Explain the diagnosis

The client was sending requests to the wrong local port. Comparing both configurations and checking the actual listener separated a client setting error from a stopped server. `127.0.0.1` is a numeric loopback address, so this exercise is not a DNS or internet-connectivity test.

Complete [the incident record](../cases/01-CONNECTION.md) using your own observed output. Explain why changing the client setting was justified by the evidence.
