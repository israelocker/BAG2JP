# Target only the supplied task-owned experimental process. Does not change settings/cards.
param([Parameter(Mandatory=$true)][int]$GameId,
      [ValidateSet('options','selector','cancel','accept')][string]$Action = 'selector',
      [string]$Tag = 'endings-view')
$ErrorActionPreference = 'Stop'
$E = 'D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb'
$Out = "D:/Dev/Recomp/BAG2JP/_work/$Tag"
$Keys = 'D:/Dev/Tools/winshot/postkey.ps1'
if ((Get-Process -Id $GameId).Path -ne "$E/BAG2JP.exe".Replace('/', '\')) { throw 'Not the experimental game process' }
New-Item -ItemType Directory -Force $Out | Out-Null
function State {
    $line = Get-Content "$E/bag2jp_watch.log" -Tail 1
    if ($line -match '8005D3D4=([0-9A-F]+).*80192028=([0-9A-F]+)') {
        return @([Convert]::ToInt32($Matches[1],16), [Convert]::ToInt32($Matches[2],16))
    }
    return @(-1,-1)
}
function Key([string[]]$Names) { & $Keys -Id $GameId -Keys $Names -HoldMs 150 -GapMs 350 | Out-Null }
function WaitRoot([int[]]$Roots, [int]$Seconds=20) {
    $until = (Get-Date).AddSeconds($Seconds)
    do { if ((State)[0] -in $Roots) { return }; Start-Sleep -Milliseconds 200 } while ((Get-Date) -lt $until)
    throw "Expected roots $Roots; observed $(State)"
}
function Shot([string]$Name) {
    $path = "$Out/$Name.png"
    if(Test-Path $path) { $path = "$Out/$Name-$(Get-Date -Format yyyyMMdd-HHmmssfff).png" }
    & 'D:/Dev/Tools/winshot/winshot.ps1' -Ids $GameId -Out $path
}
if ($Action -in @('options','selector')) {
    for($i=0; $i -lt 12 -and (State)[0] -ne 7; $i++) { Key @('Return'); Start-Sleep 2 }
    WaitRoot @(7)
    Start-Sleep -Milliseconds 1200 # root7 starts before the title's fade-in completes
    $target = if($Action -eq 'options') {5} else {4}
    for($i=0; $i -lt 6 -and (State)[1] -ne $target; $i++) { Key @('Down') }
    if((State)[1] -ne $target) { throw 'Menu cursor target not reached' }
    Shot "$Action-selected"
    Key @('S')
    WaitRoot $(if($Action -eq 'options') {@(20)} else {@(12)})
    Start-Sleep $(if($Action -eq 'selector'){6}else{2})
    Shot $Action
} elseif ($Action -eq 'cancel') {
    WaitRoot @(12,13); Key @('X'); WaitRoot @(7) 30; Start-Sleep 1; Shot 'cancel-return'
} elseif ($Action -eq 'accept') {
    WaitRoot @(12,13); Key @('S'); Start-Sleep 1; Shot 'costume';
    Key @('Right','S'); WaitRoot @(26,27) 30; Start-Sleep 12; Shot 'ending'
}
Copy-Item "$E/bag2jp_endings_view.log" "$Out/$Action-plugin.log"
Get-Content "$E/bag2jp_endings_view.log" -Tail 8
"state=$(State)"
