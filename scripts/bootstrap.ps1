$ErrorActionPreference = 'Stop'
if (Test-Path '.env') { Write-Host '.env ya existe; no se reemplaza.'; exit 0 }
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
$secret = [BitConverter]::ToString($bytes).Replace('-', '')
$template = Get-Content '.env.example' -Raw
$template = $template.Replace('REEMPLAZAR_CON_TOKEN_ALEATORIO_SEGURO_32_CHAR', $secret)
[System.IO.File]::WriteAllText((Join-Path (Get-Location) '.env'), $template, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Creado .env. Copia el valor CONTAMATE_API_TOKEN desde ese archivo al panel web. No publiques .env."
