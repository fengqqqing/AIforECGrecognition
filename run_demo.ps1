$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot

$deployDir = Get-ChildItem -LiteralPath $repoRoot -Directory |
    Where-Object { $_.Name -like "*pyqt" -and (Test-Path -LiteralPath (Join-Path $_.FullName "ECGMonitor\main.py")) } |
    Select-Object -First 1

if ($null -eq $deployDir) {
    throw "未找到 ECGMonitor 部署目录，请确认仓库根目录下存在 *pyqt\ECGMonitor\main.py"
}

$mainPath = Join-Path $deployDir.FullName "ECGMonitor\main.py"
if (-not (Test-Path -LiteralPath $mainPath)) {
    throw "未找到 demo 入口: $mainPath"
}

python $mainPath --demo
