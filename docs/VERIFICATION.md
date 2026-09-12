# Toolkit verification

## Local preparation

The 10 Python tests passed under Python 3.12 on Linux. They exercise real loopback HTTP requests, healthy responses, wrong-port failure and repair, HTTP 503 and recovery, controlled invalid-configuration errors, restricted HTTP routes, repeat setup, invalid port handling, unrelated-folder protection, and startup from a different directory.

No Windows shell is available in that local preparation environment. The separate Windows check runs in [GitHub Actions](https://github.com/VladSapozhnikov/IT-Troubleshooting-Lab/actions/workflows/verify.yml); inspect its recorded result rather than assuming success.

## Windows automation

The workflow targets Windows Server 2022 with Python 3.13 and Windows PowerShell. The ACL test copies the permissions exercise into a temporary folder, verifies write success, introduces a real deny rule, confirms a failed write, repeats setup without overwriting the original backup, restores the permissions, verifies write success, and compares the original and restored DACL. Cleanup restores permissions before removing only the test's temporary folder.

Hosted Windows runner results are not a claim of Windows 11 execution on the owner's laptop. Local drive format, account policy, and security software can differ.

## Run the checks locally

From the repository root:

```powershell
py -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_permissions.ps1
```

The tests create their own temporary workspaces. They do not fill the owner incident reports or publish screenshots. Those require the owner's actual exercise results.
