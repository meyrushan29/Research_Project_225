Write-Host "=== Fix Flutter Connection Issues ===" -ForegroundColor Cyan

# 1. Add Firewall Rule for Port 8000 (Requires Admin)
Write-Host "`n1. Attempting to unblock Port 8000 in Firewall..."
try {
    # Remove old rule if exists to ensure clean slate
    Remove-NetFirewallRule -DisplayName "Allow FastAPI Backend" -ErrorAction SilentlyContinue
    
    # Create new permissive rule
    New-NetFirewallRule -DisplayName "Allow FastAPI Backend" `
                        -Direction Inbound `
                        -LocalPort 8000 `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Any `
                        -Description "Allows development server access from Emulator" `
                        -ErrorAction Stop
                        
    Write-Host "   SUCCESS: Added firewall rule for Port 8000 (All Profiles)." -ForegroundColor Green
} catch {
    Write-Host "   WARNING: Could not add firewall rule automatically." -ForegroundColor Yellow
    Write-Host "   Please run this script as Administrator!" -ForegroundColor Red
}

# 2. Config ADB Reverse (Tunnel localhost:8000 emulator -> localhost:8000 host)
Write-Host "`n2. Setting up ADB reverse tunnel..."

# Check if adb is in path
if (-not (Get-Command "adb" -ErrorAction SilentlyContinue)) {
    $adbPath = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $adbPath) {
        $env:Path += ";$env:LOCALAPPDATA\Android\Sdk\platform-tools"
        Write-Host "   Added ADB to path."
    }
}

try {
    Write-Host "   Resetting ADB server..."
    cmd /c "adb kill-server"
    cmd /c "adb start-server"
    
    Write-Host "   Waiting for device..."
    cmd /c "adb wait-for-device"
    
    # Check for connected devices
    $devices = cmd /c "adb devices"
    Write-Host $devices
    
    if ($devices -match "emulator") {
        Write-Host "   Applying Reverse Tunnel..."
        cmd /c "adb reverse tcp:8000 tcp:8000"
        
        # VERIFY
        $reverseList = cmd /c "adb reverse --list"
        Write-Host "`n   Current Tunnels:"
        Write-Host $reverseList -ForegroundColor Cyan
        
        if ($reverseList -match "tcp:8000") {
            Write-Host "   SUCCESS: Port 8000 is now tunneled." -ForegroundColor Green
        } else {
             Write-Host "   ERROR: Tunnel command ran but port 8000 is not listed!" -ForegroundColor Red
        }
    } else {
         Write-Host "   WARNING: No Emulator found running. Please start the emulator first!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR: Failed to run ADB command." -ForegroundColor Red
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Please restart your Flutter app and try uploading again."
