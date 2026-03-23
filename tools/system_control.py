import subprocess
import psutil
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration

PROTECTED_PROCESSES = {
    "systemd", "init", "kernel", "kthreadd", "Xorg", "Xwayland",
    "gnome-shell", "gdm", "sddm", "lightdm", "pulseaudio", "pipewire",
    "NetworkManager", "dbus-daemon",
}


def open_application(name: str) -> Dict[str, Any]:
    """Launch an application by name."""
    app_map = {
        "terminal": "gnome-terminal",
        "file manager": "nautilus",
        "files": "nautilus",
        "browser": "xdg-open http://",
        "firefox": "firefox",
        "chrome": "google-chrome",
        "chromium": "chromium-browser",
        "calculator": "gnome-calculator",
        "text editor": "gedit",
        "settings": "gnome-control-center",
        "system monitor": "gnome-system-monitor",
    }

    cmd = app_map.get(name.lower(), name.lower())

    try:
        subprocess.Popen(
            cmd.split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"status": "success", "message": f"Opened {name}"}
    except FileNotFoundError:
        try:
            subprocess.Popen(
                ["xdg-open", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return {"status": "success", "message": f"Opened {name} via xdg-open"}
        except Exception as e:
            return {"status": "error", "message": f"Could not open {name}: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to open {name}: {e}"}


def close_application(name: str) -> Dict[str, Any]:
    """Close a user-space application by name. Refuses to kill system processes."""
    name_lower = name.lower()
    killed = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info["name"].lower()
            if name_lower in pname and pname not in PROTECTED_PROCESSES:
                proc.terminate()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return {"status": "success", "message": f"Closed: {', '.join(set(killed))}"}
    return {"status": "not_found", "message": f"No running application matching '{name}' found"}


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
