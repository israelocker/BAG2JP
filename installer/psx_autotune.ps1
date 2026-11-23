param(
    [string]$Toml = "",
    [string]$Exe = "",
    [string]$Proceso = "",
    [switch]$SoloConfigurar,
    [switch]$PlanAlto
)

# psx_autotune: adapta [video] a la maquina y se reajusta solo entre sesiones.
# 1) Detecta GPU, VRAM, nucleos, RAM y Hz.  2) Aplica un perfil.
# 3) Lanza el juego y mide el uso de la GPU.  4) Sube o baja la resolucion para la proxima vez.

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Toml) { $Toml = Join-Path $dir "settings.toml" }
$estadoRuta = Join-Path $dir "autotune_state.json"
$logRuta    = Join-Path $dir "autotune_log.txt"
$anchos     = @(1280, 1920, 2560, 3840)

if (-not (Test-Path $Toml)) {
    Write-Host "No encuentro el archivo de ajustes: $Toml" -ForegroundColor Red
    exit 1
}

# ---------------- 1. Hardware ----------------
$gpus = Get-CimInstance Win32_VideoController |
    Where-Object { $_.Name -notmatch 'Microsoft|Basic|Virtual|Parsec|Remote' }
$gpu = $gpus | Where-Object { $_.Name -match 'NVIDIA|GeForce|RTX|GTX|Radeon RX|Radeon Pro|Arc ' } | Select-Object -First 1
if (-not $gpu) { $gpu = $gpus | Select-Object -First 1 }

$nombre  = if ($gpu) { $gpu.Name } else { "Desconocida" }
$refresh = if ($gpu -and $gpu.CurrentRefreshRate) { [int]$gpu.CurrentRefreshRate } else { 60 }

$vramGB = 0
if ($gpu) {
    $vramGB = [math]::Round($gpu.AdapterRAM / 1GB, 1)
    $base = "HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
        $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ($p.DriverDesc -eq $gpu.Name -and $p.'HardwareInformation.qwMemorySize') {
            $vramGB = [math]::Round([double]$p.'HardwareInformation.qwMemorySize' / 1GB, 1)
        }
    }
}

$cpu     = Get-CimInstance Win32_Processor | Select-Object -First 1
$nucleos = [int]$cpu.NumberOfLogicalProcessors
$ramGB   = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)

$integrada = ($nombre -match 'Intel\(R\) (UHD|HD|Iris)|Radeon\(TM\) Graphics|Radeon Graphics|Vega') -and ($nombre -notmatch 'Radeon RX')

# Nivel maximo permitido por esta maquina (indice en $anchos)
if (-not $gpu -or $integrada -or $vramGB -lt 2) { $maxNivel = 0 }
elseif ($vramGB -lt 4) { $maxNivel = 1 }
elseif ($vramGB -lt 8) { $maxNivel = 2 }
else { $maxNivel = 3 }
if ($nucleos -lt 4 -or $ramGB -lt 8) { $maxNivel = [math]::Min($maxNivel, 1) }

$renderThread = if ($nucleos -ge 4) { "true" } else { "false" }

# ---------------- 2. Estado guardado ----------------
$firma = "$nombre|$nucleos|$ramGB"
$estado = $null
if (Test-Path $estadoRuta) {
    try { $estado = Get-Content $estadoRuta -Raw | ConvertFrom-Json } catch { $estado = $null }
}
if (-not $estado -or $estado.firma -ne $firma) {
    # Maquina nueva o sin historial: empezar en el maximo permitido
    $estado = [pscustomobject]@{ firma = $firma; nivel = $maxNivel; buenas = 0 }
}
$estado.nivel = [math]::Min([int]$estado.nivel, $maxNivel)
$nivel = [int]$estado.nivel
$ancho = $anchos[$nivel]

Write-Host ""
Write-Host "GPU:       $nombre ($vramGB GB)"
Write-Host "CPU:       $nucleos hilos   RAM: $ramGB GB   Monitor: $refresh Hz"
Write-Host "Resolucion elegida: ancho $ancho (nivel $nivel de $maxNivel)" -ForegroundColor Green
if ($refresh -gt 60) {
    Write-Host "Aviso: monitor a $refresh Hz; el juego va a 60 FPS. Si se ve irregular, usa 60 Hz." -ForegroundColor Yellow
}

