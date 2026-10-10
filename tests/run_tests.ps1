# Runs the EZER site checks against a local copy of the site.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1
# Requires: Python 3 + Playwright (pip install playwright) and Microsoft Edge.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$port = 8765
$server = Start-Process python -ArgumentList '-m', 'http.server', $port -WorkingDirectory $root -WindowStyle Hidden -PassThru
try {
    Start-Sleep -Seconds 2
    $env:EZER_TEST_URL = "http://localhost:$port/"
    $failed = 0
    foreach ($suite in 'test_page.py', 'test_seo.py', 'test_founder.py') {
        Write-Host "`n=== $suite ===" -ForegroundColor Cyan
        python (Join-Path $PSScriptRoot $suite)
        if ($LASTEXITCODE -ne 0) { $failed++ }
    }
    if ($failed) { Write-Host "`n$failed suite(s) FAILED" -ForegroundColor Red; exit 1 }
    Write-Host "`nAll suites passed" -ForegroundColor Green
}
finally {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
}
