import json
import copy
from pathlib import Path

USER_CONFIG_PATH = Path.home() / ".jarvis" / "user_config.json"

DEFAULT_CONFIG = {
    "username": "",
    "location": "",
    "preferences": {
        "temp_unit": "celsius",
        "language": "en",
        "wake_word_enabled": True,
        "camera_enabled": False,
        "tts_engine": "elevenlabs",
        "window_opacity": 0.92,
    },
    "first_run": True,
}


class LocalUser:
    """
    Single local user configuration stored at ~/.jarvis/user_config.json.
    Replaces the multi-user JWT auth system from the web version.
    """

    def __init__(self):
        self.config_path = USER_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return copy.deepcopy(DEFAULT_CONFIG)
        return copy.deepcopy(DEFAULT_CONFIG)

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=2)

    @property
    def is_first_run(self) -> bool:
        return self.data.get("first_run", True)

    @property
    def username(self) -> str:
        return self.data.get("username", "") or "User"

    @username.setter
    def username(self, value: str):
        self.data["username"] = value

    @property
    def location(self) -> str:
        return self.data.get("location", "")

    @location.setter
    def location(self, value: str):
        self.data["location"] = value

    @property
    def preferences(self) -> dict:
        return self.data.get("preferences", DEFAULT_CONFIG["preferences"])

    def get_preference(self, key: str, default=None):
        return self.preferences.get(key, default)

    def set_preference(self, key: str, value):
        if "preferences" not in self.data:
            self.data["preferences"] = copy.deepcopy(DEFAULT_CONFIG["preferences"])
        self.data["preferences"][key] = value

    def complete_first_run(self, username: str, location: str, temp_unit: str = "celsius"):
        """Called after the setup wizard completes."""
        self.data["username"] = username
        self.data["location"] = location
        self.data["preferences"]["temp_unit"] = temp_unit
        self.data["first_run"] = False
        self.save()


local_user = LocalUser()
