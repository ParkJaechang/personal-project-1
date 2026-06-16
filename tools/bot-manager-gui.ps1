$ErrorActionPreference = "Stop"

$ToolRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ToolRoot
$GuiScript = Join-Path $ToolRoot "bot_manager_gui.py"
$Pythonw = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $Pythonw)) {
    $pythonwCommand = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
    if ($pythonwCommand) {
        $Pythonw = $pythonwCommand.Source
    }
}

if (-not (Test-Path $Pythonw)) {
    throw "pythonw.exe not found. Create the project venv or install Python first."
}

Start-Process `
    -FilePath $Pythonw `
    -ArgumentList @($GuiScript) `
    -WorkingDirectory $ProjectRoot
