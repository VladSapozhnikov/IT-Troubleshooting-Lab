<# Real Windows ACL regression check in a disposable copy of the exercise. #>
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('it-lab-test-' + [Guid]::NewGuid().ToString('N'))
$testScript = Join-Path $testRoot 'scripts\permissions.ps1'
$testShell = (Get-Process -Id $PID).Path
[void](New-Item -ItemType Directory -Path (Split-Path $testScript -Parent) -Force)
Copy-Item -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts\permissions.ps1') -Destination $testScript

function Invoke-TestAction([string]$TestAction, [int]$Expected) {
    $testOutput = & $testShell -NoProfile -ExecutionPolicy Bypass -File $testScript -Action $TestAction 2>&1
    if ($LASTEXITCODE -ne $Expected) {
        throw "$TestAction expected exit $Expected, received $LASTEXITCODE. $testOutput"
    }
    Write-Output "$TestAction returned expected exit $Expected"
}

try {
    Invoke-TestAction 'Setup' 0
    Invoke-TestAction 'Check' 0
    $testFile = Join-Path $testRoot '.permission-lab\sample-report.txt'
    $testSection = [System.Security.AccessControl.AccessControlSections]::Access
    $testBefore = (Get-Acl -LiteralPath $testFile).GetSecurityDescriptorSddlForm($testSection)
    Invoke-TestAction 'Break' 0
    Invoke-TestAction 'Check' 1
    Invoke-TestAction 'Inspect' 0
    Invoke-TestAction 'Setup' 0
    Invoke-TestAction 'Check' 1
    Invoke-TestAction 'Fix' 0
    Invoke-TestAction 'Check' 0
    $testAfter = (Get-Acl -LiteralPath $testFile).GetSecurityDescriptorSddlForm($testSection)
    if ($testBefore -ne $testAfter) { throw 'The original DACL was not restored exactly.' }
    Write-Output 'PASS: Windows write succeeds, denial is enforced, setup preserves the backup, and repair restores the original DACL.'
} finally {
    if (Test-Path -LiteralPath (Join-Path $testRoot '.permission-lab\original-acl.json')) {
        & $testShell -NoProfile -ExecutionPolicy Bypass -File $testScript -Action Fix | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Cleanup could not restore the lab ACL. Inspect $testRoot" }
    }
    Remove-Item -LiteralPath $testRoot -Recurse -Force
}
