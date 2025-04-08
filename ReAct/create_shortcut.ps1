# PowerShell script to create a Windows Start Menu shortcut for ReAct Nexus

# Get the current directory where the script is located
$scriptPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$batFilePath = Join-Path -Path $scriptPath -ChildPath "run_react.bat"

# Create the shortcut
$WshShell = New-Object -ComObject WScript.Shell
$startMenuPath = [System.Environment]::GetFolderPath('StartMenu')
$programsPath = Join-Path -Path $startMenuPath -ChildPath "Programs"
$shortcutPath = Join-Path -Path $programsPath -ChildPath "ReAct Nexus.lnk"

$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $batFilePath
$Shortcut.WorkingDirectory = $scriptPath
$Shortcut.Description = "ReAct Nexus - Conversational AI Workspace"
# Use our custom Nexus icon
$iconPath = Join-Path -Path $scriptPath -ChildPath "static\nexus_icon.ico"
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = $iconPath
} else {
    # Try the robot icon as a fallback
    $robotIconPath = Join-Path -Path $scriptPath -ChildPath "static\robot_icon.ico"
    if (Test-Path $robotIconPath) {
        $Shortcut.IconLocation = $robotIconPath
    } else {
        # Fallback to default PowerShell icon if our icons are not found
        $Shortcut.IconLocation = "powershell.exe,0"
    }
}

# Save the shortcut
$Shortcut.Save()

Write-Host "Shortcut created successfully at: $shortcutPath"
Write-Host "You can now launch ReAct Nexus from the Start Menu."
