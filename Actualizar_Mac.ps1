# CineCaptions - By Cinema Productions
# Actualizar_Mac.ps1 - compila los instaladores de Mac (Apple Silicon e Intel) en GitHub y los deja en INSTALADORES\Mac.
# ============================================================================
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1                 sube cambios + compila + descarga (10-15 min)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1 -SoloDescargar  solo baja los .dmg de la ultima compilacion buena
# Deja en INSTALADORES\Mac: CineCaptions_Mac_AppleSilicon_<version>.dmg y CineCaptions_Mac_Intel_<version>.dmg (los viejos se borran).
# Requiere: git y gh (GitHub CLI) con sesion iniciada.
# v5.4.14: los minutos de macOS de un repositorio PRIVADO se pagan (en el plan gratis no alcanzan ni para una compilacion); en uno PUBLICO son gratis. Por eso la compilacion corre
# en un repositorio publico APARTE (AlejandroPiedrasanta/CineCaptions-mac-build), un ESPEJO del codigo necesario para compilar (1_codigo, 2_recursos, 3_compilar, 7_mac, .github):
# sin DOCUMENTACION, notas internas, licencias ni historial. El repositorio privado sigue siendo la copia de seguridad del codigo.
# Correrlo despues de CUALQUIER mejora del programa (el .exe y el de Mac salen del mismo codigo).
# ============================================================================
param([switch]$SoloDescargar, [string]$Mensaje = 'Actualizacion de CineCaptions')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
function Paso($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Nativo($bloque) { & $bloque; if ($LASTEXITCODE -ne 0) { throw "Fallo: $bloque" } }
$flujo = 'mac.yml'
$repoMac = 'AlejandroPiedrasanta/CineCaptions-mac-build'                 # PUBLICO (Actions gratis en macOS); espejo del codigo necesario para compilar
$espejo = Join-Path $env:USERPROFILE 'CineCaptions-mac-espejo'
$raiz = (Get-Location).Path

if (-not $SoloDescargar) {
    Paso 'Copia de seguridad del codigo (repositorio privado)'
    $ea = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    git add -A 2>&1 | Out-Null
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -q -m "$Mensaje`n`nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" 2>&1 | Out-Null
        git push -q 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host '    (no pude subir al repositorio privado; no impide compilar Mac)' -ForegroundColor Yellow }
    } else { Write-Host '    (sin cambios nuevos)' }
    $ErrorActionPreference = $ea

    Paso "Preparando el espejo publico de compilacion ($repoMac)"
    $ea = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    gh repo view $repoMac --json name 2>&1 | Out-Null
    $existe = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $ea
    if (-not $existe) {
        Nativo { gh repo create $repoMac --public --description 'Compilacion de los instaladores de Mac de CineCaptions (By Cinema Productions)' }
    }
    if (-not (Test-Path (Join-Path $espejo '.git'))) {
        if (Test-Path $espejo) { Remove-Item -Recurse -Force $espejo }
        Nativo { gh repo clone $repoMac $espejo -- -q }
        $idUsuario = gh api user -q '.id'
        $login = gh api user -q '.login'
        git -C $espejo config user.name $login
        git -C $espejo config user.email "$idUsuario+$login@users.noreply.github.com"      # el correo real no sale en el historial publico
    }
    foreach ($d in '1_codigo', '2_recursos', '3_compilar', '7_mac', '.github') {
        robocopy (Join-Path $raiz $d) (Join-Path $espejo $d) /MIR /XD __pycache__ /XF *.pyc *.exe *.dmg *.pkg /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy fallo copiando $d ($LASTEXITCODE)" }
    }
    $global:LASTEXITCODE = 0
    Set-Content -Path (Join-Path $espejo '.gitignore') -Value "__pycache__/`n*.pyc`n*.exe`n*.dmg`n*.pkg`n6_compilacion_mac/" -Encoding ASCII
    Set-Content -Path (Join-Path $espejo 'LEEME.md') -Encoding UTF8 -Value "# CineCaptions - compilacion de Mac`n`nEste repositorio solo compila los instaladores de macOS de CineCaptions (By Cinema Productions) en GitHub Actions. Los instaladores se publican en https://github.com/AlejandroPiedrasanta/CineCaptions-releases"
    New-Item -ItemType Directory -Force -Path (Join-Path $espejo 'INSTALADORES\Mac') | Out-Null
    Set-Content -Path (Join-Path $espejo 'INSTALADORES\Mac\.gitkeep') -Value '' -Encoding ASCII
    git -C $espejo add -A
    git -C $espejo diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Nativo { git -C $espejo commit -q -m "$Mensaje" }
        Nativo { git -C $espejo push -q origin HEAD }
    } else { Write-Host '    (el espejo ya estaba al dia)' }
    $sha = (git -C $espejo rev-parse HEAD).Trim()

    Paso 'Compilando en GitHub (macos-14 Apple Silicon + macos-15-intel)'
    Nativo { gh workflow run $flujo -R $repoMac }
    $id = $null
    for ($i = 0; $i -lt 20 -and -not $id; $i++) {
        Start-Sleep -Seconds 5
        $id = gh run list -R $repoMac --workflow $flujo --event workflow_dispatch --commit $sha --limit 1 --json databaseId -q '.[0].databaseId'
    }
    if (-not $id) { throw 'No encontre la compilacion que acabo de lanzar' }
    Write-Host "    https://github.com/$repoMac/actions/runs/$id"
    $limite = (Get-Date).AddMinutes(60)
    while ($true) {
        # (PowerShell 5.1 pierde las comillas dobles de -q: se lee el JSON entero y se interpreta aqui; antes esto giraba para siempre)
        $json = gh run view $id -R $repoMac --json status,conclusion
        if ($LASTEXITCODE -ne 0 -or -not $json) { throw "No pude leer el estado de la compilacion ($id): revisa 'gh auth status'" }
        $r = $json | ConvertFrom-Json
        $e = "$($r.status) $($r.conclusion)".Trim()
        if ($r.status -eq 'completed') { break }
        if ((Get-Date) -gt $limite) { throw "La compilacion de Mac lleva mas de 60 minutos ($e): mira https://github.com/$repoMac/actions/runs/$id" }
        Start-Sleep -Seconds 30
    }
    if ($e -ne 'completed success') { throw "La compilacion de Mac fallo ($e). Mira el registro: gh run view $id -R $repoMac --log-failed" }
} else {
    $id = gh run list -R $repoMac --workflow $flujo --status success --limit 1 --json databaseId -q '.[0].databaseId'
    if (-not $id) { throw 'No hay ninguna compilacion buena todavia' }
}

Paso 'Descargando los instaladores'
$tmp = Join-Path $env:TEMP "cinecaptions_mac_$id"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
Nativo { gh run download $id -R $repoMac -D $tmp }
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
