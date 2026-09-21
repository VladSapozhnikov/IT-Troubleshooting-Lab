# IT Troubleshooting Lab

This is my personal Windows troubleshooting project. I wanted something I could tinker with: break a setting, figure out why something stopped working, and get it running again.

The lab brings together Python, PowerShell, and three repeatable troubleshooting scenarios. My focus is understanding what the evidence tells me, choosing a specific fix, and checking that it actually solves the problem.

## What I'm exploring

| Scenario | What's wrong | What it demonstrates |
| --- | --- | --- |
| [Client cannot connect](docs/01-CONNECTION.md) | Client and server use different ports | Comparing configurations and testing TCP connectivity |
| [Report cannot be saved](docs/02-PERMISSIONS.md) | An explicit file-access rule blocks writing | Inspecting NTFS permissions and restoring the original access rules |
| [Service reachable but unavailable](docs/03-SERVICE.md) | The application returns HTTP 503 while TCP still connects | Separating a connection problem from an application problem using logs |

I chose these scenarios because similar symptoms can have different causes. A failed request might come from the connection settings, file access, or the application itself. The exercises make those differences visible on one computer.

**Tools:** Python standard library, Windows PowerShell, NTFS access controls, HTTP, and GitHub Actions.

## Run it in VS Code

Requirements: Windows 11, Windows PowerShell, and Python 3.10 or newer. For the permission exercise, use a local NTFS folder owned by your Windows account. Run the commands in an ordinary user terminal. The Python program uses only the standard library.

1. Download this repository with **Code > Download ZIP** and extract it.
2. Open the inner folder containing **`lab.py`** in VS Code.
3. Select **Terminal > New Terminal** and run:

```powershell
py lab.py setup
py lab.py serve
```

4. Keep that terminal open. Open a second terminal in the same folder and run:

```powershell
py lab.py check
```

Expected baseline: `PASS: TCP connected to port 8765; application returned HTTP 200 (healthy).`

Open [the local lab page](http://127.0.0.1:8765) to see the service in your browser. The [setup guide](docs/START-HERE.md) includes troubleshooting steps and instructions for using a different port.

## Try a fault and repair

With the server still running, use the second terminal:

```powershell
py lab.py break connection
py lab.py check
py lab.py diagnose
py lab.py fix connection
py lab.py check
```

The first check should fail because the client points to the wrong port. `diagnose` displays the configurations and recent lab events. After the fix, the check should return HTTP 200 again. The individual walkthroughs explain how to investigate each scenario before applying its repair.

## How the environment works

The Python program provides a small HTTP service bound to `127.0.0.1` and a separate client check. Two configuration files let the client point to the wrong port without changing the server. A service-state file introduces a controlled HTTP 503 response, and a local event log records the application's responses.

The PowerShell exercise creates a sample report, saves its original permissions, and introduces an explicit write-deny rule for the current account. The repair restores the saved permissions on that file. All scenarios use generated practice data inside the project folder.

| Location | Purpose |
| --- | --- |
| `lab.py` | Local service, client checks, and configuration exercises |
| `scripts/permissions.ps1` | Windows file-access exercise |
| `docs/` | Walkthroughs, setup, and testing notes |
| `cases/` | Templates for my troubleshooting notes |
| `evidence/` | Screenshot checklist and a place for captures |
| `.lab/`, `.permission-lab/` | Generated local data; ignored by Git |

## Tests

The test suite includes 10 Python behavior tests and a Windows permission test. Together they check successful connections, introduced faults, error handling, recovery, and restoration of the original file-access rules.

GitHub Actions runs the checks on Windows Server 2022 with Python 3.13. See the [workflow results](https://github.com/VladSapozhnikov/IT-Troubleshooting-Lab/actions/workflows/verify.yml) and [verification notes](docs/VERIFICATION.md) for details.

To run them locally:

```powershell
py -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_permissions.ps1
```

## Project notes

My personal case notes and screenshots are still to be added. Each [case template](cases/) has space for the symptom, commands, diagnosis, fix, and retest. The [screenshot checklist](evidence/README.md) outlines the before-and-after captures.

This is a local practice environment with deliberately introduced faults. The file-permission exercise focuses on one account and one generated file; the web service is intended for local experimentation.

## References

- [Microsoft: Test-NetConnection](https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection) for TCP diagnostics.
- [Microsoft: icacls](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls) for inspecting Windows file permissions.
- [Microsoft: FileSystemAccessRule](https://learn.microsoft.com/en-us/dotnet/api/system.security.accesscontrol.filesystemaccessrule) for per-account allow/deny rules.
- [Python: http.server](https://docs.python.org/3/library/http.server.html) for the local test service. It is a learning service, not a public deployment.
