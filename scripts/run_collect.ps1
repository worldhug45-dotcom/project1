param(
    [string]$Config = "config/settings.local.toml",
    [ValidateSet("api", "fixture")]
    [string]$SourceMode = "api",
    [switch]$CollectDiagnostics
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "scripts/manual_run.py",
    "collect",
    "--config",
    $Config,
    "--source-mode",
    $SourceMode
)

if ($CollectDiagnostics) {
    $arguments += "--collect-diagnostics"
}

Push-Location $repoRoot
try {
    & python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
