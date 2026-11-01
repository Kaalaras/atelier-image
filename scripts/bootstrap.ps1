param([ValidateSet('setup','start','stop')][string]$Action = 'setup')
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root '.runtime'
$uvFolder = Join-Path $runtime 'uv'
$uv = Join-Path $uvFolder 'uv.exe'
$installLock = $null
try {
    $manifest = Get-Content -LiteralPath (Join-Path $root 'versions.json') -Raw | ConvertFrom-Json
    if ($Action -ne 'setup' -and -not (Test-Path -LiteralPath $uv)) {
        throw 'Installation absente. Lancez Installer.bat en premier.'
    }
    if ($Action -eq 'setup') {
        New-Item -ItemType Directory -Force -Path $runtime | Out-Null
        try {
            $installLock = [IO.File]::Open((Join-Path $runtime 'setup.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        } catch { throw 'Une installation est deja en cours dans ce dossier. Attendez sa fin.' }
    }
    if (-not (Test-Path -LiteralPath $uv)) {
        New-Item -ItemType Directory -Force -Path $runtime | Out-Null
        $archive = Join-Path $runtime 'uv.zip'
        Write-Host 'Preparation de Python portable...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri $manifest.uv.url -OutFile $archive
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.uv.sha256) {
            throw 'Archive uv corrompue (SHA-256). Relancez Installer.bat.'
        }
        Expand-Archive -LiteralPath $archive -DestinationPath $uvFolder -Force
    }
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $runtime 'python'
    $env:UV_CACHE_DIR = Join-Path $runtime 'cache'
    $env:UV_PYTHON_PREFERENCE = 'only-managed'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONUNBUFFERED = '1'
    $env:HF_HUB_DISABLE_TELEMETRY = '1'
    $env:DO_NOT_TRACK = '1'
    & $uv run --no-project --python $manifest.python -- (Join-Path $PSScriptRoot 'manage.py') $Action
    if ($LASTEXITCODE -ne 0) { throw "Operation interrompue (code $LASTEXITCODE). Voir le message ci-dessus." }
} catch {
    Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Vous pouvez relancer Installer.bat. Vos images sont conservees.'
    exit 1
} finally {
    if ($null -ne $installLock) { $installLock.Dispose() }
}
