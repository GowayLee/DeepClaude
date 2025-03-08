"""IO Handlers for Config File"""

import json
import tempfile
import os
from typing import Optional, Dict, TypeVar, Generic
from pathlib import Path

from app.utils.errors import ConfigLoadError, ConfigSaveError
from app.utils.logger import LOGGER

from .models.system_config import SystemConfig
from .models.model_config import ModelConfig

T = TypeVar("T")


class CacheManager(Generic[T]):
    """集中缓存管理类"""

    def __init__(self):
        self._cache: Dict[Path, tuple[T, float]] = {}

    def get(self, config_path: Path) -> Optional[tuple[T, float]]:
        """获取缓存项"""
        if config_path in self._cache:
            cached_config, last_modified = self._cache[config_path]
            if last_modified == config_path.stat().st_mtime:
                return cached_config
        return None

    def set(self, config_path: Path, config: T) -> None:
        """设置缓存项"""
        self._cache[config_path] = (config, config_path.stat().st_mtime)

    def clear(self, config_path: Path) -> None:
        """清除指定缓存项"""
        if config_path in self._cache:
            del self._cache[config_path]

    def clear_all(self) -> None:
        """清除所有缓存"""
        self._cache.clear()


# 初始化缓存管理器
system_config_cache = CacheManager[SystemConfig]()
model_config_cache = CacheManager[ModelConfig]()


def load_system_config(config_path: Path) -> Optional[SystemConfig]:
    """
    加载系统配置

    Args:
        config_path: 配置文件路径

    Returns:
        SystemConfig对象, 如果文件不存在或格式错误则返回None

    Raises:
        ConfigLoadError: 当配置文件加载或验证失败时抛出
    """
    try:
        if not config_path.exists():
            LOGGER.warning(f"System config file not found: {config_path}")
            return None

        # 检查缓存是否存在且未过期
        cached_config = system_config_cache.get(config_path)
        if cached_config is not None:
            return cached_config

        # 从文件加载并更新缓存
        with open(config_path, "r", encoding="utf-8") as f:
            system_data = json.load(f)

        # 验证配置数据
        config = SystemConfig(**system_data)
        system_config_cache.set(config_path, config)
        return config

    except json.JSONDecodeError as e:
        LOGGER.error(f"Invalid JSON format in system config: {str(e)}")
        raise ConfigLoadError(f"Invalid JSON format in system config: {str(e)}")
    except Exception as e:
        LOGGER.error(f"Failed to load system config: {str(e)}")
        raise ConfigLoadError(f"Failed to load system config: {str(e)}")


def save_system_config(config: SystemConfig, config_path: Path) -> bool:
    """
    保存系统配置

    Args:
        config: 系统配置对象
        config_path: 配置文件路径

    Returns:
        是否保存成功

    Raises:
        ConfigSaveError: 当配置文件保存失败时抛出
    """
    try:
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用临时文件确保原子性写入
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=config_path.parent
        ) as tf:
            json_data = config.dict()
            json.dump(json_data, tf, ensure_ascii=False, indent=4)
            temp_path = tf.name

        # 重命名临时文件替换原配置文件
        os.replace(temp_path, config_path)

        # 清除缓存
        system_config_cache.clear(config_path)

        LOGGER.info(f"System config saved successfully to {config_path}")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to save system config: {str(e)}")
        raise ConfigSaveError(f"Failed to save system config: {str(e)}")


def load_model_config(config_path: Path) -> Optional[ModelConfig]:
    """
    加载模型配置

    Args:
        config_path: 配置文件路径

    Returns:
        ModelConfig对象, 如果文件不存在或格式错误则返回None

    Raises:
        ConfigLoadError: 当配置文件加载或验证失败时抛出
    """
    try:
        if not config_path.exists():
            LOGGER.warning(f"Model config file not found: {config_path}")
            return None

        # 检查缓存是否存在且未过期
        cached_config = model_config_cache.get(config_path)
        if cached_config is not None:
            return cached_config

        # 从文件加载并更新缓存
        with open(config_path, "r", encoding="utf-8") as f:
            model_data = json.load(f)

        # 验证配置数据
        config = ModelConfig(**model_data)
        model_config_cache.set(config_path, config)
        return config

    except json.JSONDecodeError as e:
        LOGGER.error(f"Invalid JSON format in model config: {str(e)}")
        raise ConfigLoadError(f"Invalid JSON format in model config: {str(e)}")
    except Exception as e:
        LOGGER.error(f"Failed to load model config: {str(e)}")
        raise ConfigLoadError(f"Failed to load model config: {str(e)}")


def save_model_config(config: ModelConfig, config_path: Path) -> bool:
    """
    保存配置

    Args:
        config: 模型配置对象
        config_path: 配置文件路径

    Returns:
        是否保存成功

    Raises:
        ConfigSaveError: 当配置文件保存失败时抛出
    """
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用临时文件确保原子性写入
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=config_path.parent
        ) as tf:
            json_data = config.model_dump()
            json.dump(json_data, tf, ensure_ascii=False, indent=4)
            temp_path = tf.name

        os.replace(temp_path, config_path)

        # 清除缓存
        model_config_cache.clear(config_path)

        LOGGER.info(f"Model config saved successfully to {config_path}")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to save model config: {str(e)}")
        raise ConfigSaveError(f"Failed to save model config: {str(e)}")
