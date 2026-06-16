$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"

function Import-ProjectEnv {
    if (-not (Test-Path $EnvFile)) {
        return
    }

    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $name, $value = $line.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($name) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

function Get-EnvValue {
    param(
        [string] $Name,
        [string] $Default
    )

    $value = [Environment]::GetEnvironmentVariable($Name)
    if ($value) {
        return $value
    }
    return $Default
}

Import-ProjectEnv

$docker = Get-Command "docker" -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Output "telegram-local-api already stopped (Docker not found)"
    exit 0
}

$containerName = Get-EnvValue -Name "TELEGRAM_LOCAL_API_CONTAINER" -Default "pp1-telegram-bot-api"
$status = & docker inspect -f "{{.State.Status}}" $containerName 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Output "telegram-local-api already stopped"
    exit 0
}

if ($status -eq "running") {
    & docker stop $containerName | Out-Null
    Write-Output "telegram-local-api stopped container=$containerName"
    exit 0
}

Write-Output "telegram-local-api already $status container=$containerName"
