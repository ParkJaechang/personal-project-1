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
    throw "Docker is required to run telegram local api. Install Docker Desktop first."
}

$apiId = Get-EnvValue -Name "TELEGRAM_API_ID" -Default ""
$apiHash = Get-EnvValue -Name "TELEGRAM_API_HASH" -Default ""
if (-not $apiId -or -not $apiHash) {
    throw "TELEGRAM_API_ID and TELEGRAM_API_HASH are required for telegram local api."
}

$containerName = Get-EnvValue -Name "TELEGRAM_LOCAL_API_CONTAINER" -Default "pp1-telegram-bot-api"
$port = Get-EnvValue -Name "TELEGRAM_LOCAL_API_PORT" -Default "8081"
$image = Get-EnvValue -Name "TELEGRAM_LOCAL_API_IMAGE" -Default "aiogram/telegram-bot-api:latest"
$dataDirValue = Get-EnvValue -Name "TELEGRAM_LOCAL_API_DATA_DIR" -Default ".local/telegram-bot-api"
$dataDir = if ([System.IO.Path]::IsPathRooted($dataDirValue)) {
    $dataDirValue
} else {
    Join-Path $ProjectRoot $dataDirValue
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$resolvedDataDir = (Resolve-Path $dataDir).Path

$running = & docker inspect -f "{{.State.Running}}" $containerName 2>$null
if ($LASTEXITCODE -eq 0 -and $running -eq "true") {
    Write-Output "telegram-local-api running port=$port container=$containerName limit=2000 MB"
    exit 0
}

$exists = & docker inspect -f "{{.Name}}" $containerName 2>$null
if ($LASTEXITCODE -eq 0) {
    & docker rm $containerName | Out-Null
}

& docker run `
    -d `
    --name $containerName `
    -p "127.0.0.1:$port`:8081" `
    -v "${resolvedDataDir}:/var/lib/telegram-bot-api" `
    $image `
    "--api-id=$apiId" `
    "--api-hash=$apiHash" `
    "--local" `
    "--dir=/var/lib/telegram-bot-api" `
    "--http-ip-address=0.0.0.0" `
    "--http-port=8081" | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to start telegram local api container."
}

Write-Output "telegram-local-api running port=$port container=$containerName limit=2000 MB"
