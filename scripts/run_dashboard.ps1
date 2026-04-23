param(
    [string]$Config = "config/settings.local.toml",
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8787,
    [switch]$ExposeOnLan,
    [switch]$NoBrowser
)

if ($ExposeOnLan) {
    $BindHost = "0.0.0.0"
}

$dashboardHost = switch ($BindHost) {
    "0.0.0.0" { "127.0.0.1" }
    "::" { "localhost" }
    default { $BindHost }
}

$dashboardUrl = "http://{0}:{1}" -f $dashboardHost, $Port
$healthUrl = "{0}/health" -f $dashboardUrl

$repoRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    "-m",
    "app.presentation.web.server",
    "--config",
    $Config,
    "--host",
    $BindHost,
    "--port",
    $Port
)

Write-Host "[dashboard] url: $dashboardUrl"
Write-Host "[dashboard] health: $healthUrl"
if ($ExposeOnLan) {
    Write-Host "[dashboard] lan binding enabled: connect from another device using this PC's IP and port $Port."
}

if (-not $NoBrowser) {
    Write-Host "[dashboard] opening browser automatically..."
    $browserCommand = "Start-Sleep -Seconds 2; Start-Process '$dashboardUrl'"
    Start-Process powershell -ArgumentList @(
        "-NoProfile",
        "-WindowStyle",
        "Hidden",
        "-Command",
        $browserCommand
    ) | Out-Null
}
else {
    Write-Host "[dashboard] browser auto-open disabled."
}

Push-Location $repoRoot
try {
    & python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
