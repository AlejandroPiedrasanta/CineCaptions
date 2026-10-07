# CineCaptions - By Cinema Productions
# Actualizar_Mac.ps1 - sube el codigo a GitHub, compila los instaladores de Mac (Apple Silicon e Intel) y los deja en INSTALADORES\Mac.
# ============================================================================
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1                 sube cambios + compila + descarga (10-15 min)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1 -SoloDescargar  solo baja los .dmg de la ultima compilacion buena
# Deja en INSTALADORES\Mac: CineCaptions_Mac_AppleSilicon_<version>.dmg y CineCaptions_Mac_Intel_<version>.dmg (los viejos se borran).
# Requiere: git y gh (GitHub CLI) con sesion iniciada; repositorio privado AlejandroPiedrasanta/CineCaptions.
# Correrlo despues de CUALQUIER mejora del programa (el .exe y el de Mac salen del mismo codigo).
# ============================================================================
param([switch]$SoloDescargar, [string]$Mensaje = 'Actualizacion de CineCaptions')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
function Paso($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Nativo($bloque) { & $bloque; if ($LASTEXITCODE -ne 0) { throw "Fallo: $bloque" } }
$flujo = 'mac.yml'

if (-not $SoloDescargar) {
    Paso 'Subiendo el codigo a GitHub'
    git add -A
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Nativo { git commit -q -m "$Mensaje`n`nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" }
        Nativo { git push -q }
    } else { Write-Host '    (sin cambios nuevos)' }
    $sha = (git rev-parse HEAD).Trim()

    Paso 'Compilando en GitHub (macos-14 Apple Silicon + macos-15-intel)'
    Nativo { gh workflow run $flujo }
    $id = $null
    for ($i = 0; $i -lt 20 -and -not $id; $i++) {
        Start-Sleep -Seconds 5
        $id = gh run list --workflow $flujo --event workflow_dispatch --commit $sha --limit 1 --json databaseId -q '.[0].databaseId'
    }
    if (-not $id) { throw 'No encontre la compilacion que acabo de lanzar' }
    Write-Host "    https://github.com/AlejandroPiedrasanta/CineCaptions/actions/runs/$id"
    while ($true) {
        $e = gh run view $id --json status,conclusion -q '.status + " " + .conclusion'
        if ($e -like 'completed*') { break }
        Start-Sleep -Seconds 30
    }
    if ($e -ne 'completed success') { throw "La compilacion de Mac fallo ($e). Mira el registro: gh run view $id --log-failed" }
} else {
    $id = gh run list --workflow $flujo --status success --limit 1 --json databaseId -q '.[0].databaseId'
    if (-not $id) { throw 'No hay ninguna compilacion buena todavia' }
}

Paso 'Descargando los instaladores'
$tmp = Join-Path $env:TEMP "cinecaptions_mac_$id"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
Nativo { gh run download $id -D $tmp }
$nuevos = Get-ChildItem $tmp -Recurse -Filter 'CineCaptions_Mac_*.dmg'
if (-not $nuevos) { throw 'La compilacion no dejo ningun .dmg' }
$destino = Join-Path (Get-Location) 'INSTALADORES\Mac'
New-Item -ItemType Directory -Force -Path $destino | Out-Null
Get-ChildItem $destino -Filter 'CineCaptions_Mac_*.dmg' | Remove-Item -Force
Get-ChildItem . -Filter 'CineCaptions_Mac_*.dmg' | Remove-Item -Force      # (los que quedaban sueltos en la raiz)
foreach ($d in $nuevos) {
    Move-Item $d.FullName $destino -Force
    Write-Host ('    {0}  ({1:N0} MB)' -f $d.Name, ($d.Length / 1MB))
}
Remove-Item -Recurse -Force $tmp
Paso 'LISTO: instaladores de Mac al dia en INSTALADORES\Mac'
