#
# Tonie API - Automatisches Installationsskript für Windows
#

Write-Host ""
Write-Host "=============================" -ForegroundColor Cyan
Write-Host " Tonie API Installer" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[..] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "[X] $msg" -ForegroundColor Red; exit 1 }

# 1. Python
$python = Get-Command python -ErrorAction SilentlyContinue
$python3 = Get-Command python3 -ErrorAction SilentlyContinue

if (-not $python -and -not $python3) {
    Write-Info "Python wird installiert..."

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    } else {
        Write-Fail "Bitte installiere Python manuell von https://www.python.org/downloads/"
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Success "Python installiert"
} else {
    Write-Success "Python bereits installiert"
}

# 2. pipx
$pipx = Get-Command pipx -ErrorAction SilentlyContinue

if (-not $pipx) {
    Write-Info "pipx wird installiert..."

    $pip = Get-Command pip -ErrorAction SilentlyContinue
    if (-not $pip) { $pip = Get-Command pip3 -ErrorAction SilentlyContinue }

    if ($pip) {
        & $pip.Source install --user pipx
        python -m pipx ensurepath
    } else {
        python -m pip install --user pipx
        python -m pipx ensurepath
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Success "pipx installiert"
} else {
    Write-Success "pipx bereits installiert"
}

# 3. tonie-api
Write-Info "Tonie API wird installiert..."

try {
    pipx install git+https://github.com/Julschik/toniebox-api.git --force 2>$null
} catch {
    python -m pipx install git+https://github.com/Julschik/toniebox-api.git --force 2>$null
}
Write-Success "Tonie API installiert"

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Installation erfolgreich!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 4. Login
Write-Info "Jetzt richten wir deine Zugangsdaten ein..."
Write-Host ""

$loginResult = tonie login
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Alles fertig! Hier ist die Uebersicht:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    tonie --help
    Write-Host ""
    Write-Host "Tipp: Starte mit 'tonie tonies' um deine Tonies zu sehen." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Login uebersprungen. Du kannst spaeter 'tonie login' ausfuehren." -ForegroundColor Yellow
    Write-Host ""
    tonie --help
}
