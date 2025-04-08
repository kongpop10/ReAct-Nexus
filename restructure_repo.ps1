# PowerShell script to restructure the repository
# Move files from ReAct/ to the root directory

# Create a new branch for restructuring
git checkout -b restructure-root

# Create a temporary directory to store the files
$tempDir = "temp_restructure"
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

# Remove the temporary directory
Remove-Item -Path $tempDir -Recurse -Force

# Add all files to git
git add .

# Commit the changes
git commit -m "Restructure repository: Move files from ReAct/ to root"

# Push the changes to GitHub
git push -u origin restructure-root

Write-Host "Repository restructured successfully. Now create a PR on GitHub to merge these changes into master."
