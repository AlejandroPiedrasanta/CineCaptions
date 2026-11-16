# CineCaptions - By Cinema Productions
# Actualizar_Mac.ps1 - compila los instaladores de Mac (Apple Silicon e Intel) en GitHub y los deja en INSTALADORES\Mac.
# ============================================================================
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1                 sube cambios + compila + descarga (10-15 min)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1 -SoloDescargar  solo baja los .dmg de la ultima compilacion buena
# Deja en INSTALADORES\Mac: CineCaptions_Mac_AppleSilicon_<version>.dmg y CineCaptions_Mac_Intel_<version>.dmg (los viejos se borran).
# Requiere: git y gh (GitHub CLI) con sesion iniciada.
# v5.4.14: la compilacion corre en un repositorio APARTE (AlejandroPiedrasanta/CineCaptions-mac-build), un ESPEJO del codigo necesario para compilar (1_codigo, 2_recursos,
# 3_compilar, 7_mac, .github): sin DOCUMENTACION, notas internas, licencias ni historial. El repositorio privado sigue siendo la copia de seguridad del codigo.
# v5.52 (seguridad): el espejo es PRIVADO (siendo publico, cualquiera leia todo el codigo). Los minutos de macOS de un repositorio privado cuentan x10 contra el cupo
# gratis (2000/mes: unas 14 compilaciones de ~14 min); pasado el cupo GitHub no arranca la compilacion ("spending limit") hasta el mes siguiente o hasta poner un pago.
# El espejo sube SOLO lo que el repositorio privado no ignora (firma.json, .env, certificados .pfx/.p12/.pem/.key nunca salen).
# Correrlo despues de CUALQUIER mejora del programa (el .exe y el de Mac salen del mismo codigo).
# ============================================================================
param([switch]$SoloDescargar, [string]$Mensaje = 'Actualizacion de CineCaptions')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
function Paso($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Nativo($bloque) { & $bloque; if ($LASTEXITCODE -ne 0) { throw "Fallo: $bloque" } }
$flujo = 'mac.yml'
$repoMac = 'AlejandroPiedrasanta/CineCaptions-mac-build'                 # PRIVADO desde la 5.52; espejo del codigo necesario para compilar
$espejo = Join-Path $env:USERPROFILE 'CineCaptions-mac-espejo'
$raiz = (Get-Location).Path
# 2026-11-16 (el usuario: «deja 2 carpetas: el programa y los instaladores»): el programa vive en PROGRAMA\ y los instaladores en
# ..\INSTALADORES (junto a PROGRAMA, en la raíz de CineCaptions); en el espejo de Mac siguen dentro
$INST = Join-Path (Split-Path $raiz -Parent) 'INSTALADORES'
if ((Split-Path $raiz -Leaf) -ne 'PROGRAMA' -or -not (Test-Path -LiteralPath $INST)) { $INST = Join-Path $raiz 'INSTALADORES' }
$repo = if ((Split-Path $raiz -Leaf) -eq 'PROGRAMA') { Split-Path $raiz -Parent } else { $raiz }    # (.git, .github y .gitignore: en la raíz)

if (-not $SoloDescargar) {
    Paso 'Copia de seguridad del codigo (repositorio privado)'
    $ea = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    git add -A 2>&1 | Out-Null
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -q -m "$Mensaje`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" 2>&1 | Out-Null
        git push -q 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host '    (no pude subir al repositorio privado; no impide compilar Mac)' -ForegroundColor Yellow }
    } else { Write-Host '    (sin cambios nuevos)' }
    $ErrorActionPreference = $ea

    Paso "Preparando el espejo privado de compilacion ($repoMac)"
    $ea = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    gh repo view $repoMac --json name 2>&1 | Out-Null
    $existe = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $ea
    if (-not $existe) {
        Nativo { gh repo create $repoMac --private --description 'Compilacion de los instaladores de Mac de CineCaptions (By Cinema Productions)' }
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
        # (sin el runtime de Remotion de Windows ni las dependencias de desarrollo: la Mac arma los suyos con preparar_remotion.py)
        $origen = if ($d -eq '.github') { Join-Path $repo $d } else { Join-Path $raiz $d }
        robocopy $origen (Join-Path $espejo $d) /MIR /XD __pycache__ node_modules (Join-Path $raiz '2_recursos\edicion_pro\remotion\runtime') (Join-Path $raiz '1_codigo\remotion\out') (Join-Path $raiz '1_codigo\remotion\public') /XF *.pyc *.exe *.dmg *.pkg *.pfx *.p12 *.pem *.key firma.json .env .env.* /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy fallo copiando $d ($LASTEXITCODE)" }
    }
    $global:LASTEXITCODE = 0
    # v5.52: robocopy copia la CARPETA, no lo de git: el espejo ignora lo mismo que el repositorio privado (sus reglas, sin comentarios) mas cualquier certificado o clave
    # (las reglas de la raíz llevan «PROGRAMA/» delante; el espejo tiene 1_codigo… en su raíz)
    $reglas = @(Get-Content (Join-Path $repo '.gitignore') -Encoding UTF8 | Where-Object { $_.Trim() -and -not $_.StartsWith('#') } | ForEach-Object { $_ -replace '^(!?)PROGRAMA/', '$1' })
    Set-Content -Path (Join-Path $espejo '.gitignore') -Value ((@('__pycache__/', '*.pyc', '*.exe', '*.dmg', '*.pkg', '6_compilacion_mac/', '*.pfx', '*.p12', '*.pem', '*.key', 'firma.json', '.env', '.env.*') + $reglas) -join "`n") -Encoding ASCII
    Set-Content -Path (Join-Path $espejo 'LEEME.md') -Encoding UTF8 -Value "# CineCaptions - compilacion de Mac`n`nEste repositorio solo compila los instaladores de macOS de CineCaptions (By Cinema Productions) en GitHub Actions. Los instaladores se publican en https://github.com/AlejandroPiedrasanta/CineCaptions-releases"
    New-Item -ItemType Directory -Force -Path (Join-Path $espejo 'INSTALADORES\Mac') | Out-Null
    Set-Content -Path (Join-Path $espejo 'INSTALADORES\Mac\.gitkeep') -Value '' -Encoding ASCII
    git -C $espejo rm -r -q --cached . | Out-Null          # lo que ya estaba subido y ahora se ignora (desktop.ini) sale del espejo
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
$destino = Join-Path $INST 'Mac'
New-Item -ItemType Directory -Force -Path $destino | Out-Null
Get-ChildItem $destino -Filter 'CineCaptions_Mac_*.dmg' | Remove-Item -Force
Get-ChildItem . -Filter 'CineCaptions_Mac_*.dmg' | Remove-Item -Force      # (los que quedaban sueltos en la raiz)
foreach ($d in $nuevos) {
    Move-Item $d.FullName $destino -Force
    Write-Host ('    {0}  ({1:N0} MB)' -f $d.Name, ($d.Length / 1MB))
}
Remove-Item -Recurse -Force $tmp
Paso 'LISTO: instaladores de Mac al dia en INSTALADORES\Mac'
