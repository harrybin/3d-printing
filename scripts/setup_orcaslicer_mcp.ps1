$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv-orcaslicer-mcp"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    python -m venv $venv
}

& $python -m pip install --disable-pip-version-check `
    -r (Join-Path $root "tools\orcaslicer-mcp-requirements.txt")

Write-Host "OrcaSlicer MCP installed in $venv"
Write-Host "Restart the MCP client so .vscode\mcp.json is reloaded."
