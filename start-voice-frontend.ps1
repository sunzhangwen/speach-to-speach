[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [Nullable[int]]$Port,

    [string]$SpeechToSpeechUrl
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$ConfigPath = Join-Path $ProjectRoot "voice-config.json"
$ActivateScript = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$UiRoot = Join-Path $ProjectRoot "hf-realtime-voice"
$UiServer = Join-Path $UiRoot "server.py"

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Missing project configuration file: $ConfigPath"
}

try {
    $Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
} catch {
    throw "Invalid JSON in project configuration file '$ConfigPath': $($_.Exception.Message)"
}

$ConfiguredFrontendPort = $Config.frontend.port
$ConfiguredBackendPort = $Config.backend.port
foreach ($portSetting in @(
    @{ Name = "frontend.port"; Value = $ConfiguredFrontendPort },
    @{ Name = "backend.port"; Value = $ConfiguredBackendPort }
)) {
    if ($null -eq $portSetting.Value -or [int]$portSetting.Value -lt 1 -or [int]$portSetting.Value -gt 65535) {
        throw "voice-config.json $($portSetting.Name) must be an integer from 1 to 65535."
    }
}
if (-not $PSBoundParameters.ContainsKey("Port")) {
    $Port = [int]$ConfiguredFrontendPort
}
if (-not $PSBoundParameters.ContainsKey("SpeechToSpeechUrl")) {
    $SpeechToSpeechUrl = "ws://127.0.0.1:$ConfiguredBackendPort/v1/realtime"
}

$requiredPaths = @(
    $ActivateScript
    $Python
    $UiRoot
    $UiServer
    (Join-Path $UiRoot "index.html")
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required UI file: $path"
    }
}

. $ActivateScript

$portProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
try {
    $portProbe.Start()
} catch {
    $owner = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty OwningProcess
    $ownerText = if ($owner) { " Process ID: $owner." } else { "" }
    throw "UI port $Port is already in use.$ownerText Stop the existing process or run: .\start-voice-frontend.ps1 -Port $($Port + 1)"
} finally {
    $portProbe.Stop()
}

& $Python -c "import fastapi, uvicorn"
if ($LASTEXITCODE -ne 0) {
    throw "The UI requires fastapi and uvicorn in the project virtual environment."
}

$env:SPEECH_TO_SPEECH_URL = $SpeechToSpeechUrl

Write-Host "Starting the speech-to-speech web UI."
Write-Host "UI:      http://localhost:$Port/"
Write-Host "Backend: $SpeechToSpeechUrl"
Write-Host "Keep start-voice-backend.ps1 running in another PowerShell window."

Push-Location $UiRoot
try {
    & $Python -m uvicorn server:app --host 127.0.0.1 --port $Port
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
