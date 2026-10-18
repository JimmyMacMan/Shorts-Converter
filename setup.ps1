# ==============================================================================
# Automated Setup Script for Shorts Generator (Windows 10 & 11)
# ==============================================================================

# 1. Ensure script is running with Administrator privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[!] Requesting Administrator privileges..." -ForegroundColor Yellow
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Bind execution path to where this script lives
Set-Location $PSScriptRoot
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Setting up Shorts Generator Environment..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 2. Check and Install Python
$pythonInstalled =$false
try {
    $null = Get-Command python -ErrorAction Stop
    $pythonInstalled =$true
} catch {
    if (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe") {
        $pythonInstalled =$true
    }
}

if ($pythonInstalled) {
    Write-Host "[+] Python is already installed." -ForegroundColor Green
} else {
    Write-Host "[*] Python not found. Installing via winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
}

# 3. Check and Install FFmpeg
$ffmpegInstalled =$false
try {
    $null = Get-Command ffmpeg -ErrorAction Stop
    $ffmpegInstalled =$true
} catch {
    if (Test-Path "C:\ffmpeg\bin\ffmpeg.exe") {
        $ffmpegInstalled =$true
    }
}

if ($ffmpegInstalled) {
    Write-Host "[+] FFmpeg is already installed." -ForegroundColor Green
} else {
    Write-Host "[*] FFmpeg not found. Installing via winget..." -ForegroundColor Yellow
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
}

# 4. Refresh Environment PATH for the current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 5. Create Desktop Shortcut to Drop_Video_Here.bat (using safe string paths)
$batPath = "$PSScriptRoot\Drop_Video_Here.bat"
if (Test-Path $batPath) {$desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = "$desktopPath\Shorts Generator.lnk"
    
    $shell = New-Object -ComObject WScript.Shell;
    $link  = $shell.CreateShortcut($shortcutPath);
    $link.TargetPath       =$batPath;
    $link.WorkingDirectory =$PSScriptRoot;
    $link.Description      = "Drag and drop video files here to generate 30s vertical clips";
    $link.Save();
    
    Write-Host "[+] Desktop shortcut created successfully!" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: 'Drop_Video_Here.bat' not found in $PSScriptRoot. Shortcut skipped." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Setup complete! You can now drag videos onto your Desktop shortcut." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Read-Host -Prompt "Press Enter to exit"