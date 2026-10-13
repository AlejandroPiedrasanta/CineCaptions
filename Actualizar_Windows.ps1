# CineCaptions - By Cinema Productions
# Actualizar_Windows.ps1 - deja en INSTALADORES\Windows el instalador de Windows AL DIA con el codigo: sube la version si el codigo cambio, compila y borra los viejos.
# ============================================================================
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1                 compila solo si el codigo cambio desde la ultima vez (sube la version +1)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -SinSubir       compila SIN subir la version (por si ya la subiste a mano en version.py)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -Forzar         compila aunque no haya cambios
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -Limpio         lo rehace todo desde cero (PyInstaller --clean)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -SoloInstalador  reusa el programa ya compilado y solo rehace el instalador (si solo cambiaste Instalador.cs)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -Registrar       da por bueno el instalador actual para el codigo actual (sin compilar)
#   powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1 -Comprobar      no compila: dice si el instalador de la raiz esta al dia o desactualizado
# Deja: INSTALADORES\Windows\Instalar_CineCaptions_<version>.exe (los anteriores se borran).
# Hace, por orden: 1) mira si el codigo cambio (huella del contenido) 2) sube la version (version.py) y la copia a los scripts de Resolve
#                  3) 3_compilar\Construir_Instalador.ps1 (PyInstaller + autoprueba + instalador) 4) comprueba el resultado y anota la huella.
# Correrlo despues de CUALQUIER mejora del programa (el .exe de Windows y los de Mac salen del mismo codigo: Actualizar_Mac.ps1).
# ============================================================================
param([switch]$SinSubir, [switch]$Forzar, [switch]$Limpio, [switch]$Comprobar, [switch]$SoloInstalador, [switch]$Registrar)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz
$utf8 = New-Object System.Text.UTF8Encoding($false)
$obra = Join-Path $raiz '6_compilacion'
$vpy = Join-Path $obra 'venv314\Scripts\python.exe'
$estadoRuta = Join-Path $obra 'huella_fuentes.json'
function Paso($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }

function VersionActual {
    $t = [IO.File]::ReadAllText((Join-Path $raiz '1_codigo\version.py'), $utf8)
    if ($t -notmatch "APP_VERSION = '([\d.]+)'") { throw 'No encontre APP_VERSION en 1_codigo\version.py' }
    return $matches[1]
}

# Huella del CONTENIDO que entra en el .exe: el codigo y los textos se leen enteros; imagenes, fuentes y audios, por nombre y tamano.
function HuellaFuentes {
    $sha = [Security.Cryptography.SHA256]::Create()
    $texto = 'py', 'lua', 'cs', 'txt', 'json', 'spec', 'ps1', 'manifest', 'csv', 'md'
    $archivos = @()
    # herramientas de desarrollo que el programa no usa al correr (consulta de documentacion y MCP de pruebas): cambiarlas NO pide un instalador nuevo
    $archivos += Get-ChildItem -LiteralPath (Join-Path $raiz '1_codigo') -Filter '*.py' -File | Where-Object { @('mapa_codigo.py', 'mcp_cinecaptions.py') -notcontains $_.Name }
    $archivos += Get-ChildItem -LiteralPath (Join-Path $raiz '2_recursos') -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and $_.Name -ne '0_LEEME.txt' }
    foreach ($n in 'Instalador.cs', 'cinecaptions.spec', 'requirements.txt', 'rthook_stanza_stub.py', 'app.manifest', 'banner.jpg') {
        $archivos += Get-Item -LiteralPath (Join-Path $raiz "3_compilar\$n")
    }
    $lineas = New-Object System.Collections.Generic.List[string]
    foreach ($f in ($archivos | Sort-Object FullName)) {
        $rel = $f.FullName.Substring($raiz.Length)
        $ext = $f.Extension.TrimStart('.').ToLowerInvariant()
        if ($texto -contains $ext -and $f.Length -lt 8MB -and $rel -notmatch '\\(version\.py)$') {
            $h = [BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($f.FullName))).Replace('-', '')
        } else { $h = "tam$($f.Length)" }
        $lineas.Add("$rel|$h")
    }
    # version.py cuenta SIN su numero (si no, subir la version contaria como un cambio de codigo)
    $v = [IO.File]::ReadAllText((Join-Path $raiz '1_codigo\version.py'), $utf8) -replace "APP_VERSION = '[\d.]+'", "APP_VERSION = 'X'"
    $lineas.Add('version.py|' + [BitConverter]::ToString($sha.ComputeHash($utf8.GetBytes($v))).Replace('-', ''))
    return [BitConverter]::ToString($sha.ComputeHash($utf8.GetBytes(($lineas -join "`n")))).Replace('-', '')
}

