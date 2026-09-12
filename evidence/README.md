# Evidence checklist

No owner screenshots or results have been supplied yet. Add only captures from your own run, and label any later automated-test output separately.

| Case | Capture before repair | Capture after repair |
| --- | --- | --- |
| 01 | Failed client check plus client/server port mismatch | Successful HTTP 200 check |
| 02 | Access-denied check plus explicit deny in Inspect | Successful write and restored access rules |
| 03 | HTTP 503, successful TCP check, and maintenance log | HTTP 200 and healthy log entry |

Suggested filenames: `01-connection-before.png`, `01-connection-after.png`, `02-permissions-before.png`, `02-permissions-after.png`, `03-service-before.png`, `03-service-after.png`.

Crop screenshots to the relevant commands and output. Exclude account names, unrelated terminal tabs, and private paths when they are not needed. Do not upload `.permission-lab/original-acl.json`; it includes the local account SID and saved ACL. The purpose-built Python log contains synthetic lab events only.

Send the six images and short observations to your assistant, or add reviewed images here. Fill the matching case report with actual results, then change its status from pending to complete. A GitHub Actions run verifies the toolkit but does not count as you completing the exercise.
