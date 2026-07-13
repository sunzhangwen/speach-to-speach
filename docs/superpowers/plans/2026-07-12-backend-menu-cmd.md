# Backend Menu CMD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create one double-clickable CMD menu for starting the voice backend in CPU fast, CPU quality, or GPU mode.

**Architecture:** A thin CMD wrapper owns menu selection only and delegates all validation and backend lifecycle behavior to `start-voice-backend.ps1`. Every mode uses port 8765 and preserves the console after the backend exits.

**Tech Stack:** Windows CMD, Windows PowerShell

## Global Constraints

- Keep `start-voice-backend.ps1` unchanged.
- Use `powershell.exe -NoProfile -ExecutionPolicy Bypass` only for the launched process.
- Do not launch the model during static verification.

---

### Task 1: Backend mode menu

**Files:**
- Create: `start-voice-backend-menu.cmd`

**Interfaces:**
- Consumes: `start-voice-backend.ps1` parameters `Device`, `CpuProfile`, and `BackendPort`.
- Produces: numbered interactive choices `1`, `2`, and `3`.

- [ ] **Step 1: Confirm the target does not already exist**

Run: `Test-Path .\start-voice-backend-menu.cmd`
Expected: `False`

- [ ] **Step 2: Create the menu wrapper**

Create a CMD script that changes to `%~dp0`, loops on invalid menu input, maps the three choices to the approved PowerShell arguments, captures `%ERRORLEVEL%`, and pauses after exit.

- [ ] **Step 3: Verify content statically**

Run PowerShell assertions checking the target PowerShell filename, all three device/profile mappings, port 8765, and the pause behavior.
Expected: `CMD menu static verification passed.`

- [ ] **Step 4: Confirm existing project tests remain green**

Run: `.\venv\Scripts\python.exe -m pytest .\tests -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

Skip because the workspace is not a Git repository.
