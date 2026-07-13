# Project Layout and Shared Configuration Design

## Goal

Separate backend source code from root-level launchers and runtime assets, centralize local service defaults in one JSON file, and provide double-clickable CMD wrappers for both backend and frontend.

## Target layout

```text
speach2speach/
├─ backend/
│  ├─ run_s2s.py
│  ├─ s2s_runtime/
│  └─ tests/
├─ hf-realtime-voice/
├─ models/
├─ .cache/
├─ venv/
├─ voice-config.json
├─ start-voice-backend.ps1
├─ start-voice-backend-menu.cmd
├─ start-voice-frontend.ps1
└─ start-voice-frontend.cmd
```

`hf-realtime-voice` keeps its existing name and contents. Models, caches, the shared virtual environment, documentation, and launchers remain at the project root.

## Shared configuration

`voice-config.json` contains:

```json
{
  "lmStudio": {
    "baseUrl": "http://127.0.0.1:1234/v1",
    "model": "qwen/qwen3-4b-2507"
  },
  "backend": {
    "port": 8765
  },
  "frontend": {
    "port": 7860
  }
}
```

Both PowerShell launchers require this file and validate required values. Explicit command-line parameters override JSON defaults. The frontend derives its default WebSocket URL as `ws://127.0.0.1:<backend.port>/v1/realtime`; an explicit `-SpeechToSpeechUrl` still overrides the derived URL.

## Backend launcher

`start-voice-backend.ps1` resolves `backend/run_s2s.py`, reads the LM Studio base URL and model from JSON, and uses the configured backend port unless `-BackendPort` is supplied. Existing device, CPU profile, online/offline, model, cache, and environment behavior remains unchanged.

`start-voice-backend-menu.cmd` selects CPU fast, CPU quality, or GPU without hard-coding a port, allowing the PowerShell launcher to use JSON configuration.

## Frontend launcher

`start-voice-frontend.ps1` uses the configured frontend port unless `-Port` is supplied and derives its backend WebSocket URL unless `-SpeechToSpeechUrl` is supplied. Error text refers to the renamed `start-voice-frontend.ps1`.

`start-voice-frontend.cmd` invokes the PowerShell frontend launcher from the project root, captures its exit code, and pauses after exit.

## Backend relocation

`run_s2s.py`, `s2s_runtime/`, and `tests/` move under `backend/`. `run_s2s.py` resolves the project root as its parent directory's parent so `.cache` remains root-relative. Tests run with `backend` as their import root and continue importing `s2s_runtime` without changing application package names.

## Validation

- Parse `voice-config.json` and assert required values and port ranges.
- Parse both PowerShell scripts without starting services.
- Statically assert launcher paths, override behavior, mode mappings, and CMD targets.
- Run all backend unit tests from the relocated directory.
- Do not start LM Studio, load speech models, or occupy service ports during verification.
