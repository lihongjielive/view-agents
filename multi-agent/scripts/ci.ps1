# 本地 CI：与 GitHub Actions 相同步骤
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
pip install -e ".[dev]" -q
pytest -q
python scripts/fault_drill/run_all.py
Write-Host "[ci] OK"