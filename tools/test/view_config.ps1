# Thin JSON bridge only: TOML loading, precedence and path guards live in Python.
function Get-ViewConfig {
    param([string]$Operation,[string]$Output,[string]$LocalConfig,
          [string]$ExpectedExe,[string]$KeyTool,[string]$ShotTool)
    $argv=@('-3.13',(Join-Path $PSScriptRoot 'view_config.py'),'--operation',$Operation,'--output',$Output)
    foreach($pair in @(@('--local-config',$LocalConfig),@('--expected-exe',$ExpectedExe),
                       @('--key-tool',$KeyTool),@('--shot-tool',$ShotTool))) {
        if($pair[1]) { $argv+=@($pair[0],$pair[1]) }
    }
    $encoding=[Console]::OutputEncoding
    try {
        [Console]::OutputEncoding=New-Object System.Text.UTF8Encoding
        $json=& py @argv
        if($LASTEXITCODE -ne 0) { throw 'View configuration rejected' }
    } finally { [Console]::OutputEncoding=$encoding }
    $config=$json | ConvertFrom-Json
    if(!$config.effective) { throw 'Missing effective view configuration' }
    return $config
}
