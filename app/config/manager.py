import json
import threading
from typing import Dict, Optional, List, Any
from pathlib import Path

from .io import load_model_config, load_shown_model_config
from .models.system_config import SystemConfig
from .models.model_config import ModelConfig


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        """initialize the ConfigManager"""
        self.system: SystemConfig = None
        self.models: Dict[str, ModelConfig] = {}
        self.config_file_path = Path("config.json")
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

    def _load_system_config(self) -> None:
        """加载系统配置"""
        self.system = load_system_config(self.config_file_path)
        if self.system is None:
            # 创建默认系统配置
            self.system = SystemConfig(
                cors_origins=["*"],
                api_keys=["sk-default-key"],
                host="0.0.0.0",
                port=8000,
                proxy=None,
                debug=True,
            )
            save_system_config(self.system, self.config_file_path)

    def _load_model_config(self) -> None:
        """加载模型配置"""
        models_dir = Path("models_config")
        self.models = load_model_config(models_dir)

    def save_model_config(self, model_config: ModelConfig) -> bool:
        """保存模型配置"""
        models_dir = Path("models_config")
        result = save_model_config(model_config, models_dir)
        if result:
            self.models[model_config.id] = model_config
        return result
