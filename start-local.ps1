# Startet den gebauten Prototyp ausschließlich auf Loopback.
param([switch]$Reload)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot 'backend\.venv1\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'backend/.venv1 fehlt. Folge der Einrichtung in README.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'frontend\dist\index.html'))) {
    throw 'Frontend-Build fehlt. Führe in frontend: npm ci und npm run build aus.'
}
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'backend\.env'))) {
    throw 'Konfiguration fehlt. Kopiere backend/.env.example nach backend/.env und ergänze deine Zugangsdaten.'
}
Push-Location (Join-Path $taskRoot 'backend')
try {
    Write-Host 'Lernraum: http://127.0.0.1:8000 — Beenden mit Strg+C'
    & $taskPython -c 'import fastapi, uvicorn, oracledb, sqlglot, pydantic_settings'
    if ($LASTEXITCODE -ne 0) {
        throw 'Backend-Pakete fehlen. Installiere backend/requirements.lock in backend/.venv1.'
    }
    $taskArguments = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000')
    if ($Reload) { $taskArguments += '--reload' }
    & $taskPython @taskArguments
    if ($LASTEXITCODE -ne 0) {
        throw 'Backend-Start fehlgeschlagen. Prüfe die Meldung oben; möglicherweise ist Port 8000 bereits belegt.'
    }
} finally {
    Pop-Location
}
