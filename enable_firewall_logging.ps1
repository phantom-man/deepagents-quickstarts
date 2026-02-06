# Enable Verbose Persistent Windows Firewall Logging
# RUN AS ADMINISTRATOR

Write-Host "Configuring Windows Firewall Logging..." -ForegroundColor Cyan

# Create log directory if needed
$logDir = "C:\Windows\System32\LogFiles\Firewall"
if (!(Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    Write-Host "Created directory: $logDir" -ForegroundColor Yellow
}

# Set log file location for all profiles
netsh advfirewall set allprofiles logging filename "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"

# Set maximum log file size (32MB - maximum allowed)
netsh advfirewall set allprofiles logging maxfilesize 32767

# Enable logging of DROPPED connections (blocked traffic)
netsh advfirewall set allprofiles logging droppedconnections enable

# Enable logging of ALLOWED connections (permitted traffic)
netsh advfirewall set allprofiles logging allowedconnections enable

Write-Host "`n--- Verifying Configuration ---" -ForegroundColor Yellow
netsh advfirewall show allprofiles logging

# Grant read access to Users group
$logFile = "C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
if (Test-Path $logFile) {
    try {
        $acl = Get-Acl $logFile
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Users", "Read", "Allow")
        $acl.AddAccessRule($rule)
        Set-Acl $logFile $acl
        Write-Host "`nRead access granted to Users group" -ForegroundColor Cyan
    } catch {
        Write-Host "`nNote: Could not modify ACL, run log viewer as Admin" -ForegroundColor Yellow
    }
}

Write-Host "`n--- Firewall Logging Enabled! ---" -ForegroundColor Green
Write-Host "Log file location: C:\Windows\System32\LogFiles\Firewall\pfirewall.log" -ForegroundColor White
Write-Host "`nTo view logs in real-time (in this Admin window), run:" -ForegroundColor Cyan
Write-Host '  Get-Content "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" -Tail 50 -Wait' -ForegroundColor White

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
