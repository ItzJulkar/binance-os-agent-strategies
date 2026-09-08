# Binance Agent OS Multi-Strategy — Live Terminal launcher (PowerShell)
# Shows all trades taken via the Binance OS agent in a live color dashboard.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = "python"
if (Get-Command "py" -ErrorAction SilentlyContinue) { $py = "py" }
Write-Host "Starting Binance OS multi-strategy live terminal..." -ForegroundColor Cyan
& $py "$root\terminal\terminal.py"
