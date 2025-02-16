"""Select model from cache or parse model ID."""

import os

from app.utils.logger import logger


class ModelSelector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ModelSelector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.cache: dict[str, tuple[str, str]] = {}  # Initialize cache dictionary
        pass

    def _parse_model_id(self, model_id: str) -> tuple[str, str]:
        """Parse model ID update and return it."""
        logger.debug(f"Parsing model ID: {model_id}")

        # `model_id` pattern: <deepseek_alias>+<claude_alias>
        model_id = model_id.replace("-", "_")
        deepseek_part, claude_part = model_id.split("+")

        # Generate aliases
        deepseek_alias = f"MODEL_{deepseek_part.upper()}"
        claude_alias = f"MODEL_{claude_part.upper()}"

        logger.debug(f"DeepSeek alias: {deepseek_alias}")
        logger.debug(f"Claude alias: {claude_alias}")

        # Fetch from ENV or use defaults
        deepseek_name = os.getenv(deepseek_alias, deepseek_part)
        claude_name = os.getenv(claude_alias, claude_part)

        # Cache the result
        self.cache[model_id] = (deepseek_name, claude_name)

        return (deepseek_name, claude_name)

    def select_model(self, model_id) -> tuple[str, str]:
        """Select model from cache or parse model ID."""
        if model_id in self.cache:
            logger.info(f"Model '{model_id}' found in cache.")
            return self.cache[model_id]

        logger.info(f"Model '{model_id}' not found in cache.")
        model_pair = self._parse_model_id(model_id)
        logger.info(f"Model '{model_id}' parsed successfully.")
        return model_pair
