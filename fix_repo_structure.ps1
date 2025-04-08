# PowerShell script to fix the repository structure
# Move files from ReAct/ to the root directory

# Create a temporary directory
$tempDir = "temp_fix"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Clone the repository to get the files from the ReAct folder
git clone https://github.com/kongpop10/ReAct-Nexus.git $tempDir

# Move all files from ReAct/ to the root directory
Get-ChildItem -Path "$tempDir/ReAct" -Force | ForEach-Object {
    $destPath = $_.Name
    if (Test-Path $destPath) {
        Write-Host "Skipping $($_.Name) as it already exists in the root directory"
    } else {
        Write-Host "Moving $($_.Name) to the root directory"
        Copy-Item -Path $_.FullName -Destination $destPath -Recurse -Force
    }
}

# Remove the ReAct folder
Remove-Item -Path "ReAct" -Recurse -Force -ErrorAction SilentlyContinue

# Remove the temporary directory
Remove-Item -Path $tempDir -Recurse -Force

# Add all files to git
git add .

# Commit the changes
git commit -m "Fix repository structure: Move files from ReAct/ to root"

# Push the changes to GitHub
git push -u origin fix-repo-structure

Write-Host "Repository structure fixed successfully. Now create a PR on GitHub to merge these changes into master."
