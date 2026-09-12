<# Windows NTFS exercise. Only modifies its own generated report file. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Setup', 'Break', 'Check', 'Inspect', 'Fix')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'This exercise requires Windows and a local NTFS drive.'
    }
    $labRoot = Split-Path $PSScriptRoot -Parent
    $labFolder = Join-Path $labRoot '.permission-lab'
    $labFile = Join-Path $labFolder 'sample-report.txt'
    $labMarker = Join-Path $labFolder 'marker.txt'
    $labBackup = Join-Path $labFolder 'original-acl.json'
    $labIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $labSection = [System.Security.AccessControl.AccessControlSections]::Access
    $labTag = 'it-troubleshooting-permissions-v1'

    if (Test-Path -LiteralPath $labFolder) {
        if ((Get-Item -LiteralPath $labFolder -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Linked lab folders are not supported.'
        }
        if (!(Test-Path -LiteralPath $labMarker) -or (Get-Content -LiteralPath $labMarker -Raw).Trim() -ne $labTag) {
            throw 'Unrecognized permissions workspace. Use a fresh project download.'
        }
        foreach ($labPath in @($labFile, $labMarker, $labBackup)) {
            if ((Test-Path -LiteralPath $labPath) -and ((Get-Item -LiteralPath $labPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw 'Linked lab files are not supported.'
            }
        }
    } elseif ($Action -eq 'Setup') {
        [void](New-Item -ItemType Directory -Path $labFolder)
        Set-Content -LiteralPath $labMarker -Value $labTag -Encoding UTF8
    } else {
        throw 'Run this script with -Action Setup first.'
    }

    if ($Action -eq 'Setup') {
        if (!(Test-Path -LiteralPath $labFile)) {
            if (Test-Path -LiteralPath $labBackup) { throw 'The report was removed. Use a fresh project download.' }
            Set-Content -LiteralPath $labFile -Value 'Synthetic report for a local permissions exercise.' -Encoding UTF8
        }
        if (!(Test-Path -LiteralPath $labBackup)) {
            $labAcl = Get-Acl -LiteralPath $labFile
            @{
                sid = $labIdentity.Value
                sddl = $labAcl.GetSecurityDescriptorSddlForm($labSection)
            } | ConvertTo-Json | Set-Content -LiteralPath $labBackup -Encoding UTF8
        }
        Write-Output 'READY: Synthetic report created and original file permissions saved locally.'
        exit 0
    }

    $labOriginal = Get-Content -LiteralPath $labBackup -Raw | ConvertFrom-Json
    if ($labOriginal.sid -ne $labIdentity.Value) { throw 'Use the same Windows account that created this exercise.' }

    switch ($Action) {
        'Break' {
            $labAcl = Get-Acl -LiteralPath $labFile
            $labRights = [System.Security.AccessControl.FileSystemRights]::WriteData -bor [System.Security.AccessControl.FileSystemRights]::AppendData
            $labRule = [System.Security.AccessControl.FileSystemAccessRule]::new(
                $labIdentity, $labRights, [System.Security.AccessControl.AccessControlType]::Deny
            )
            $labAcl.AddAccessRule($labRule)
            Set-Acl -LiteralPath $labFile -AclObject $labAcl
            Write-Output 'INTRODUCED: Write denied on the synthetic report. Run -Action Check.'
        }
        'Check' {
            try {
                [IO.File]::AppendAllText($labFile, "Verified write from the local lab.`r`n")
                Write-Output 'PASS: The synthetic report is writable.'
            } catch {
                $labCause = $_.Exception
                while ($null -ne $labCause.InnerException) { $labCause = $labCause.InnerException }
                if ($labCause -is [UnauthorizedAccessException]) {
                    Write-Output 'FAIL: Access denied while writing the synthetic report. Inspect its ACL.'
                    exit 1
                }
                throw
            }
        }
        'Inspect' {
            # Label the current account instead of publishing its username/SID.
            $labAcl = Get-Acl -LiteralPath $labFile
            $labRules = $labAcl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
            $labRules | ForEach-Object {
                [pscustomobject]@{
                    Account = $(if ($_.IdentityReference.Value -eq $labIdentity.Value) { 'Current lab account' } else { 'Other inherited or system account' })
                    Type = $_.AccessControlType
                    Rights = $_.FileSystemRights
                    Inherited = $_.IsInherited
                }
            } | Format-Table -AutoSize
        }
        'Fix' {
            $labAcl = Get-Acl -LiteralPath $labFile
            $labAcl.SetSecurityDescriptorSddlForm([string]$labOriginal.sddl, $labSection)
            Set-Acl -LiteralPath $labFile -AclObject $labAcl
            Write-Output 'RESTORED: Original report permissions. Run -Action Check to verify.'
        }
    }
    exit 0
} catch {
    Write-Output ('ERROR: ' + $_.Exception.Message)
    exit 2
}
