# Named versus requests with observed-state gates; no runtime changes.
param(
    [ValidateSet('inspect','probe','run')][string]$Action = 'inspect',
    [int]$GameId = 0,
    [string]$Tag = 'versus',
    [string]$P1Character = 'Heat',
    [ValidateSet('BAG1','BAG2')][string]$P1Version = 'BAG2',
    [ValidateSet('A','B')][string]$P1Costume = 'A',
    [string]$P2Character = 'Heat',
    [ValidateSet('BAG1','BAG2')][string]$P2Version = 'BAG2',
    [ValidateSet('A','B')][string]$P2Costume = 'A',
    [ValidateSet('HeatBAG2','HeatBAG1')][string]$Stage = 'HeatBAG2',
    [switch]$TemporaryControls,
    [switch]$Finish,
    [switch]$StageSurvey,
    [double]$FinishTimeout = 420
)
$ErrorActionPreference = 'Stop'
$arguments = @('-3.13', "$PSScriptRoot/versus_session.py", '--action', $Action,
    '--game-id', $GameId, '--tag', $Tag, '--p1-character', $P1Character,
    '--p1-version', $P1Version, '--p1-costume', $P1Costume,
    '--p2-character', $P2Character, '--p2-version', $P2Version,
    '--p2-costume', $P2Costume, '--stage', $Stage)
if ($TemporaryControls) { $arguments += '--temporary-controls' }
if ($StageSurvey) { $arguments += '--stage-survey' }
if ($Finish) { $arguments += '--finish', '--finish-timeout', $FinishTimeout }
& py @arguments
if ($LASTEXITCODE -ne 0) { throw "Versus harness failed (exit $LASTEXITCODE); inspect its result.json" }