# ---------------- 3. Aplicar configuracion ----------------
function Aplicar-Config($ruta, $seccion, $cambios) {
    if (-not (Test-Path "$ruta.bak")) { Copy-Item $ruta "$ruta.bak" }
    $lineas = Get-Content $ruta -Encoding UTF8
    $salida = New-Object System.Collections.Generic.List[string]
    $en = $false
    $hechos = @{}
    foreach ($l in $lineas) {
        if ($l -match '^\s*\[(.+)\]\s*$') {
            if ($en) {
                foreach ($k in $cambios.Keys) {
                    if (-not $hechos.ContainsKey($k)) { $salida.Add("$k = $($cambios[$k])") }
                }
            }
            $en = ($Matches[1] -eq $seccion)
            $salida.Add($l)
            continue
        }
        if ($en -and $l -match '^\s*([A-Za-z_]+)\s*=') {
            $k = $Matches[1]
            if ($cambios.Contains($k)) {
                $hechos[$k] = $true
                $salida.Add("$k = $($cambios[$k])")
                continue
            }
        }
        $salida.Add($l)
    }
    if ($en) {
        foreach ($k in $cambios.Keys) {
            if (-not $hechos.ContainsKey($k)) { $salida.Add("$k = $($cambios[$k])") }
        }
    }
    $full = (Resolve-Path $ruta).Path
    [System.IO.File]::WriteAllLines($full, $salida, (New-Object System.Text.UTF8Encoding($false)))
}

$cambios = [ordered]@{
    window_width            = "$ancho"
    fullscreen              = "1"
    render_thread           = $renderThread
    present_thread          = "false"
    frame_generation        = "false"
    vsync                   = '"on"'
    frame_interpolation     = "false"
    frame_interpolation_fps = "0"
}
Aplicar-Config $Toml "video" $cambios

# ---------------- 4. Exe, GPU de alto rendimiento y plan de energia ----------------
if (-not $Exe) {
    $cand = Get-ChildItem $dir -Filter "psxrecomp*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cand) { $Exe = $cand.FullName }
}

if ($Exe -and (Test-Path $Exe)) {
    $Exe = (Resolve-Path $Exe).Path
    try {
        $k = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
        if (-not (Test-Path $k)) { New-Item $k -Force | Out-Null }
        Set-ItemProperty $k -Name $Exe -Value "GpuPreference=2;"
    } catch {}
}

if ($PlanAlto) {
    try { powercfg /setactive SCHEME_MIN | Out-Null } catch {}
}

if ($SoloConfigurar -or -not $Exe -or -not (Test-Path $Exe)) {
    $estado | ConvertTo-Json | Set-Content $estadoRuta
    if (-not $SoloConfigurar) {
        Write-Host "No encontre el ejecutable; solo se aplico la configuracion. Usa -Exe ""ruta\psxrecomp.exe""." -ForegroundColor Yellow
    }
    exit 0
}

# ---------------- 5. Lanzar y medir ----------------
$nombreProc = if ($Proceso) { $Proceso } else { [IO.Path]::GetFileNameWithoutExtension($Exe) }
Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) | Out-Null
Start-Sleep -Seconds 2

$muestras = New-Object System.Collections.Generic.List[double]
$lecturas = 0
$t0 = Get-Date

while ($true) {
    $procs = Get-Process -Name $nombreProc -ErrorAction SilentlyContinue
    if (-not $procs) { break }
    foreach ($pr in $procs) { try { $pr.PriorityClass = 'High' } catch {} }

    if (((Get-Date) - $t0).TotalSeconds -lt 15) { Start-Sleep -Seconds 1; continue }

    $maximo = 0
    foreach ($pr in $procs) {
        $id = $pr.Id
        $c = Get-Counter "\GPU Engine(pid_${id}_*engtype_3D)\Utilization Percentage" -ErrorAction SilentlyContinue
        if ($c) {
            $lecturas++
            $m = ($c.CounterSamples | Measure-Object CookedValue -Maximum).Maximum
            if ($m -gt $maximo) { $maximo = $m }
        }
    }
    $muestras.Add([math]::Min($maximo, 100))
    Start-Sleep -Milliseconds 500
}

# ---------------- 6. Decidir el ajuste para la proxima vez ----------------
$decision = "sin cambios"
if ($lecturas -gt 0 -and $muestras.Count -ge 40) {
    $prom = ($muestras | Measure-Object -Average).Average
    $sat  = ($muestras | Where-Object { $_ -gt 92 }).Count / $muestras.Count

    if ($sat -gt 0.20 -and $nivel -gt 0) {
        $estado.nivel = $nivel - 1
        $estado.buenas = 0
        $decision = "bajo a ancho $($anchos[$estado.nivel]) (GPU saturada)"
    }
    elseif ($sat -lt 0.03 -and $prom -lt 40 -and $nivel -lt $maxNivel) {
        $estado.buenas = [int]$estado.buenas + 1
        if ($estado.buenas -ge 2) {
            $estado.nivel = $nivel + 1
            $estado.buenas = 0
            $decision = "subo a ancho $($anchos[$estado.nivel]) (GPU con margen)"
        } else {
            $decision = "margen detectado, confirmo en otra sesion"
        }
    }
    else {
        $estado.buenas = 0
    }
    $resumen = "GPU prom {0:N0}% | saturada {1:P0}" -f $prom, $sat
} else {
    $resumen = "sesion corta o contador de GPU no disponible; sin medicion"
}

$estado | ConvertTo-Json | Set-Content $estadoRuta
$linea = "{0:yyyy-MM-dd HH:mm} | ancho {1} | {2} | {3}" -f (Get-Date), $ancho, $resumen, $decision
Add-Content $logRuta $linea
Write-Host $linea
