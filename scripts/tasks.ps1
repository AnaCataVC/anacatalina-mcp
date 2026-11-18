<#
.SYNOPSIS
    Unified task runner for anacatalina-mcp in PowerShell.
.DESCRIPTION
    Provides shortcuts for running tests, coverage, security audits, upstream sync, hooks setup, version bump, and dev server.
.EXAMPLE
    .\scripts\tasks.ps1 test
    .\scripts\tasks.ps1 serve
    .\scripts\tasks.ps1 setup-hooks
    .\scripts\tasks.ps1 bump -Version 1.10.2
    .\scripts\tasks.ps1 check-all
#>
param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("test", "cov", "invariants", "audit", "sync", "sec", "serve", "setup-hooks", "bump", "check-all")]
    [string]$Task,

    [Parameter(Position=1)]
    [int]$Port = 8080,

    [Parameter()]
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

# Resolve Python interpreter
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$TasksPy = Join-Path $ProjectRoot "scripts\tasks.py"

if ($Version) {
    & $Python $TasksPy $Task --port $Port --version $Version
} else {
    & $Python $TasksPy $Task --port $Port
}
exit $LASTEXITCODE
