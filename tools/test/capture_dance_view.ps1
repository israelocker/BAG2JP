# Capture selected native Dance View actions from an observed playlist/index state.
param([Parameter(Mandatory)][int]$GameId,[Parameter(Mandatory)][string]$ExpectedExe,
 [Parameter(Mandatory)][string]$Cases,[Parameter(Mandatory)][string]$Output,
 [Parameter(Mandatory)][int]$CurrentIndex,[Parameter(Mandatory)][int]$ItemCount,
 [string]$ConfirmKey='X',[string]$WatchLog='',[string]$IndexAddress='801BFA98',[string]$KeyTool='',
 [string]$ShotTool='', [string]$LocalConfig='')
$ErrorActionPreference='Stop'
. "$PSScriptRoot/view_config.ps1"
$config=Get-ViewConfig -Operation dance-capture -Output $Output -LocalConfig $LocalConfig -ExpectedExe $ExpectedExe -KeyTool $KeyTool -ShotTool $ShotTool
$Output=$config.effective.output
$ExpectedExe=$config.effective.exe
$KeyTool=$config.effective.key_tool
$ShotTool=$config.effective.shot_tool
$game=Get-Process -Id $GameId
if ([IO.Path]::GetFullPath($game.Path) -ne [IO.Path]::GetFullPath($ExpectedExe)) { throw 'Unexpected game process' }
if ($ItemCount -lt 2 -or $CurrentIndex -lt 0 -or $CurrentIndex -ge $ItemCount) { throw 'Invalid viewer index contract' }
if (Test-Path -LiteralPath $Output) { throw 'Preserve existing capture output' }
$items=@(Get-Content -LiteralPath $Cases -Raw | ConvertFrom-Json)
if ($items.Count -eq 1 -and $items[0] -is [Array]) { $items=$items[0] }
foreach ($item in $items) {
 if ($item.index -lt 0 -or $item.index -ge $ItemCount -or $item.name -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid capture case' }
}
function Read-ViewerIndex {
 $line=Get-Content -LiteralPath $WatchLog -Tail 1
 if ($line -notmatch ($IndexAddress+'=([0-9A-Fa-f]+)(?: |$)')) { throw 'Viewer index watch unavailable' }
 $value=[Convert]::ToInt32($matches[1],16)
 if ($value -eq 65535) { return $ItemCount-1 }
 if ($value -ge $ItemCount) { throw 'Viewer index out of bounds' }
 return $value
}
if ($IndexAddress -notmatch '^[0-9A-Fa-f]{8}$') { throw 'Invalid watch address' }
New-Item -ItemType Directory -Path $Output | Out-Null
$timeline=@();$cursor=$CurrentIndex
foreach ($item in $items) {
 $step=([int]$item.index-$cursor+$ItemCount)%$ItemCount;$key='Right'
 if ($step -gt $ItemCount/2) { $step=$ItemCount-$step;$key='Left' }
 if ($WatchLog) {
  $attempt=0
  while (($cursor=Read-ViewerIndex) -ne [int]$item.index) {
   if (++$attempt -gt 2*$ItemCount) { throw 'Viewer navigation did not converge' }
   $distance=([int]$item.index-$cursor+$ItemCount)%$ItemCount
   $key=if ($distance -gt $ItemCount/2) { 'Left' } else { 'Right' }
   & $KeyTool -Id $GameId -Keys $key -HoldMs 40 -GapMs 180 | Out-Null
  }
 } else {
 for ($i=0;$i -lt $step;$i++) { & $KeyTool -Id $GameId -Keys $key -HoldMs 70 -GapMs 100 | Out-Null }
 }

 & $KeyTool -Id $GameId -Keys $ConfirmKey -HoldMs 70 -GapMs 100 | Out-Null
 for ($sample=0;$sample -lt 3;$sample++) {
  Start-Sleep -Milliseconds 700
  $path=Join-Path $Output ('{0:D2}-{1}-{2}.png' -f [int]$item.index,$item.name,$sample)
  & $ShotTool -Ids $GameId -Out $path -Screen | Out-Null
 }
 $timeline += [pscustomobject]@{index=[int]$item.index;name=$item.name;samples=3;game_id=$GameId;index_verified=[bool]$WatchLog}
 $timeline | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Output 'timeline.json')
 $cursor=[int]$item.index
 Write-Output ('Captured '+$item.name+' at index '+$cursor)
}
