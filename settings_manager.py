"""
Settings management for RIAS.
Handles persistence of user preferences like theme selection.
"""

import json
import os
import logging
from typing import Any, Dict, Optional
from constants import (
    SETTINGS_FILE,
    DATA_DIR,
    DEFAULT_THEME,
    THEMES,
)


class SettingsManager:
    """Manages application settings persistence and retrieval."""

    def __init__(self) -> None:
        """Initialize the settings manager and ensure data directory exists."""
        os.makedirs(DATA_DIR, exist_ok=True)
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from file, or initialize with defaults if file doesn't exist."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    self._settings = json.load(f)
                logging.info("Settings loaded from file")
            else:
                self._settings = self._get_default_settings()
                self.save()
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            self._settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings dictionary."""
        return {
            "theme": DEFAULT_THEME,
        }

    def save(self) -> bool:
        """
        Save current settings to file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._settings, f, indent=2)
            logging.info("Settings saved to file")
            return True
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key.
            default: Default value if key not found.

        Returns:
            Setting value or default.
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value and persist to disk.

        Args:
            key: Setting key.
            value: Setting value.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self._settings[key] = value
            return self.save()
        except Exception as e:
            logging.error(f"Failed to set setting {key}: {e}")
            return False

    def get_theme(self) -> str:
        """
        Get the current theme name.

        Returns:
            Theme name, or default if not set.
        """
        theme = self.get("theme", DEFAULT_THEME)
        if theme not in THEMES:
            theme = DEFAULT_THEME
            self.set("theme", theme)
        return theme

    def set_theme(self, theme_name: str) -> bool:
        """
        Set the theme and persist to disk.

        Args:
            theme_name: Name of the theme.

        Returns:
            True if valid theme and successfully saved, False otherwise.
        """
        if theme_name not in THEMES:
            logging.warning(f"Invalid theme: {theme_name}")
            return False
        return self.set("theme", theme_name)

    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to defaults.

        Returns:
            True if successful, False otherwise.
        """
        self._settings = self._get_default_settings()
        return self.save()
