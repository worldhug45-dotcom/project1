param(
    [string]$Config = "config/settings.local.toml"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "scripts/manual_run.py",
    "status",
    "--config",
    $Config
)

Push-Location $repoRoot
try {
    & python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
