# Windows Startup

This service can be registered as a Windows Scheduled Task so it starts when the user logs in.

## 1. Confirm Manual Run First

Run this from the project root:

```powershell
.\scripts\run-service.ps1
```

Stop it with `Ctrl+C` after Telegram smoke testing succeeds.

## 2. Register Scheduled Task

Open PowerShell as the normal Windows user that should run the bot.

```powershell
$ProjectRoot = "C:\Users\PJC\Documents\SOOP"
$ScriptPath = Join-Path $ProjectRoot "scripts\run-service.ps1"

$Action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
  -TaskName "SOOP Telegram Clip Downloader" `
  -Action $Action `
  -Trigger $Trigger `
  -Settings $Settings `
  -Description "Downloads SOOP User Clips from Telegram messages."
```

## 3. Start or Stop Manually

```powershell
Start-ScheduledTask -TaskName "SOOP Telegram Clip Downloader"
Stop-ScheduledTask -TaskName "SOOP Telegram Clip Downloader"
Get-ScheduledTask -TaskName "SOOP Telegram Clip Downloader"
```

## 4. Update the Service

After pulling new code:

```powershell
cd C:\Users\PJC\Documents\SOOP
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Stop-ScheduledTask -TaskName "SOOP Telegram Clip Downloader"
Start-ScheduledTask -TaskName "SOOP Telegram Clip Downloader"
```

## 5. Remove the Task

```powershell
Unregister-ScheduledTask -TaskName "SOOP Telegram Clip Downloader" -Confirm:$false
```
