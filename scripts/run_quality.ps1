param()

$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    Write-Host "[quality] format check"
    & python -m ruff format --check app tests scripts
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "[quality] lint check"
    & python -m ruff check app tests scripts
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "[quality] type check"
    & python -m mypy
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
