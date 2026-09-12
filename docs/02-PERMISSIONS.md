# Incident 02: Report cannot be saved

**Practice ticket:** A local application can read a sample report but cannot save an update. Investigate the file's access rules and restore its original permissions.

This exercise uses your current Windows account and one newly generated file. Use a local NTFS folder you own and keep the same account throughout. The original ACL backup stays in `.permission-lab/` and is ignored by Git.

## Establish the baseline

In the VS Code PowerShell terminal:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Setup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Check
```

Expected: `READY`, then `PASS: The synthetic report is writable.` Setup creates `.permission-lab/sample-report.txt` and saves its original file ACL. Check attempts a real append to that file.

## Introduce the fault

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Break
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Check
```

Expected: `FAIL: Access denied...`. The script adds an explicit deny for `WriteData` and `AppendData` on the sample file for the current account. It does not deny reading the file or changing its permissions.

## Inspect the evidence

```powershell
Get-Content .\.permission-lab\sample-report.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Inspect
```

Reading should still work. Inspect shows a `Deny` entry for `Current lab account` with write/append rights and `Inherited = False`. That is the deliberate explicit rule introduced by this exercise. Account names are replaced with labels in this view to make screenshots easier to share.

For comparison, Windows also provides:

```powershell
icacls .\.permission-lab\sample-report.txt
```

Its output may show your actual account name or SID. Keep that raw output local or redact it before sharing. Do not change access on other files while following this exercise.

## Restore and verify

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Fix
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Check
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\permissions.ps1 -Action Inspect
```

Expected: `RESTORED`, then `PASS`; the exercise's deny rule is gone. The repair restores the saved original file ACL rather than granting broad access to everyone.

## Explain the diagnosis

An ACL is a list of access rules. In this controlled example, an explicit deny for the current account prevents a write despite inherited permissions. The file can still be read. Testing both operations and inspecting the deny rule supports the diagnosis.

This is a single-account, single-file NTFS exercise. It is not Active Directory, user provisioning, or a demonstration of every Windows permission-precedence case. Record what you actually saw in [the incident report](../cases/02-PERMISSIONS.md).
