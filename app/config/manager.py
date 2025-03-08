"""Config Manager Module"""

import threading
from pathlib import Path
from app.utils.errors import ConfigLoadError, ConfigSaveError
from app.utils.logger import LOGGER

from .io import (
    load_model_config,
    load_system_config,
    save_model_config,
    save_system_config,
)
from .models.system_config import SystemConfig
from .models.model_config import ModelConfig, Provider, ProviderType


SYSTEM_CONFIG_PATH = "./config/system.json"
MODEL_CONFIG_PATH = "./config/models.json"


class ConfigManager:
    """Global Config Manager"""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        """initialize the ConfigManager"""
        self._system_config: SystemConfig = None
        self._model_config: ModelConfig = None
        self._load_configs()

    @classmethod
    def initialize(cls) -> None:
        """singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ConfigManager()

    @classmethod
    def instance(cls) -> "ConfigManager":
        """get singleton instance"""
        if cls._instance is None:
            cls.initialize()
        return cls._instance

    def _load_configs(self):
        """Load config files with enhanced error handling and fallback mechanism"""

        LOGGER.info("Loading configuration files...")

        try:
            # Load model config with retry and fallback
            self._model_config = self._load_config_with_fallback(
                Path(MODEL_CONFIG_PATH),
                load_model_config,
                "Model",
                "Failed to load model config"
            )

            # Load system config with retry and fallback
            self._system_config = self._load_config_with_fallback(
                Path(SYSTEM_CONFIG_PATH),
                load_system_config,
                "System",
                "Failed to load system config",
                self._create_default_system_config
            )

            LOGGER.info("Configuration files loaded successfully")

        except ConfigLoadError as e:
            LOGGER.critical(f"Critical configuration loading error: {str(e)}")
            raise
        except Exception as e:
            LOGGER.critical(f"Unexpected error loading configurations: {str(e)}")
            raise ConfigLoadError(f"Unexpected error: {str(e)}")

    def _load_config_with_fallback(self, config_path: Path, loader, config_type: str, 
                                 error_message: str, fallback_creator=None):
        """Helper method to load config with retry and fallback mechanism"""
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                config = loader(config_path)
                if config is not None:
                    return config
                
                # If config is None and we have a fallback creator
                if fallback_creator is not None:
                    LOGGER.warning(f"{config_type} config not found, creating default...")
                    return fallback_creator(config_path)
                
                raise ConfigLoadError(f"{config_type} config not found at {config_path}")

            except ConfigLoadError as e:
                last_exception = e
                LOGGER.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    LOGGER.info(f"Retrying {config_type} config loading...")
                continue
            except Exception as e:
                last_exception = e
                LOGGER.error(f"Unexpected error loading {config_type} config: {str(e)}")
                break

        if last_exception:
            LOGGER.error(f"{error_message}: {str(last_exception)}")
            raise ConfigLoadError(f"{error_message}: {str(last_exception)}")

    def _create_default_system_config(self, config_path: Path) -> SystemConfig:
        """Create default system configuration"""
        try:
            default_config = SystemConfig(
                api_key="<your_api_key>",
                allow_origins=["*"],
                log_level="INFO",
                proxy={"proxy_open": False, "proxy_address": "127.0.0.1:7890"},
            )

            if not save_system_config(default_config, config_path):
                raise ConfigSaveError(
                    f"Failed to save default system config to {config_path}"
                )

            LOGGER.info("Default system configuration created successfully")
            return default_config

        except Exception as e:
            LOGGER.critical(f"Failed to create default system config: {str(e)}")
            raise ConfigLoadError(f"Failed to create default system config: {str(e)}")

    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        with self._lock:
            return self._system_config

    def get_model_config(self) -> ModelConfig:
        """获取模型配置"""
        with self._lock:
            return self._model_config

    def get_provider_config(self, provider_name: str) -> Provider:
        """获取指定provider配置"""
        with self._lock:
            return self._model_config.get_provider(provider_name)

    def get_model_info(
        self, model_name: str
    ) -> tuple[str, str, str, ProviderType, bool]:
        """获取指定模型信息"""
        with self._lock:
            return self._model_config.get_model_request_info(model_name)

    def update_system_config(self, config: SystemConfig) -> bool:
        """更新系统配置"""
        with self._lock:
            try:
                LOGGER.info("Updating system configuration...")
                self._system_config = config
                if not save_system_config(config, Path(SYSTEM_CONFIG_PATH)):
                    raise ConfigSaveError(
                        f"Failed to save system config to {SYSTEM_CONFIG_PATH}"
                    )
                LOGGER.info("System configuration updated successfully")
                return True
            except Exception as e:
                LOGGER.error(f"Failed to update system configuration: {str(e)}")
                raise

    def update_model_config(self, config: ModelConfig) -> bool:
        """更新模型配置"""
        with self._lock:
            try:
                LOGGER.info("Updating model configuration...")
                self._model_config = config
                if not save_model_config(config, Path(MODEL_CONFIG_PATH)):
                    raise ConfigSaveError(
                        f"Failed to save model config to {MODEL_CONFIG_PATH}"
                    )
                LOGGER.info("Model configuration updated successfully")
                return True
            except Exception as e:
                LOGGER.error(f"Failed to update model configuration: {str(e)}")
                raise
