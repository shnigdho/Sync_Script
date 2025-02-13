# FileSync.ps1
# Create log file in the script directory
$LogFile = Join-Path $PSScriptRoot "sync_log.txt"
$LastRunFile = Join-Path $PSScriptRoot "last_run.txt"

# Function to write to log
function Write-Log {
    param($Message)
    $LogMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

# Source and destination paths - MODIFY THESE
$SourcePath = "E:\work_destination"      # Your SSD path
$DestinationPath = "\\user\F\test_server"  # Your network HDD path

# Function to sync deletions
function Sync-Deletions {
    param (
        $SourceDir,
        $DestDir
    )
    
    # Get all files in destination
    $destFiles = Get-ChildItem -Path $DestDir -Recurse -File
    
    foreach ($destFile in $destFiles) {
        # Construct the equivalent source path
        $relativePath = $destFile.FullName.Substring($DestDir.Length)
        $sourcePath = Join-Path $SourceDir $relativePath
        
        # If source doesn't exist, delete from destination
        if (-not (Test-Path $sourcePath)) {
            Remove-Item $destFile.FullName -Force
            Write-Log "Deleted: $($destFile.FullName)"
        }
    }
    
    # Clean up empty directories
    $destDirs = Get-ChildItem -Path $DestDir -Recurse -Directory | Sort-Object FullName -Descending
    foreach ($dir in $destDirs) {
        if ((Get-ChildItem -Path $dir.FullName -Force).Count -eq 0) {
            Remove-Item $dir.FullName -Force
            Write-Log "Removed empty directory: $($dir.FullName)"
        }
    }
}

# Function to perform the sync
function Sync-Folders {
    try {
        # Check if paths exist
        if (-not (Test-Path $SourcePath)) {
            Write-Log "Error: Source path does not exist: $SourcePath"
            return
        }
        if (-not (Test-Path $DestinationPath)) {
            Write-Log "Error: Destination path does not exist: $DestinationPath"
            return
        }

        Write-Log "Starting sync operation..."
        
        # Copy all files from source to destination, including subdirectories
        robocopy $SourcePath $DestinationPath /MIR /FFT /Z /XA:H /W:5 /R:3 /MT:8 /MON:1
        
        # Check robocopy exit code
        switch ($LASTEXITCODE) {
            0 { Write-Log "No files were copied. No failure was encountered." }
            1 { Write-Log "One or more files were copied successfully." }
            2 { Write-Log "Extra files or directories were detected." }
            4 { Write-Log "Some mismatched files or directories were detected." }
            8 { Write-Log "Some files or directories could not be copied." }
            16 { Write-Log "Serious error. Robocopy did not copy any files." }
            default { Write-Log "Unknown error occurred: $LASTEXITCODE" }
        }
        
        # Record last run time
        Get-Date -Format "yyyy-MM-dd HH:mm:ss" | Set-Content $LastRunFile
        
    } catch {
        Write-Log "Error occurred: $_"
    }
}

# Main script execution
Write-Log "File sync service started"
Write-Log "Monitoring $SourcePath"
Write-Log "Syncing to $DestinationPath"

# Initial sync
Sync-Folders

# Keep the script running and monitoring
try {
    while ($true) {
        Start-Sleep -Seconds 10
        Sync-Folders
    }
} catch {
    Write-Log "Error in main loop: $_"
} finally {
    Write-Log "Sync service stopped"
}