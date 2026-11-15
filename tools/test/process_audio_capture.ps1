param([Parameter(Mandatory=$true)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
try {
    Add-Type -Path (Join-Path $PSScriptRoot 'process_audio_capture.cs')
    exit [Bag2ProcessAudio.Capture]::Run($RequestPath)
}
catch {
    [Console]::Error.WriteLine($_.Exception.ToString())
    exit 1
}
