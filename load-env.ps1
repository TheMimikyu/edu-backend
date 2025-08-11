param(
    [string]$Path = ".env"
)

if (-not (Test-Path $Path)) {
    Write-Host "No .env file found at $Path" -ForegroundColor Yellow
    exit 1
}

Get-Content $Path | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        $name  = $matches[1].Trim()
        $value = $matches[2].Trim('"').Trim("'")
        ${env:$name} = $value
        Write-Host "Loaded $name" -ForegroundColor Green
    }
}
