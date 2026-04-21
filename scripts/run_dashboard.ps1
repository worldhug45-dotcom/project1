param(
    [string]$Config = "config/settings.local.toml",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8787
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "-m",
    "app.presentation.web.server",
    "--config",
    $Config,
    "--host",
    $Host,
    "--port",
    $Port
)

Push-Location $repoRoot
try {
    & python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
