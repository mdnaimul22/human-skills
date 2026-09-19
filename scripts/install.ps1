[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "🚀 Installing human-skills global CLI dispatcher for Windows..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Split-Path -Parent $scriptDir
$execPath = Join-Path $repoDir "skills\helpers\execute.py"

if (-not (Test-Path $execPath)) {
    Write-Error "❌ Error: Could not find execute.py at '$execPath'"
    exit 1
}

$pythonExe = ""
foreach ($cmd in @("python", "python3", "py")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        try {
            $verCheck = & $found.Source -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonExe = $found.Source
                break
            }
        } catch {
        }
    }
}

if (-not $pythonExe) {
    Write-Error "❌ Error: Python 3 (>= 3.8) is required but not found in PATH."
    Write-Host "💡 Please install Python from https://www.python.org/ or via Microsoft Store, and check 'Add Python to PATH'." -ForegroundColor Yellow
    exit 1
}

$pyVer = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "🐍 Detected Python: $pythonExe (v$pyVer)" -ForegroundColor Green

$destDir = Join-Path $env:USERPROFILE ".local\bin"
if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

$cmdFile = Join-Path $destDir "human-skills.cmd"
$psFile = Join-Path $destDir "human-skills.ps1"

$cmdScript = "@echo off`r`n`"$pythonExe`" `"$execPath`" %*`r`n"
[System.IO.File]::WriteAllText($cmdFile, $cmdScript, [System.Text.Encoding]::ASCII)

$psScript = "& `"$pythonExe`" `"$execPath`" `$args`r`n"
[System.IO.File]::WriteAllText($psFile, $psScript, [System.Text.Encoding]::UTF8)

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$paths = $userPath -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

if ($paths -notcontains $destDir) {
    $newPath = if ($userPath) { "$userPath;$destDir" } else { $destDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$destDir;$env:Path"
    Write-Host "🔄 Added $destDir to your Windows User PATH." -ForegroundColor Yellow
} else {
    Write-Host "ℹ️ $destDir is already in User PATH." -ForegroundColor Gray
}

Write-Host "🔍 Verifying installation..." -ForegroundColor Cyan
try {
    & $cmdFile --list | Out-Null
    Write-Host "✅ Verification passed! 'human-skills' command is verified functional." -ForegroundColor Green
} catch {
    Write-Warning "Execution test failed: $_"
}

Write-Host "=================================================================" -ForegroundColor Green
Write-Host "🎉 human-skills installed successfully!" -ForegroundColor Green
Write-Host "📍 Installed wrappers:" -ForegroundColor White
Write-Host "  • CMD:        $cmdFile" -ForegroundColor White
Write-Host "  • PowerShell: $psFile" -ForegroundColor White
Write-Host ""
Write-Host "You can now run 'human-skills' from ANY PowerShell or CMD window:" -ForegroundColor Cyan
Write-Host "  • human-skills --list" -ForegroundColor White
Write-Host "  • human-skills --list-all" -ForegroundColor White
Write-Host "  • human-skills --tool_info tree_gen" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Green
