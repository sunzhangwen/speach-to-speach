[CmdletBinding()]
param(
    [ValidateSet("cpu", "gpu")]
    [string]$Device = "cpu",

    [ValidateSet("quality", "fast")]
    [string]$CpuProfile = "quality",

    [ValidateRange(1, 65535)]
    [Nullable[int]]$BackendPort,

    [switch]$Online
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$ConfigPath = Join-Path $ProjectRoot "voice-config.json"
$BackendRoot = Join-Path $ProjectRoot "backend"
$ActivateScript = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$Launcher = Join-Path $BackendRoot "run_s2s.py"
$WhisperModel = Join-Path $ProjectRoot "models\whisper-large-v3"
$FasterWhisperModel = Join-Path $ProjectRoot "models\faster-whisper-small"
$QwenTtsModel = Join-Path $ProjectRoot "models\Qwen3-TTS-12Hz-1.7B-CustomVoice"

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Missing project configuration file: $ConfigPath"
}

try {
    $Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
} catch {
    throw "Invalid JSON in project configuration file '$ConfigPath': $($_.Exception.Message)"
}

$ConfiguredBackendPort = $Config.backend.port
$LmStudioBaseUrl = [string]$Config.lmStudio.baseUrl
$LmStudioModel = [string]$Config.lmStudio.model

if ($null -eq $ConfiguredBackendPort -or [int]$ConfiguredBackendPort -lt 1 -or [int]$ConfiguredBackendPort -gt 65535) {
    throw "voice-config.json backend.port must be an integer from 1 to 65535."
}
if ([string]::IsNullOrWhiteSpace($LmStudioBaseUrl)) {
    throw "voice-config.json lmStudio.baseUrl must not be empty."
}
$parsedLmStudioUri = $null
if (-not [Uri]::TryCreate($LmStudioBaseUrl, [UriKind]::Absolute, [ref]$parsedLmStudioUri) -or
    $parsedLmStudioUri.Scheme -notin @("http", "https")) {
    throw "voice-config.json lmStudio.baseUrl must be an absolute HTTP or HTTPS URL."
}
if ([string]::IsNullOrWhiteSpace($LmStudioModel)) {
    throw "voice-config.json lmStudio.model must not be empty."
}
if (-not $PSBoundParameters.ContainsKey("BackendPort")) {
    $BackendPort = [int]$ConfiguredBackendPort
}

$requiredPaths = @(
    $ActivateScript
    $Python
    $Launcher
    (Join-Path $QwenTtsModel "model.safetensors")
    (Join-Path $QwenTtsModel "speech_tokenizer\model.safetensors")
    (Join-Path $ProjectRoot ".cache\torch\hub\snakers4_silero-vad_master")
    (Join-Path $ProjectRoot ".cache\nltk_data\tokenizers\punkt_tab")
)

if ($Device -eq "cpu" -and $CpuProfile -eq "fast") {
    $requiredPaths += Join-Path $FasterWhisperModel "model.bin"
} else {
    $requiredPaths += Join-Path $WhisperModel "model.safetensors"
}

foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing required project file: $path"
    }
}

. $ActivateScript

$portProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $BackendPort)
try {
    $portProbe.Start()
} catch {
    throw "Voice backend port $BackendPort is already in use. Stop the existing backend or run with -BackendPort followed by a free port."
} finally {
    $portProbe.Stop()
}

$env:HF_HOME = Join-Path $ProjectRoot ".cache\huggingface"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"
$env:TORCH_HOME = Join-Path $ProjectRoot ".cache\torch"
$env:NLTK_DATA = Join-Path $ProjectRoot ".cache\nltk_data"

if ($Online) {
    Remove-Item Env:HF_HUB_OFFLINE -ErrorAction SilentlyContinue
    Remove-Item Env:TRANSFORMERS_OFFLINE -ErrorAction SilentlyContinue
} else {
    $env:HF_HUB_OFFLINE = "1"
    $env:TRANSFORMERS_OFFLINE = "1"
}

$RuntimeDevice = if ($Device -eq "gpu") { "cuda" } else { "cpu" }
$SttDtype = if ($Device -eq "gpu") { "float16" } else { "float32" }
$TtsDtype = if ($Device -eq "gpu") { "auto" } else { "float32" }
$SttBackend = if ($Device -eq "cpu" -and $CpuProfile -eq "fast") { "faster-whisper" } else { "whisper" }

if ($Device -eq "gpu") {
    & $Python -c "import sys, torch; sys.exit(0 if torch.cuda.is_available() else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "GPU mode requires a CUDA-enabled PyTorch installation and a supported NVIDIA GPU."
    }
}

$preflightBody = @{
    model = $LmStudioModel
    input = "Reply with OK."
    max_output_tokens = 8
    stream = $false
} | ConvertTo-Json

try {
    $null = Invoke-RestMethod `
        -Method Post `
        -Uri "$LmStudioBaseUrl/responses" `
        -ContentType "application/json" `
        -Body $preflightBody `
        -TimeoutSec 60
} catch {
    throw "LM Studio preflight failed at $LmStudioBaseUrl/responses for model '$LmStudioModel': $($_.Exception.Message) Start the LM Studio server, load the model, and verify its Responses API before retrying."
}

$arguments = @(
    $Launcher
    "--mode", "realtime"
    "--ws_port", $BackendPort
    "--device", $RuntimeDevice
    "--stt", $SttBackend
    "--language", "zh"
    "--llm_backend", "responses-api"
    "--model_name", $LmStudioModel
    "--responses_api_base_url", $LmStudioBaseUrl
    "--responses_api_api_key", "none"
    "--responses_api_stream"
    "--stream_batch_sentences", "1"
    "--tts", "qwen3"
    "--qwen3_tts_model_name", $QwenTtsModel
    "--qwen3_tts_device", $RuntimeDevice
    "--qwen3_tts_dtype", $TtsDtype
    "--qwen3_tts_language", "zh"
    "--qwen3_tts_backend", "torch"
    "--enable_live_transcription"
    "--thresh", "0.2"
    "--min_silence_ms", "1000"
    "--speech_pad_ms", "500"
    "--speculative_reopen_ms", "4000"
    "--unanswered_reopen_ms", "12000"
    "--log_level", "info"
)

if ($SttBackend -eq "faster-whisper") {
    $arguments += @(
        "--faster_whisper_stt_model_name", $FasterWhisperModel
        "--faster_whisper_stt_device", "cpu"
        "--faster_whisper_stt_compute_type", "int8"
        "--faster_whisper_stt_gen_language", "zh"
        "--faster_whisper_stt_gen_beam_size", "1"
    )
} else {
    $arguments += @(
        "--stt_model_name", $WhisperModel
        "--stt_torch_dtype", $SttDtype
    )
}

Write-Host "Starting speech-to-speech in $Device mode ($RuntimeDevice), STT profile: $CpuProfile ($SttBackend)."
& $Python @arguments

exit $LASTEXITCODE
