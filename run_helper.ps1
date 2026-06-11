param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectDir
)

Set-Location -LiteralPath $ProjectDir

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

Write-Info "Project directory: $ProjectDir"

# Determine if a system Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Info "Found system Python: $($python.Source)"
    $pythonPath = $python.Source
} else {
    # Use embeddable Python inside the project folder
    $embedDir = Join-Path $ProjectDir "python-embed"
    $pythonPath = Join-Path $embedDir "python.exe"

    if (-Not (Test-Path $pythonPath)) {
        Write-Info "No system Python found. Preparing embeddable Python in $embedDir"

        # Choose a Python version to download (update as needed)
        $pyVersion = '3.11.8'
        $zipName = "python-$pyVersion-embed-amd64.zip"
        $downloadUrl = "https://www.python.org/ftp/python/$pyVersion/$zipName"

        Write-Info "Downloading embeddable Python $pyVersion..."
        $tmpZip = Join-Path $env:TEMP $zipName
        try {
            Invoke-WebRequest -Uri $downloadUrl -OutFile $tmpZip -UseBasicParsing -ErrorAction Stop
        } catch {
            Write-Err "Failed to download embeddable Python from $downloadUrl. $_"
            exit 2
        }

        New-Item -ItemType Directory -Path $embedDir -Force | Out-Null
        Write-Info "Extracting embeddable Python..."
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($tmpZip, $embedDir)

        # The embeddable package uses python.exe; ensure DLLs are present
        if (-Not (Test-Path $pythonPath)) {
            Write-Err "python.exe not found after extracting embeddable package."
            exit 3
        }

        Write-Info "Embeddable Python prepared."
    } else {
        Write-Info "Using existing embeddable Python at $pythonPath"
    }
}

# Prepare local packages directory inside project
$localPackages = Join-Path $ProjectDir "python-packages"
if (-Not (Test-Path $localPackages)) { New-Item -ItemType Directory -Path $localPackages | Out-Null }

# Ensure pip is available for this python
Write-Info "Ensuring pip is available for $pythonPath"
& $pythonPath -V
& $pythonPath -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Info "pip not found for this Python. Attempting to bootstrap pip..."
    $getPip = Join-Path $ProjectDir "get-pip.py"
    try {
        Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing -ErrorAction Stop
        & $pythonPath $getPip
    } catch {
        Write-Err "Failed to bootstrap pip: $_"
        exit 4
    }
}

# Install requirements into local folder
if (Test-Path (Join-Path $ProjectDir "requirements.txt")) {
    Write-Info "Installing required packages into $localPackages"
    & $pythonPath -m pip install --no-warn-script-location -r (Join-Path $ProjectDir "requirements.txt") --target $localPackages
    if ($LASTEXITCODE -ne 0) {
        Write-Err "pip install failed with exit code $LASTEXITCODE"
        exit 5
    }
} else {
    Write-Info "No requirements.txt found; skipping pip install"
}

# Run the main script with PYTHONPATH set to include local packages
Write-Info "Running download_images.py..."
$env:PYTHONPATH = $localPackages
& $pythonPath (Join-Path $ProjectDir "download_images.py")
$exitCode = $LASTEXITCODE

Write-Info "Process exited with code $exitCode"
exit $exitCode
