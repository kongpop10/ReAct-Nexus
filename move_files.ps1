# PowerShell script to move files from ReAct/ to the root directory

# Get all files and directories in the ReAct folder
$items = Get-ChildItem -Path "ReAct" -Force

# Move each item to the root directory
foreach ($item in $items) {
    $destPath = Join-Path -Path "." -ChildPath $item.Name
    
    # Check if the destination already exists
    if (Test-Path $destPath) {
        Write-Host "Skipping $($item.Name) as it already exists in the root directory"
    } else {
        Write-Host "Moving $($item.Name) to the root directory"
        Copy-Item -Path $item.FullName -Destination $destPath -Recurse -Force
    }
}

# Add all files to git
git add .

# Commit the changes
git commit -m "Move files from ReAct/ to root directory"

Write-Host "Files moved successfully. Now you can delete the ReAct folder and push the changes."
