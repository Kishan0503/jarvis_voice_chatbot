import subprocess
import shutil
import psutil
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration

PROTECTED_PROCESSES = {
    "systemd", "init", "kernel", "kthreadd", "Xorg", "Xwayland",
    "gnome-shell", "gdm", "sddm", "lightdm", "pulseaudio", "pipewire",
    "NetworkManager", "dbus-daemon",
}

# Maps display name → ordered list of commands to try when launching.
# The first command that exists on PATH wins.
_LAUNCH_MAP: Dict[str, list] = {
    "terminal":           ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"],
    "file manager":       ["nautilus", "thunar", "dolphin"],
    "files":              ["nautilus", "thunar", "dolphin"],
    "browser":            ["xdg-open https://google.com"],
    "firefox":            ["firefox"],
    "chrome":             ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"],
    "google chrome":      ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"],
    "chromium":           ["chromium-browser", "chromium"],
    "calculator":         ["gnome-calculator", "kcalc", "mate-calc"],
    "text editor":        ["gedit", "gnome-text-editor", "kate", "mousepad"],
    "settings":           ["gnome-control-center", "unity-control-center"],
    "system monitor":     ["gnome-system-monitor", "ksysguard"],
    "teams":              ["teams", "teams-for-linux", "teams-for-linux-nativefier"],
    "microsoft teams":    ["teams", "teams-for-linux", "teams-for-linux-nativefier"],
    "notes":              ["gnome-notes", "bijiben", "gnote"],
    "gnome notes":        ["gnome-notes", "bijiben"],
    "vs code":            ["code", "code-oss", "codium"],
    "vscode":             ["code", "code-oss", "codium"],
    "code":               ["code", "code-oss", "codium"],
    "spotify":            ["spotify"],
    "slack":              ["slack"],
    "discord":            ["discord"],
    "telegram":           ["telegram-desktop", "telegram"],
    "vlc":                ["vlc"],
    "gimp":               ["gimp"],
    "libreoffice":        ["libreoffice"],
    "thunderbird":        ["thunderbird"],
    "zoom":               ["zoom"],
    "postman":            ["postman"],
}

