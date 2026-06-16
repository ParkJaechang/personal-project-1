param(
    [string] $ShortcutName = "soop tools.lnk"
)

$ErrorActionPreference = "Stop"

$ToolRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ToolRoot
$GuiScript = Join-Path $ToolRoot "bot_manager_gui.py"
$Pythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$Desktop = [Environment]::GetFolderPath("Desktop")
if (-not $ShortcutName.EndsWith(".lnk", [System.StringComparison]::OrdinalIgnoreCase)) {
    $ShortcutName = "$ShortcutName.lnk"
}
$ShortcutPath = Join-Path $Desktop $ShortcutName

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)

if (Test-Path $Pythonw) {
    $shortcut.TargetPath = $Pythonw
    $shortcut.Arguments = "`"$GuiScript`""
} else {
    $launcher = Join-Path $ToolRoot "bot-manager-gui.ps1"
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`""
}

$shortcut.WorkingDirectory = $ProjectRoot
$shortcut.Description = "Open soop tools."
$shortcut.Save()

Write-Output $ShortcutPath
