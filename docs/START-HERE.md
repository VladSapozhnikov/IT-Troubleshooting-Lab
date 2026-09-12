# Start here: Windows and VS Code

## 1. Open the correct folder

Download and extract the repository. In VS Code select **File > Open Folder** and choose the folder that directly contains `lab.py`, `scripts`, and `README.md`.

In a new PowerShell terminal, check:

```powershell
Test-Path .\lab.py
py --version
```

The first command should say `True`; Python should be 3.10 or newer. If the first command says `False`, open the inner extracted folder before continuing.

## 2. Start the practice service

```powershell
py lab.py setup
py lab.py serve
```

Setup creates the example files. Serve runs the small local application and prints its address. Leave this terminal open. If you close it or press Ctrl+C, the application stops.

## 3. Open a second terminal

Select **Terminal > New Terminal**. Run:

```powershell
py lab.py check
```

Expected: `PASS` and `HTTP 200`. This is your working baseline. Capture it before introducing a fault.

Complete [connection troubleshooting](01-CONNECTION.md), [file permissions](02-PERMISSIONS.md), and [application health](03-SERVICE.md) in that order. Run one command at a time. Commands marked as the broken check are expected to fail; this is the symptom you investigate.

## If the port is already occupied

Stop any earlier copy of this lab with Ctrl+C in its own terminal. Do not stop an unfamiliar process. If the port is still occupied, with this lab stopped run:

```powershell
py lab.py setup --port 8877
py lab.py serve
```

Use port `8877` for the server and `8878` for the deliberately wrong port throughout the walkthrough. The check/fix commands read the selected port automatically. No firewall or network-adapter changes are part of this lab.

## How PowerShell scripts are launched

The walkthroughs use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...` to run these local lab scripts in a separate process. That option applies to the launched process; it does not set a permanent system policy. If Windows reports an organization policy restriction, stop and share the error rather than changing system settings.

## Reset an exercise

- Restore a client port: `py lab.py fix connection`
- Clear simulated maintenance: `py lab.py fix service`
- Restore the sample report's original permissions:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Fix
```

`py lab.py setup` preserves an existing exercise's state. The permissions Setup action also preserves its saved original ACL, even when repeated during a fault.

When finished, run the three fixes above for exercises you initialized, verify success, then stop the service with Ctrl+C. Generated data stays within this project folder. The lab makes no persistent service installation.