function LeerEstado {
    if (Test-Path -LiteralPath $estadoRuta) { try { return (Get-Content -LiteralPath $estadoRuta -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { } }
    return $null
}

$version = VersionActual
$salida = Join-Path $raiz 'INSTALADORES\Windows'
$exeActual = Join-Path $salida "Instalar_CineCaptions_$version.exe"
Paso 'Mirando si el codigo cambio'
$huella = HuellaFuentes
$estado = LeerEstado
$cambio = (-not $estado) -or ($estado.huella -ne $huella)
$otros = @((@(Get-ChildItem -LiteralPath $salida -Filter 'Instalar_CineCaptions*.exe' -File -ErrorAction SilentlyContinue) + @(Get-ChildItem -LiteralPath $raiz -Filter 'Instalar_CineCaptions*.exe' -File)) | Where-Object { $_.FullName -ne $exeActual })
$alDia = (Test-Path -LiteralPath $exeActual) -and $estado -and ($estado.version -eq $version) -and (-not $cambio) -and ($otros.Count -eq 0)

if ($Comprobar) {
    if ($alDia) { Write-Host "    AL DIA: $(Split-Path $exeActual -Leaf) corresponde al codigo actual (version $version)." -ForegroundColor Green; exit 0 }
    $porque = if (-not (Test-Path -LiteralPath $exeActual)) { "no existe Instalar_CineCaptions_$version.exe" } elseif ($cambio) { 'el codigo cambio despues de la ultima compilacion' } elseif ($otros.Count) { 'hay instaladores viejos en la raiz' } else { 'no hay registro de la ultima compilacion' }
    Write-Host "    DESACTUALIZADO: $porque. Corre Actualizar_Windows.ps1." -ForegroundColor Yellow
    exit 1
}
if ($Registrar) {
    # «el instalador de la raiz YA corresponde a este codigo» (p. ej. tras tocar solo herramientas de desarrollo): anota la huella sin compilar
    if (-not (Test-Path -LiteralPath $exeActual)) { throw "No existe $(Split-Path $exeActual -Leaf): no hay nada que registrar" }
    [IO.File]::WriteAllText($estadoRuta, ('{{"version": "{0}", "huella": "{1}", "fecha": "{2}"}}' -f $version, $huella, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')), $utf8)
    Write-Host "    Registrado: $(Split-Path $exeActual -Leaf) se considera al dia con el codigo actual." -ForegroundColor Green
    exit 0
}
if ($alDia -and -not $Forzar -and -not $Limpio) {
    Write-Host "    Sin cambios desde la version ${version}: $(Split-Path $exeActual -Leaf) ya esta al dia. (-Forzar para recompilar)" -ForegroundColor Green
    exit 0
}

# 2) la version sube sola cuando el codigo cambio sobre una version que ya se compilo (si la subiste tu a mano, se respeta)
if (-not (Test-Path $vpy)) { Write-Host '    (no hay entorno de compilacion todavia: Construir_Instalador.ps1 lo prepara)' }
$subir = (-not $SinSubir) -and $cambio -and $estado -and ($estado.version -eq $version) -and (Test-Path $vpy)
if ($subir) {
    Paso "El codigo cambio desde la version ${version}: subo la version"
    & $vpy (Join-Path $raiz '3_compilar\sincronizar_version.py') --subir
    if ($LASTEXITCODE -ne 0) { throw 'No pude subir la version' }
    $version = VersionActual
} elseif ($estado -and $estado.version -ne $version) {
    Write-Host "    (version $version subida a mano; ultima compilada: $($estado.version))"
}

# 2b) Remotion (animaciones de la Edicion PRO): bundle + runtime (node, renderizador, chrome sin ventana) dentro de 2_recursos
if (Test-Path $vpy) {
    Paso 'Remotion: animaciones de la Edicion PRO'
    & $vpy (Join-Path $raiz '3_compilar\preparar_remotion.py')
    if ($LASTEXITCODE -ne 0) { throw 'No pude preparar Remotion (ver arriba)' }
}

# 3) compilar
Paso "Compilando CineCaptions $version"
$argumentos = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $raiz '3_compilar\Construir_Instalador.ps1'))
if ($Limpio) { $argumentos += '-Limpio' }
if ($SoloInstalador) { $argumentos += '-SoloInstalador' }
& powershell @argumentos
if ($LASTEXITCODE -ne 0) { throw "La compilacion fallo (codigo $LASTEXITCODE): el instalador de la raiz NO se toco" }

# 4) comprobar lo que quedo
Paso 'Comprobando'
$exeNuevo = Join-Path $salida "Instalar_CineCaptions_$version.exe"
if (-not (Test-Path -LiteralPath $exeNuevo)) { throw "No quedo $exeNuevo" }
$fv = (Get-Item -LiteralPath $exeNuevo).VersionInfo.FileVersion
if (-not $fv.StartsWith($version)) { throw "El instalador dice version $fv y el codigo $version" }
$sobran = @((@(Get-ChildItem -LiteralPath $salida -Filter 'Instalar_CineCaptions*.exe' -File) + @(Get-ChildItem -LiteralPath $raiz -Filter 'Instalar_CineCaptions*.exe' -File)) | Where-Object { $_.FullName -ne $exeNuevo })
foreach ($s in $sobran) { [IO.File]::Delete($s.FullName); Write-Host "    quitado: $($s.Name)" }
& $vpy (Join-Path $raiz '3_compilar\sincronizar_version.py') --comprobar
if ($LASTEXITCODE -ne 0) { throw 'Los scripts de Resolve no coinciden con la version del programa' }
$huellaFinal = HuellaFuentes
[IO.File]::WriteAllText($estadoRuta, ('{{"version": "{0}", "huella": "{1}", "fecha": "{2}"}}' -f $version, $huellaFinal, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')), $utf8)
Paso ("LISTO: {0}  ({1:N0} MB)" -f (Split-Path $exeNuevo -Leaf), ((Get-Item -LiteralPath $exeNuevo).Length / 1MB))
Write-Host '    Para Mac: powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1' -ForegroundColor DarkGray
