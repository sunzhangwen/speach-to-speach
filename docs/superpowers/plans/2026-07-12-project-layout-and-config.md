# Project Layout and Shared Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Relocate backend source under `backend/`, centralize local service defaults in `voice-config.json`, and provide root-level CMD launchers for backend and frontend.

**Architecture:** Root launchers load and validate one JSON configuration file while retaining command-line override support. Backend application code and tests move together under `backend/`; runtime assets remain root-relative.

**Tech Stack:** PowerShell, Windows CMD, Python, JSON

## Global Constraints

- Keep models, caches, virtual environment, frontend project, and launchers at the root.
- Explicit PowerShell arguments override JSON defaults.
- Verification must not load speech models or occupy service ports.

---

### Task 1: Relocate backend source

**Files:**
- Move: `run_s2s.py` to `backend/run_s2s.py`
- Move: `s2s_runtime/` to `backend/s2s_runtime/`
- Move: `tests/` to `backend/tests/`

- [ ] Move backend files while preserving package names.
- [ ] Update `run_s2s.py` to resolve the project root one directory above `backend`.
- [ ] Run relocated unit tests with `backend` as the working directory.

### Task 2: Add and consume shared configuration

**Files:**
- Create: `voice-config.json`
- Modify: `start-voice-backend.ps1`
- Modify: `start-voice-frontend.ps1`

- [ ] Add approved LM Studio and port defaults.
- [ ] Load and validate JSON in both launchers.
- [ ] Preserve explicit parameter overrides.
- [ ] Parse both PowerShell scripts without executing services.

### Task 3: Update CMD launchers

**Files:**
- Modify: `start-voice-backend-menu.cmd`
- Create: `start-voice-frontend.cmd`

- [ ] Remove hard-coded backend ports from the menu wrapper.
- [ ] Add the frontend wrapper with exit-code preservation and pause.
- [ ] Statically verify all CMD targets and mode mappings.

### Task 4: Final verification

- [ ] Validate JSON values and port ranges.
- [ ] Run every relocated backend unit test.
- [ ] Confirm old root backend paths no longer exist.
- [ ] Confirm the target directory structure matches the specification.
