# Setup Firewall Logging with Log Rotation
# RUN AS ADMINISTRATOR - Sets up logging + scheduled rotation task

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Windows Firewall Verbose Logging Setup" -ForegroundColor Cyan
Write-Host " WITH Automatic Log Rotation (No Deletion)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$netsh = "$env:SystemRoot\System32\netsh.exe"

# --- Step 1: Create directories ---
Write-Host "`n[1/4] Creating directories..." -ForegroundColor Yellow

$logDir = "C:\Windows\System32\LogFiles\Firewall"
$archiveDir = "$logDir\Archive"
$scriptDir = "C:\ProgramData\FirewallLogRotation"

foreach ($dir in @($logDir, $archiveDir, $scriptDir)) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

# --- Step 2: Configure Firewall Logging ---
Write-Host "`n[2/4] Configuring Windows Firewall logging..." -ForegroundColor Yellow

& $netsh advfirewall set allprofiles logging filename "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
Write-Host "  Set filename: OK" -ForegroundColor Green

& $netsh advfirewall set allprofiles logging maxfilesize 32767
Write-Host "  Set maxfilesize 32MB: OK" -ForegroundColor Green

& $netsh advfirewall set allprofiles logging droppedconnections enable
Write-Host "  Set droppedconnections enable: OK" -ForegroundColor Green

& $netsh advfirewall set allprofiles logging allowedconnections enable
Write-Host "  Set allowedconnections enable: OK" -ForegroundColor Green

# --- Step 3: Copy rotation script to system location ---
Write-Host "`n[3/4] Installing log rotation script..." -ForegroundColor Yellow

$rotationScript = @'
# Firewall Log Rotation Script - Runs every 15 minutes
$logFile = "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
$archiveDir = "C:\Windows\System32\LogFiles\Firewall\Archive"
$maxSizeMB = 30

if (!(Test-Path $archiveDir)) { New-Item -Path $archiveDir -ItemType Directory -Force | Out-Null }

if (Test-Path $logFile) {
    $fileSizeMB = (Get-Item $logFile).Length / 1MB
    if ($fileSizeMB -ge $maxSizeMB) {
        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $archivePath = Join-Path $archiveDir "pfirewall_$timestamp.log"
        Copy-Item -Path $logFile -Destination $archivePath -Force
        Clear-Content -Path $logFile -Force
        Compress-Archive -Path $archivePath -DestinationPath "$archivePath.zip" -Force
        Remove-Item -Path $archivePath -Force
        Add-Content -Path "C:\Windows\System32\LogFiles\Firewall\rotation_history.log" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Rotated $([math]::Round($fileSizeMB,2)) MB to $archivePath.zip"
    }
}
'@

$scriptPath = "$scriptDir\Rotate-FirewallLogs.ps1"
Set-Content -Path $scriptPath -Value $rotationScript -Force
Write-Host "  Installed: $scriptPath" -ForegroundColor Green

# --- Step 4: Create Scheduled Task ---
Write-Host "`n[4/4] Creating scheduled task for log rotation..." -ForegroundColor Yellow

$taskName = "FirewallLogRotation"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create new scheduled task - runs every 15 minutes
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Rotates Windows Firewall logs to prevent overwriting. Archives to compressed files." | Out-Null

Write-Host "  Created scheduled task: $taskName" -ForegroundColor Green

# --- Verification ---
Write-Host "`n========================================" -ForegroundColor Green
Write-Host " SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nFirewall Logging Configuration:" -ForegroundColor Cyan
& $netsh advfirewall show allprofiles logging

Write-Host "`nScheduled Task Status:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName $taskName | Format-Table TaskName, State -AutoSize

Write-Host "`nLog Locations:" -ForegroundColor Cyan
Write-Host "  Active Log:    $logDir\pfirewall.log" -ForegroundColor White
Write-Host "  Archived Logs: $archiveDir\*.zip" -ForegroundColor White
Write-Host "  Rotation Log:  $logDir\rotation_history.log" -ForegroundColor White

Write-Host "`nTo view live logs (run as Admin):" -ForegroundColor Yellow
Write-Host '  Get-Content "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" -Tail 50 -Wait' -ForegroundColor White

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
