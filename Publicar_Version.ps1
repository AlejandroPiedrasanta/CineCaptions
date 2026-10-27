# CineCaptions - By Cinema Productions
# Publicar_Version.ps1 - publica la version actual para que los programas instalados se actualicen solos (actualizaciones.py).
# ============================================================================
#   powershell -ExecutionPolicy Bypass -File Publicar_Version.ps1 -Notas "Lo nuevo en una linea"            genera version.json y lo SUBE
#   powershell -ExecutionPolicy Bypass -File Publicar_Version.ps1 -SinSubir                                  solo genera INSTALADORES\version.json (para revisarlo)
#   powershell -ExecutionPolicy Bypass -File Publicar_Version.ps1 -CrearRepo -Notas "..."                     crea (una vez) el repositorio PUBLICO de instaladores
#   powershell -ExecutionPolicy Bypass -File Publicar_Version.ps1 -Canal beta -Notas "..."                    publica como beta (solo la ven quienes activaron 'Recibir versiones beta')
# Antes: Actualizar_Windows.ps1 y Actualizar_Mac.ps1 (los instaladores de la version actual tienen que estar en INSTALADORES\).
# El repositorio de instaladores es PUBLICO y solo trae los .exe/.dmg y version.json; el codigo sigue en el repositorio privado.
# Cada instalador va con su SHA-256: el programa NO instala nada cuya huella no coincida. Y el manifiesto va FIRMADO (v5.52, firmar_manifiesto.py).
# ============================================================================
param(
    [string]$Notas = '',          # vacío = las mejoras de esta versión tal como están en ajustes_ui.NOTAS_VERSION (una por línea): es lo que enseña el aviso de actualización
    [string]$Repo = 'AlejandroPiedrasanta/CineCaptions-releases',
    [ValidateSet('estable', 'beta')][string]$Canal = 'estable',
    [switch]$SinSubir,
    [switch]$CrearRepo
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
function Paso($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
function Nativo($bloque) { & $bloque; if ($LASTEXITCODE -ne 0) { throw "Fallo: $bloque" } }
function Sondear($bloque) { $antes = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; try { & $bloque 2>&1 | Out-Null } finally { $ErrorActionPreference = $antes }; return $LASTEXITCODE }

$version = ([regex]::Match((Get-Content '1_codigo\version.py' -Raw), "APP_VERSION\s*=\s*'([^']+)'")).Groups[1].Value
if (-not $version) { throw 'No pude leer APP_VERSION de 1_codigo\version.py' }
$etiqueta = "v$version"
if ([string]::IsNullOrWhiteSpace($Notas)) {
    $vpy = Join-Path (Get-Location) '6_compilacion/venv315/Scripts/python.exe'
    $tmpNotas = Join-Path ([IO.Path]::GetTempPath()) 'cc_notas_version.txt'
    Remove-Item -LiteralPath $tmpNotas -ErrorAction SilentlyContinue
    # por archivo UTF-8: la consola de Windows PowerShell rompe las tildes de lo que imprime Python
    try { & $vpy -X utf8 '3_compilar/notas_de_version.py' $version $tmpNotas | Out-Null; if (Test-Path $tmpNotas) { $Notas = [IO.File]::ReadAllText($tmpNotas, (New-Object Text.UTF8Encoding $false)).Trim() } } catch { $Notas = '' }
    if ([string]::IsNullOrWhiteSpace($Notas)) { $Notas = 'Mejoras y correcciones.' }
}
$base = "https://github.com/$Repo/releases/download/$etiqueta"
Paso "Version $version ($Canal)"

# Los instaladores de ESTA version, uno por plataforma
$piezas = [ordered]@{
    'windows'    = "INSTALADORES\Windows\Instalar_CineCaptions_$version.exe"
    'mac_arm64'  = "INSTALADORES\Mac\CineCaptions_Mac_AppleSilicon_$version.dmg"
    'mac_x86_64' = "INSTALADORES\Mac\CineCaptions_Mac_Intel_$version.dmg"
}
$archivos = [ordered]@{}
$subir = @()
foreach ($clave in $piezas.Keys) {
    $ruta = $piezas[$clave]
    if (-not (Test-Path -LiteralPath $ruta)) { Write-Host "    FALTA  $ruta  (corre Actualizar_Windows.ps1 / Actualizar_Mac.ps1)" -ForegroundColor Yellow; continue }
    $f = Get-Item -LiteralPath $ruta
    $huella = (Get-FileHash -LiteralPath $ruta -Algorithm SHA256).Hash.ToLower()
    $archivos[$clave] = [ordered]@{ url = "$base/$($f.Name)"; sha256 = $huella; tam = [int64]$f.Length }
    $subir += $f.FullName
    Write-Host ("    {0,-11} {1}  {2:N1} MB  {3}" -f $clave, $f.Name, ($f.Length / 1MB), $huella.Substring(0, 12))
}
if ($archivos.Count -eq 0) { throw "No hay ningun instalador de la $version en INSTALADORES\" }
if (-not $archivos.Contains('windows')) { Write-Host '    (aviso) sin el .exe de Windows: los Windows no verian esta version' -ForegroundColor Yellow }

# El manifiesto: la entrada de este canal es la nueva; la del otro canal se conserva de la publicacion anterior (si la hay)
$manifiesto = [ordered]@{}
if (-not $SinSubir) {
    $previo = Join-Path ([IO.Path]::GetTempPath()) 'cc_version_previa.json'
    Remove-Item -LiteralPath $previo -ErrorAction SilentlyContinue
    $rc = Sondear { gh release download --repo $Repo --pattern 'version.json' --output $previo }
    if ($rc -eq 0 -and (Test-Path $previo)) {
        try { $p = Get-Content $previo -Raw | ConvertFrom-Json; foreach ($c in 'estable', 'beta') { if ($c -ne $Canal -and $p.$c) { $manifiesto[$c] = $p.$c } } } catch { }
    }
}
# v5.20: las versiones son de DOS numeros (5.20); los programas 5.5.x instalados solo entienden x.y.z: el manifiesto lleva 5.20.0
$versionManifiesto = if ($version.Split('.').Count -eq 2) { "$version.0" } else { $version }
$manifiesto[$Canal] = [ordered]@{ version = $versionManifiesto; notas = $Notas; fecha = (Get-Date -Format 'yyyy-MM-dd'); archivos = $archivos }
$json = $manifiesto | ConvertTo-Json -Depth 8
$salida = Join-Path (Get-Location) 'INSTALADORES\version.json'
[IO.File]::WriteAllText($salida, $json, (New-Object Text.UTF8Encoding $false))       # UTF-8 SIN BOM (el programa lo lee con json.loads)
# v5.52: FIRMADO (Ed25519) con la clave privada de ~/CineCaptions_claves (fuera del repositorio): los programas desde la 5.52 rechazan
# un version.json sin firma, asi que sin la clave no se publica
$vpy = Join-Path (Get-Location) '6_compilacion/venv315/Scripts/python.exe'
Nativo { & $vpy -X utf8 '3_compilar/firmar_manifiesto.py' $salida }
Write-Host "    manifiesto: $salida"
if ($SinSubir) { Write-Host ''; Write-Host 'Listo (sin subir). Revisa INSTALADORES\version.json.' -ForegroundColor Green; return }

# El repositorio publico de instaladores
Paso "Repositorio $Repo"
if ((Sondear { gh repo view $Repo }) -ne 0) {
    if (-not $CrearRepo) {
        Write-Host "    El repositorio $Repo no existe todavia." -ForegroundColor Yellow
        Write-Host '    Sera PUBLICO (solo trae los instaladores y version.json, no el codigo). Para crearlo una vez:' -ForegroundColor Yellow
        Write-Host '    powershell -ExecutionPolicy Bypass -File Publicar_Version.ps1 -CrearRepo -Notas "..."' -ForegroundColor Yellow
        exit 1
    }
    Nativo { gh repo create $Repo --public --add-readme --description 'Instaladores de CineCaptions (By Cinema Productions)' }
}
# GitHub no deja crear una publicacion en un repositorio VACIO (sin ningun commit): se le pone un README minimo
if ((Sondear { gh api "repos/$Repo/commits?per_page=1" }) -ne 0) {
    $leeme = "# CineCaptions - instaladores`n`nInstaladores publicos de CineCaptions (By Cinema Productions). Aqui solo estan los .exe y .dmg de cada version y su version.json; el programa se actualiza solo desde aqui.`n"
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($leeme))
    Nativo { gh api -X PUT "repos/$Repo/contents/README.md" -f message='README' -f content=$b64 --silent }
}

# Una publicacion por version; si ya existia (reintento) se reemplazan sus archivos
Paso "Subiendo $etiqueta"
# las notas viajan por archivo UTF-8 (por la linea de comandos de Windows las tildes se estropean)
$archivoNotas = Join-Path ([IO.Path]::GetTempPath()) 'cc_notas_publicacion.txt'
[IO.File]::WriteAllText($archivoNotas, $Notas, (New-Object Text.UTF8Encoding $false))
if ((Sondear { gh release view $etiqueta --repo $Repo }) -eq 0) {
    Nativo { gh release upload $etiqueta @($subir + $salida) --repo $Repo --clobber }
    Nativo { gh release edit $etiqueta --repo $Repo --notes-file $archivoNotas }
} else {
    Nativo { gh release create $etiqueta @($subir + $salida) --repo $Repo --title "CineCaptions $version" --notes-file $archivoNotas --latest }
}

Paso 'Comprobando lo publicado'
$url = "https://github.com/$Repo/releases/latest/download/version.json"
# la cache de GitHub tarda en enterarse de la version nueva: se reintenta hasta ~3 min antes de dar error (en 5.5.5 y 5.5.6 la 1.a mirada daba la anterior)
$v = $null
for ($i = 0; $i -lt 10; $i++) {
    $publicado = Invoke-RestMethod -Uri "$url`?t=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())" -UseBasicParsing -Headers @{ 'Cache-Control' = 'no-cache' }
    $v = $publicado.$Canal.version
    if ($v -eq $versionManifiesto) { break }      # (el manifiesto lleva x.y.z: «5.49.0»)
    Start-Sleep -Seconds 20
}
Write-Host "    $url  ->  $Canal $v"
if ($v -ne $versionManifiesto) { throw "El manifiesto publicado dice $v y se esperaba $versionManifiesto" }
Write-Host ''
Write-Host "Publicada la $version. Los CineCaptions instalados la veran en menos de 12 h (o al pulsar 'Buscar actualizaciones')." -ForegroundColor Green
