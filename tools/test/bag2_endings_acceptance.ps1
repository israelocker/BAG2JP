# One bounded experimental run. Uses the actual Start-Process game PID, unique
# evidence paths and fresh backups; never kills an existing user's game.
param([ValidateSet('Menu','HeatBag1','HeatBag2')][string]$Mode = 'Menu',
      [string]$Tag = 'endings-acceptance', [int]$ObserveSeconds = 42, [string]$LocalConfig = '')
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/view_config.ps1"
$config=Get-ViewConfig -Operation endings-acceptance -Output "$Tag-$(Get-Date -Format yyyyMMdd-HHmmss)" -LocalConfig $LocalConfig
$E=$config.effective.game
$Out=$config.effective.output
$Keys=$config.effective.key_tool
$ShotTool=$config.effective.shot_tool
$ExpectedConfig=@{common=$config.config.common;local=$config.config.local;schema=$config.config.schema;
                 files=$config.files;effective=$config.effective} | ConvertTo-Json -Depth 6 -Compress
if($config.files.local) { $LocalConfig=$config.files.local }
if(Get-Process BAG2JP -ErrorAction SilentlyContinue) { throw 'Existing game session; test refused' }
New-Item -ItemType Directory -Force "$Out/backups" | Out-Null
$Files = @('game.toml','keybinds.ini','mods/state.toml','saves/card1.mcd','saves/card2.mcd')
foreach($f in $Files) {
    if(Test-Path -LiteralPath "$E/$f") { Copy-Item -LiteralPath "$E/$f" -Destination "$Out/backups/$($f.Replace('/','_'))" }
}
function Key([string[]]$Names) { & $Keys -Id $game.Id -Keys $Names -HoldMs 150 -GapMs 550 | Out-Null }
function Shot([string]$Name) { & $ShotTool -Ids $game.Id -Out "$Out/$Name.png" }
function WaitRoot([int]$Expected, [int]$Seconds = 30) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $line = Get-Content -LiteralPath "$E/bag2jp_watch.log" -Tail 1
        if($line -match '8005D3D4=([0-9A-F]+)' -and [Convert]::ToInt32($Matches[1],16) -eq $Expected) { return }
        if($game.HasExited) { throw 'Game exited before expected state' }
        Start-Sleep -Milliseconds 200
    } while((Get-Date) -lt $deadline)
    throw "Timed out waiting for root $Expected; last watch: $line"
}
$game = $null
try {
    $env:BAG2JP_ANIM_TRACE = '1'
    $env:BAG2JP_WATCH = '8005D3D4:4,8005F7CC:1,8005F7C8:4,80192028:4,8005E6A0:4,8005E668:2,8006D9F6:2'
    $env:BAG2JP_AUDIO_DUMP = '1'
    $game = Start-Process "$E/BAG2JP.exe" -WorkingDirectory $E -ArgumentList '--no-launcher' -PassThru
    $game.Id | Set-Content -LiteralPath "$Out/game-pid.txt"
    Write-Output "game_pid=$($game.Id) evidence=$Out"
    Start-Sleep 18
    if($Mode -eq 'Menu') {
        & "$PSScriptRoot/bag2_endings_view.ps1" -GameId $game.Id -Action options -Tag $Out -LocalConfig $LocalConfig -ExpectedConfig $ExpectedConfig
        Key @('X'); WaitRoot 7
    }
    & "$PSScriptRoot/bag2_endings_view.ps1" -GameId $game.Id -Action selector -Tag $Out -LocalConfig $LocalConfig -ExpectedConfig $ExpectedConfig
    Key @('S'); Start-Sleep -Milliseconds 700
    Shot 'heat-version-costume'
    if($Mode -eq 'Menu') {
        Key @('X')
        & "$PSScriptRoot/bag2_endings_view.ps1" -GameId $game.Id -Action cancel -Tag $Out -LocalConfig $LocalConfig -ExpectedConfig $ExpectedConfig
    } else {
        $open = Get-Content -LiteralPath "$E/bag2jp_charsel_popup.log" | Select-String 'open:.*current (\d+)' | Select-Object -Last 1
        if(!$open) { throw 'No observed Heat version popup' }
        $version = [int]$open.Matches[0].Groups[1].Value
        $wanted = if($Mode -eq 'HeatBag1') {1} else {0}
        if($version -ne $wanted) { Key @('Right') }
        Shot 'chosen-version'
        Key @('S'); WaitRoot 27
        Start-Sleep 9; Shot 'movie-09s'
        Start-Sleep 8; Shot 'movie-17s'
        if($ObserveSeconds -gt 17) { Start-Sleep ($ObserveSeconds - 17) }
        Shot 'credits-or-return'
    }
} finally {
    if($game -and !$game.HasExited) {
        $null = $game.CloseMainWindow()
        if(!$game.WaitForExit(15000)) { throw 'Task game did not close; not restoring files while it runs' }
    }
    foreach($name in @('bag2jp_endings_view.log','bag2jp_charsel_popup.log','bag2jp_bag1_endings.log',
                      'bag2jp_hd_intro.log','bag2jp_watch.log','bag2jp_audio.wav','bag2jp_audio_sync.log')) {
        if(Test-Path -LiteralPath "$E/$name") { Copy-Item -LiteralPath "$E/$name" -Destination "$Out/$name" }
    }
    $checks = @(foreach($f in $Files) {
        $backup = "$Out/backups/$($f.Replace('/','_'))"
        if(Test-Path -LiteralPath $backup) {
            $same = (Get-FileHash -LiteralPath "$E/$f").Hash -eq (Get-FileHash -LiteralPath $backup).Hash
            if(!$same) { Copy-Item -LiteralPath "$E/$f" -Destination "$backup.after-test"; Copy-Item -LiteralPath $backup -Destination "$E/$f" }
            @{file=$f; unchanged=$same; preserved=((Get-FileHash -LiteralPath "$E/$f").Hash -eq (Get-FileHash -LiteralPath $backup).Hash)}
        }
    })
    $checks | ConvertTo-Json | Set-Content -LiteralPath "$Out/preservation.json"
    Write-Output "evidence=$Out preservation=$($checks | ConvertTo-Json -Compress)"
}
