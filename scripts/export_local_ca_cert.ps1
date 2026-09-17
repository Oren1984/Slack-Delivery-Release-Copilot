# Some networks (corporate proxies, antivirus "web protection" features like
# Norton, Kaspersky, etc.) intercept outbound TLS and re-sign it with a local
# root certificate. Windows and most such tools trust that root automatically,
# but a fresh Docker Linux container does not, so `docker compose build` can
# fail with SSL: CERTIFICATE_VERIFY_FAILED when pip tries to reach PyPI.
#
# This script copies the intercepting root certificate (if one is active on
# this machine) into docker/extra-ca-certs/, which the Dockerfile trusts in
# addition to the standard public CA bundle. It does NOT disable or weaken
# certificate verification anywhere — it only adds a real root of trust that
# this machine's own network already relies on.
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/export_local_ca_cert.ps1

$ErrorActionPreference = "Stop"
$targetDir = Join-Path $PSScriptRoot "..\docker\extra-ca-certs"
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$candidates = @()
if ($env:NODE_EXTRA_CA_CERTS) { $candidates += $env:NODE_EXTRA_CA_CERTS }
$candidates += "C:\ProgramData\Norton\Antivirus\wscert.pem"

$found = $false
foreach ($path in $candidates) {
    if ($path -and (Test-Path $path)) {
        $dest = Join-Path $targetDir "local-intercept-ca.crt"
        Copy-Item -Path $path -Destination $dest -Force
        Write-Host "Copied local intercepting CA cert from '$path' to '$dest'."
        $found = $true
        break
    }
}

if (-not $found) {
    Write-Host "No known TLS-intercepting CA certificate found on this machine."
    Write-Host "If 'docker compose build' fails with a certificate error, locate your"
    Write-Host "security software's or proxy's root CA (.crt/.pem) and copy it manually"
    Write-Host "into docker/extra-ca-certs/, then rebuild."
}