# Maps display name → list of process names to search when terminating.
# Handles cases like "Google Chrome" → process name is just "chrome".
_PROCESS_MAP: Dict[str, list] = {
    "chrome":             ["chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
    "google chrome":      ["chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
    "chromium":           ["chromium", "chromium-browser", "chrome"],
    "firefox":            ["firefox", "firefox-bin"],
    "teams":              ["teams", "teams-for-linux"],
    "microsoft teams":    ["teams", "teams-for-linux"],
    "notes":              ["gnome-notes", "bijiben", "gnote"],
    "terminal":           ["gnome-terminal", "gnome-terminal-server", "xterm", "konsole"],
    "files":              ["nautilus"],
    "file manager":       ["nautilus", "thunar", "dolphin"],
    "calculator":         ["gnome-calculator", "kcalc"],
    "settings":           ["gnome-control-center"],
    "system monitor":     ["gnome-system-monitor", "ksysguard"],
    "vs code":            ["code", "code-oss", "codium"],
    "vscode":             ["code", "code-oss", "codium"],
    "spotify":            ["spotify"],
    "slack":              ["slack"],
    "discord":            ["discord"],
    "telegram":           ["telegram-desktop", "telegram"],
    "vlc":                ["vlc"],
    "zoom":               ["zoom"],
}


def _try_launch(commands: list, display_name: str) -> Dict[str, Any]:
    """
    Try each command in order. Launch the first one found on PATH.
    Returns success/error dict.
    """
    for cmd_str in commands:
        parts = cmd_str.split()
        executable = parts[0]
        if shutil.which(executable):
            try:
                subprocess.Popen(
                    parts,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return {"status": "success", "message": f"Opened {display_name}"}
            except Exception as e:
                continue  # try next command
    return {
        "status": "error",
        "message": (
            f"Could not find '{display_name}' on this system. "
            "It may not be installed."
        ),
    }


def open_application(name: str) -> Dict[str, Any]:
    """Launch an application by name."""
    key = name.lower().strip()
    commands = _LAUNCH_MAP.get(key)

    if commands:
        return _try_launch(commands, name)

    # Unknown app — try the name directly, then xdg-open as last resort
    if shutil.which(key):
        try:
            subprocess.Popen(
                [key],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return {"status": "success", "message": f"Opened {name}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open {name}: {e}"}

    # xdg-open as absolute last resort (handles URLs, file associations)
    try:
        subprocess.Popen(
            ["xdg-open", key],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"status": "success", "message": f"Attempted to open {name} via system handler"}
    except Exception:
        return {
            "status": "error",
            "message": f"'{name}' does not appear to be installed on this system.",
        }


def close_application(name: str) -> Dict[str, Any]:
    """Close a user-space application by name. Refuses to kill system processes."""
    key = name.lower().strip()

    # Build the set of process names to search for
    target_names: set[str] = set()

    # Check known map first
    if key in _PROCESS_MAP:
        target_names.update(_PROCESS_MAP[key])
    else:
        # Fall back: use the raw name and each word of it (handles "Google Chrome" → "chrome")
        target_names.add(key)
        target_names.update(w for w in key.split() if len(w) > 2)

    killed = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info["name"].lower()
            # Match if the process name equals or contains any of our targets
            if any(t in pname or pname in t for t in target_names):
                if pname not in {p.lower() for p in PROTECTED_PROCESSES}:
                    proc.terminate()
                    killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return {"status": "success", "message": f"Closed: {', '.join(set(killed))}"}
    return {
        "status": "not_found",
        "message": f"'{name}' does not appear to be running.",
    }


def list_running_apps() -> Dict[str, Any]:
    """List user-visible running applications."""
    apps = set()
    for proc in psutil.process_iter(["pid", "name", "username"]):
        try:
            if proc.info["username"] and proc.info["name"] not in PROTECTED_PROCESSES:
                apps.add(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_apps = sorted(apps)[:30]
    return {"status": "success", "apps": sorted_apps, "count": len(sorted_apps)}


def get_system_info() -> Dict[str, Any]:
    """Get CPU, RAM, disk, and battery status."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    info = {
        "cpu_percent": cpu,
        "ram_total_gb": round(mem.total / (1024 ** 3), 1),
        "ram_used_gb": round(mem.used / (1024 ** 3), 1),
        "ram_percent": mem.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_percent": disk.percent,
    }

    battery = psutil.sensors_battery()
    if battery:
        info["battery_percent"] = battery.percent
        info["battery_plugged"] = battery.power_plugged

    return {"status": "success", **info}


def set_system_volume(level: int) -> Dict[str, Any]:
    """Set system audio volume (0-100) using amixer."""
    level = max(0, min(100, level))
    try:
        subprocess.run(
            ["amixer", "set", "Master", f"{level}%"],
            capture_output=True, timeout=5,
        )
        return {"status": "success", "message": f"Volume set to {level}%"}
    except Exception as e:
        return {"status": "error", "message": f"Could not set volume: {e}"}


def lock_screen() -> Dict[str, Any]:
    """Lock the desktop session."""
    try:
        subprocess.Popen(["loginctl", "lock-session"], start_new_session=True)
        return {"status": "success", "message": "Screen locked"}
    except Exception as e:
        return {"status": "error", "message": f"Could not lock screen: {e}"}


system_tool_declarations = [
    FunctionDeclaration(
        name="open_application",
        description="Open/launch an application by name (e.g., 'firefox', 'terminal', 'vs code')",
        parameters={"type": "object", "properties": {
            "name": {"type": "string", "description": "Application name to open"}
        }, "required": ["name"]},
    ),
    FunctionDeclaration(
        name="close_application",
        description="Close/terminate a running application by name",
        parameters={"type": "object", "properties": {
            "name": {"type": "string", "description": "Application name to close"}
        }, "required": ["name"]},
    ),
    FunctionDeclaration(
        name="list_running_apps",
        description="List all currently running user applications",
        parameters={"type": "object", "properties": {}},
    ),
    FunctionDeclaration(
        name="get_system_info",
        description="Get system information: CPU usage, RAM, disk space, battery",
        parameters={"type": "object", "properties": {}},
    ),
    FunctionDeclaration(
        name="set_system_volume",
        description="Set the system audio volume to a specific level (0-100)",
        parameters={"type": "object", "properties": {
            "level": {"type": "integer", "description": "Volume level from 0 to 100"}
        }, "required": ["level"]},
    ),
    FunctionDeclaration(
        name="lock_screen",
        description="Lock the desktop screen",
        parameters={"type": "object", "properties": {}},
    ),
]

tool_functions = {
    "open_application": open_application,
    "close_application": close_application,
    "list_running_apps": list_running_apps,
    "get_system_info": get_system_info,
    "set_system_volume": set_system_volume,
    "lock_screen": lock_screen,
}
