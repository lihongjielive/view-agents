# §0 基建：Windows 一键测试（pytest + fault_drill）
param(
    [switch]$FaultDrill,
    [switch]$E2eOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "python not found"
}

pip install -e ".[dev]" -q | Out-Null

if ($E2eOnly) {
    pytest -q tests/test_figure01_skeleton.py tests/test_e2e_refund_coupon.py
}
else {
    pytest -q
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($FaultDrill) {
    python scripts/fault_drill/run_all.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "[OK] tests passed"