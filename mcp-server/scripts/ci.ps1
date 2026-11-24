# mcp-server CI（Windows 本地对照 GitHub Actions）
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

pip install -e ".[dev]" -q
pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[OK] mcp-server pytest"