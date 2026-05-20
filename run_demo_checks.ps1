$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot

$deployDir = Get-ChildItem -LiteralPath $repoRoot -Directory |
    Where-Object { $_.Name -like "*pyqt" -and (Test-Path -LiteralPath (Join-Path $_.FullName "ECGMonitor\offline_replay.py")) } |
    Select-Object -First 1

if ($null -eq $deployDir) {
    throw "ECGMonitor deploy directory was not found. Expected: *pyqt\ECGMonitor\offline_replay.py"
}

$ecgDir = Join-Path $deployDir.FullName "ECGMonitor"
$testsDir = Join-Path $ecgDir "tests"
$offlineReplay = Join-Path $ecgDir "offline_replay.py"

function Invoke-DemoCheck {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "[$Name]" -ForegroundColor Cyan
    & $Command
    Write-Host "[$Name] OK" -ForegroundColor Green
}

Invoke-DemoCheck "1/4 unit tests" {
    & python -m unittest discover -s $testsDir -p "test_*.py" -t $ecgDir -v
}

Invoke-DemoCheck "2/4 demo policy validation" {
    & python -m unittest discover -s $testsDir -p "test_demo_policy.py" -t $ecgDir -v
}

Invoke-DemoCheck "3/4 fixed demo mock replay" {
    & python $offlineReplay --row 3 --samples 2000 --event-interval 500 --lead-events "0,0,0,0" --hr-events "72,84,78,90" --mock-label 0
}

Invoke-DemoCheck "4/4 fixed demo real-model replay" {
    & python $offlineReplay --row 3 --samples 2000 --event-interval 500 --lead-events "0,0,0,0" --hr-events "72,84,78,90" --real-model
}

Write-Host "Demo checks completed." -ForegroundColor Green
