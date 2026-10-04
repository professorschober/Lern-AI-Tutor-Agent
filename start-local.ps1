# Startet den gebauten Prototyp ausschließlich auf Loopback.
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Python-Umgebung fehlt. Folge der Einrichtung in README.md.'
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
    & $taskPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
