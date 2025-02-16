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
        # change `-` to `_`
        origin_model_id = model_id
        model_id = model_id.replace("-", "_")
        # split the model_id into two parts and convert to uppercase
        # add prefix of MODEL_
        deepseek_alias: str = "MODEL_" + model_id.split("+")[0].upper()
        claude_alias: str = "MODEL_" + model_id.split("+")[1].upper()

        logger.debug(f"DeepSeek alias: {deepseek_alias}")
        logger.debug(f"Claude alias: {claude_alias}")

        # try to find alias in ENV
        deepseek_name: str | None = os.getenv(deepseek_alias)
        claude_name: str | None = os.getenv(claude_alias)

        # check availability of models
        if deepseek_name is None or claude_name is None:
            raise ValueError(f"Model '{model_id}' not found.")

        # check if model is already in cache
        if origin_model_id in self.cache:
            return self.cache[origin_model_id]

        # add model to cache
        self.cache[origin_model_id] = (deepseek_name, claude_name)

        return (deepseek_name, claude_name)

    def select_model(self, model_id) -> tuple[str, str]:
        """Select model from cache or parse model ID."""
        if model_id in self.cache:
            logger.info(f"Model '{model_id}' found in cache.")
            return self.cache[model_id]
        else:
            try:
                logger.info(f"Model '{model_id}' not found in cache.")
                model_pair = self._parse_model_id(model_id)
            except ValueError as e:
                raise ValueError(f"Model '{model_id}' not found.") from e

            logger.info(f"Model '{model_id}' parsed successfully.")
            return model_pair
