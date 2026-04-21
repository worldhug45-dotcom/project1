param(
    [string]$Config = "config/settings.local.toml",
    [ValidateSet("api", "fixture")]
    [string]$SourceMode = "api"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "scripts/manual_run.py",
    "observe",
    "--config",
    $Config,
    "--source-mode",
    $SourceMode
)

Push-Location $repoRoot
try {
    & python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
