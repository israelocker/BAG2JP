# Real-ESRGAN one file per process (a long batch ended in VK_ERROR_DEVICE_LOST); retry once.
# usage: esr_each.ps1 [-In in_retry] [-Out out_retry]
param([string]$In = 'in_retry', [string]$Out = 'out_retry')
$W = 'D:\Dev\Recomp\BAG2JP\_work\uipack'
$exe = 'D:\Dev\Tools\realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe'
New-Item -ItemType Directory -Force "$W\$Out" | Out-Null
$files = Get-ChildItem "$W\$In" -Filter *.png
$i = 0
foreach ($f in $files) {
  $i++
  $o = "$W\$Out\$($f.Name)"
  for ($try = 0; $try -lt 2; $try++) {
    & $exe -i $f.FullName -o $o -n realesrgan-x4plus-anime -s 4 -t 128 -f png 2>$null | Out-Null
    if (Test-Path $o) { break }
  }
  "$i/$($files.Count) $($f.Name)" | Out-File -Append "$W\esr_each.log"
}
"DONE" | Out-File -Append "$W\esr_each.log"
