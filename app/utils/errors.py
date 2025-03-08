"""Error Classes"""

from abc import ABC


class DeepClaudeError(ABC, Exception):
    """Base class for all DeepClaude errors"""

    _header = "Error: "

    def __init__(self, reason: str):
        self.reason_msg = reason
        self.message = self._header + reason

    def __str__(self):
        return self.message


class ConfigError(DeepClaudeError):
    """Configuration error"""

    _header = "Configuration Error: "

class ConfigLoadError(ConfigError):
    """Error occurred while loading configuration"""

    _header = "Configuration Load Error: "

class ConfigSaveError(ConfigError):
    """Error occurred while saving configuration"""

    _header = "Configuration Save Error: "
