# Firewall Log Rotation Script
# Runs as scheduled task to archive logs before they're overwritten
# RUN AS ADMINISTRATOR

$logFile = "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
$archiveDir = "C:\Windows\System32\LogFiles\Firewall\Archive"
$maxSizeMB = 30  # Rotate when log reaches 30MB (before 32MB limit)

# Create archive directory if it doesn't exist
if (!(Test-Path $archiveDir)) {
    New-Item -Path $archiveDir -ItemType Directory -Force | Out-Null
}

# Check if log file exists and get its size
if (Test-Path $logFile) {
    $fileSizeMB = (Get-Item $logFile).Length / 1MB
    
    if ($fileSizeMB -ge $maxSizeMB) {
        # Generate timestamp for archive filename
        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $archiveName = "pfirewall_$timestamp.log"
        $archivePath = Join-Path $archiveDir $archiveName
        
        # Copy current log to archive (copy instead of move so Windows can keep writing)
        Copy-Item -Path $logFile -Destination $archivePath -Force
        
        # Clear the current log file (Windows will continue writing to it)
        Clear-Content -Path $logFile -Force
        
        # Compress the archived log to save space
        $compressedPath = "$archivePath.zip"
        Compress-Archive -Path $archivePath -DestinationPath $compressedPath -Force
        Remove-Item -Path $archivePath -Force
        
        # Log the rotation event
        $rotationLog = "C:\Windows\System32\LogFiles\Firewall\rotation_history.log"
        $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Rotated log ($([math]::Round($fileSizeMB, 2)) MB) to $compressedPath"
        Add-Content -Path $rotationLog -Value $logEntry
        
        Write-Host "Log rotated: $compressedPath" -ForegroundColor Green
    }
}
