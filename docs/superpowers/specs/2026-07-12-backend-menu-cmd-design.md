# Backend Menu CMD Design

## Goal

Add one double-clickable CMD entry point that lets the user select the existing backend's fast CPU, quality CPU, or GPU mode.

## Interface

The script displays three numbered choices:

1. CPU fast: `-Device cpu -CpuProfile fast -BackendPort 8765`
2. CPU quality: `-Device cpu -CpuProfile quality -BackendPort 8765`
3. GPU: `-Device gpu -CpuProfile quality -BackendPort 8765`

The script accepts `1`, `2`, or `3`. Invalid input returns to the menu.

## Execution

The CMD file changes to its own directory and invokes `start-voice-backend.ps1` through `powershell.exe -NoProfile -ExecutionPolicy Bypass`. Backend setup, validation, and error handling remain in the PowerShell script.

After the backend exits, the CMD window displays its exit code and pauses so errors remain visible.

## Verification

Static checks confirm that all three menu branches pass the intended arguments, quote paths safely, and target the existing PowerShell script. The backend will not be launched during verification because doing so loads large speech models and occupies port 8765.
