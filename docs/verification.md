# Verification Guide

Run these checks from the repository root unless a command says otherwise.

## Repository

```powershell
git status -sb --untracked-files=all
git remote -v
git rev-parse HEAD
git rev-parse origin/master
```

## Tooling

```powershell
pio --version
python --version
```

Note: this Windows environment currently prints a Python `RequestsDependencyWarning` when PlatformIO starts. Builds still complete successfully.

## Firmware Builds

```powershell
pio run -d projects\weather-station
pio run -d projects\smart-home
pio run -d projects\voice-control
pio run -d projects\gesture-control
pio run -d projects\ai-camera
pio run -d projects\ir-blaster
pio run -d projects\rf-gateway
```

For the Puzhong-specific weather station firmware:

```powershell
Set-Location projects\weather-station
pio run -c platformio_puzhong.ini
Set-Location ..\..
```

## Simulator Syntax Checks

```powershell
python -m py_compile simulator\esp32_demo.py projects\weather-station\simulator\weather_station.py projects\weather-station\simulator\weather_station_puzhong.py projects\smart-home\simulator\smart_home_demo.py projects\voice-control\simulator\voice_demo.py projects\gesture-control\simulator\gesture_demo.py projects\ai-camera\simulator\camera_demo.py projects\ir-blaster\simulator\ir_demo.py projects\rf-gateway\simulator\rf_demo.py
```

## Manual Simulator Run

The unified simulator opens a Tkinter UI and serves the documented local API:

```powershell
python simulator\esp32_demo.py
```

Expected API base: `http://localhost:8080`.

## Unified Simulator API Smoke Test

This starts the same HTTP handler used by the Tkinter app, checks representative endpoints, and shuts the server down:

```powershell
@'
import importlib.util
import json
import threading
import time
from urllib.request import urlopen

path = r"D:\projects\hardware\esp32-ai-projects\simulator\esp32_demo.py"
spec = importlib.util.spec_from_file_location("esp32_demo", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
threading.Thread(target=module.start_http_server, args=(8080,), daemon=True).start()
time.sleep(0.8)

def get_json(path):
    with urlopen(f"http://127.0.0.1:8080{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))

home_before = get_json("/home/state")
toggle = get_json("/home/toggle?id=0")
home_after = get_json("/home/state")
result = {
    "weather": get_json("/weather"),
    "home_toggle_ok": toggle["ok"],
    "home_relay0_before": home_before["relays"][0],
    "home_relay0_after": home_after["relays"][0],
    "voice": get_json("/voice/state"),
    "gesture": get_json("/gesture/state"),
    "ir": get_json("/ir/ac"),
    "rf": get_json("/rf/devices"),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
module._http_server.shutdown()
'@ | python -
```

## Final Diff Checks

```powershell
git diff --check
git diff --stat
git status -sb --untracked-files=all
```
