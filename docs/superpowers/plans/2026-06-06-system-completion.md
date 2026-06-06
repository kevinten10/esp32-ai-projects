# ESP32 AI Projects System Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `D:\projects\hardware\esp32-ai-projects` buildable, demonstrable, documented, and maintainable against the current GitHub repository state.

**Architecture:** Preserve the existing layout: independent PlatformIO projects under `projects/`, reusable C++ components under `components/`, Python standard-library simulators, and Markdown docs. Prefer small compatibility fixes and verification documentation over broad rewrites.

**Tech Stack:** PlatformIO Core 6.1.19, Arduino ESP32 framework, C++ firmware, Python 3 simulators, Git/GitHub.

---

## Task 1: Repository and Tooling Baseline

**Files:**
- Read: `README.md`
- Read: `PROJECT_STRUCTURE.md`
- Read: `GEMINI.md`
- Read: `projects/*/platformio.ini`

- [x] Confirm local branch and remote with `git status -sb` and `git remote -v`.
- [x] Confirm local `HEAD` matches `origin/master` before work started.
- [x] Confirm GitHub repository `kevinten10/esp32-ai-projects` is public, default branch `master`, with no open issues or PRs at inspection time.
- [x] Confirm PlatformIO starts with `pio --version`.

## Task 2: Firmware Build Matrix

**Files:**
- Modify: `projects/weather-station/platformio.ini`
- Modify: `projects/weather-station/platformio_puzhong.ini`
- Modify: `projects/ir-blaster/src/main.cpp`
- Modify: `projects/ai-camera/src/main.cpp`
- Modify: `projects/smart-home/src/main.cpp`
- Modify: `projects/rf-gateway/src/main.cpp`

- [x] Fix weather-station so default and Puzhong entry points are not linked together.
- [x] Verify `pio run -d projects/weather-station`.
- [x] Verify `pio run -c platformio_puzhong.ini` from `projects/weather-station`.
- [x] Verify `pio run -d projects/smart-home`.
- [x] Verify `pio run -d projects/voice-control`.
- [x] Verify `pio run -d projects/gesture-control`.
- [x] Verify `pio run -d projects/ai-camera`.
- [x] Verify `pio run -d projects/ir-blaster`.
- [x] Verify `pio run -d projects/rf-gateway`.

## Task 3: Simulator Verification

**Files:**
- Modify: `projects/ai-camera/simulator/camera_demo.py`
- Modify: `projects/ir-blaster/simulator/ir_demo.py`
- Modify: `simulator/esp32_demo.py`
- Read: `simulator/README.md`

- [x] Fix Python `global` declaration errors in affected simulators.
- [x] Verify all simulator Python files with `python -m py_compile`.
- [x] Verify the unified simulator HTTP API handler by starting `start_http_server(8080)` in a background thread and querying representative endpoints.
- [ ] Optionally launch the full Tkinter UI manually when an interactive desktop run is desired.

## Task 4: Documentation Alignment

**Files:**
- Modify: `PROJECT_STRUCTURE.md`
- Create: `docs/verification.md`

- [ ] Update `PROJECT_STRUCTURE.md` to list all current projects: `ai-camera`, `gesture-control`, `ir-blaster`, `rf-gateway`, `smart-home`, `voice-control`, `weather-station`.
- [ ] Add `docs/verification.md` with the exact commands used for Git, firmware, Puzhong firmware, and simulator checks.

## Task 5: Final Hygiene

**Files:**
- Review all modified files.

- [ ] Run `git diff --check`.
- [ ] Run `git status -sb --untracked-files=all`.
- [ ] Summarize completed work, verified commands, warnings, and remaining optional manual hardware/UI checks.
