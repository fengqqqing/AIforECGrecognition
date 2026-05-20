$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/2] 运行单元测试..." -ForegroundColor Cyan
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "[2/2] 运行离线回放（mock推理）..." -ForegroundColor Cyan
python offline_replay.py --samples 4000 --mock-label 2

Write-Host "离线检查完成。" -ForegroundColor Green
