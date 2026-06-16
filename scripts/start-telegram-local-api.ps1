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

function Resolve-DockerCommand {
    $docker = Get-Command "docker" -ErrorAction SilentlyContinue
    if ($docker) {
        return $docker.Source
    }

    $defaultDocker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $defaultDocker) {
        return $defaultDocker
    }

    return $null
}

function Invoke-DockerText {
    param(
        [string] $Docker,
        [string[]] $Arguments,
        [int] $TimeoutSeconds = 8
    )

    $job = Start-Job -ScriptBlock {
        param($DockerPath, $DockerArguments)
        $output = & $DockerPath @DockerArguments 2>&1
        [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($output -join "`n")
        }
    } -ArgumentList $Docker, $Arguments

    if (-not (Wait-Job $job -Timeout $TimeoutSeconds)) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -Force -ErrorAction SilentlyContinue
        return [pscustomobject]@{
            ExitCode = 124
            Output = "Docker command timed out"
        }
    }

    $result = Receive-Job $job 2>&1
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    return $result
}

Import-ProjectEnv

$docker = Resolve-DockerCommand
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
$dataVolume = Get-EnvValue -Name "TELEGRAM_LOCAL_API_DATA_VOLUME" -Default "pp1-telegram-bot-api-data"
$downloadDirValue = Get-EnvValue -Name "DOWNLOAD_DIR" -Default "downloads"
$downloadDir = if ([System.IO.Path]::IsPathRooted($downloadDirValue)) {
    $downloadDirValue
} else {
    Join-Path $ProjectRoot $downloadDirValue
}

New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
$resolvedDownloadDir = (Resolve-Path $downloadDir).Path

$version = Invoke-DockerText -Docker $docker -Arguments @("version")
if ($version.ExitCode -ne 0) {
    throw "Docker Desktop is installed but the Docker engine is not running yet. Start Docker Desktop and try again."
}

$runningResult = Invoke-DockerText -Docker $docker -Arguments @("inspect", "-f", "{{.State.Running}}", $containerName)
if ($runningResult.ExitCode -eq 0 -and $runningResult.Output.Trim() -eq "true") {
    Write-Output "telegram-local-api running port=$port container=$containerName limit=2000 MB"
    exit 0
}

$existsResult = Invoke-DockerText -Docker $docker -Arguments @("inspect", "-f", "{{.Name}}", $containerName)
if ($existsResult.ExitCode -eq 0) {
    Invoke-DockerText -Docker $docker -Arguments @("rm", $containerName) | Out-Null
}

& $docker run `
    -d `
    --name $containerName `
    -p "127.0.0.1:$port`:8081" `
    -v "${dataVolume}:/var/lib/telegram-bot-api" `
    -v "${resolvedDownloadDir}:/telegram-files:ro" `
    -e "TELEGRAM_API_ID=$apiId" `
    -e "TELEGRAM_API_HASH=$apiHash" `
    -e "TELEGRAM_LOCAL=1" `
    -e "TELEGRAM_HTTP_IP_ADDRESS=0.0.0.0" `
    -e "TELEGRAM_HTTP_PORT=8081" `
    $image | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to start telegram local api container."
}

Write-Output "telegram-local-api running port=$port container=$containerName limit=2000 MB"
