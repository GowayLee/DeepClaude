"""IO Handlers for Config File"""

import json
import tempfile
import os
from typing import Dict, Optional, List, Any
from pathlib import Path

from .models.system_config import SystemConfig
from .models.model_config import ModelConfig


def load_system_config(config_path: Path) -> Optional[SystemConfig]:
    """
    加载系统配置

    Args:
        config_path: 配置文件路径

    Returns:
        SystemConfig对象, 如果文件不存在或格式错误则返回None
    """
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                system_data = json.load(f)
            return SystemConfig(**system_data)
        return None
    except Exception as e:
        print(f"加载系统配置失败: {str(e)}")
        return None


def save_system_config(config: SystemConfig, config_path: Path) -> bool:
    """
    保存系统配置

    Args:
        config: 系统配置对象
        config_path: 配置文件路径

    Returns:
        是否保存成功
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
        return True
    except Exception as e:
        print(f"保存系统配置失败: {str(e)}")
        return False


def load_model_config(models_dir: Path) -> Dict[str, ModelConfig]:
    """
    加载所有模型配置

    Args:
        models_dir: 模型配置目录

    Returns:
        模型ID到ModelConfig的映射字典
    """
    models = {}
    try:
        if not models_dir.exists():
            models_dir.mkdir(parents=True, exist_ok=True)
            return models

        for config_file in models_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    model_data = json.load(f)
                model_config = ModelConfig(**model_data)
                models[model_config.id] = model_config
            except Exception as e:
                print(f"加载模型配置 {config_file.name} 失败: {str(e)}")
                continue
        return models
    except Exception as e:
        print(f"加载模型配置目录失败: {str(e)}")
        return models


def load_shown_model_config(models: Dict[str, ModelConfig]) -> List[Dict[str, Any]]:
    """
    处理用于前端显示的模型配置

    Args:
        models: 模型配置字典

    Returns:
        适合前端显示的模型配置列表
    """
    shown_models = []
    for model_id, model_config in models.items():
        # 转换为前端友好的格式
        shown_model = model_config.dict(exclude={"api_key", "password"})
        shown_models.append(shown_model)
    return shown_models


def save_model_config(model_config: ModelConfig, models_dir: Path) -> bool:
    """
    保存单个模型配置

    Args:
        model_config: 模型配置对象
        models_dir: 模型配置目录

    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        models_dir.mkdir(parents=True, exist_ok=True)

        config_path = models_dir / f"{model_config.id}.json"

        # 使用临时文件确保原子性写入
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=models_dir
        ) as tf:
            json_data = model_config.dict()
            json.dump(json_data, tf, ensure_ascii=False, indent=4)
            temp_path = tf.name

        # 重命名临时文件替换原配置文件
        os.replace(temp_path, config_path)
        return True
    except Exception as e:
        print(f"保存模型配置失败: {str(e)}")
        return False


def delete_model_config(model_id: str, models_dir: Path) -> bool:
    """
    删除模型配置

    Args:
        model_id: 模型ID
        models_dir: 模型配置目录

    Returns:
        是否删除成功
    """
    try:
        config_path = models_dir / f"{model_id}.json"
        if config_path.exists():
            config_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"删除模型配置失败: {str(e)}")
        return False
