"""Model Configuration Classes"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator, ValidationError

from app.utils.logger import logger


class ProviderType(str, Enum):
    """Enum for Provider Type"""

    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OPENAI_COMPATIBLE = "openai-compatible"


class Provider(BaseModel):
    """Provider Configuration"""

    model_config = ConfigDict(
        str_min_length=1,  # 确保字符串字段至少有一个字符
        str_strip_whitespace=True,  # 去除字符串字段的空白字符
    )

    name: str = Field(..., description="Provider name")
    type: ProviderType = Field(..., description="Provider type")
    base_url: str = Field(..., description="Base URL for API requests")
    api_key: str = Field(..., description="API key for authentication")
    use_proxy: bool = Field(default=False, description="Whether to use proxy")

    @model_validator(mode="after")
    def _validate_base_url(self) -> "Provider":
        """Validate base URL starts with http or https"""
        base_url = self.__dict__.get("base_url", "")
        if not base_url.startswith(("http://", "https://")):
            logger.warning(
                "Base URL '%s' does not start with http or https", self.base_url
            )
        return self


class BasicModel(BaseModel):
    """Base Model Configuration"""

    model_config = ConfigDict(
        str_min_length=1,
        str_strip_whitespace=True,
    )

    name: str = Field(..., description="Model name")
    model_id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name")
    context: int = Field(gt=0, description="Context window size")
    max_tokens: int = Field(gt=0, description="Maximum involved tokens")


class DeepModel(BaseModel):
    """Deep Model Configuration"""

    model_config = ConfigDict(
        str_min_length=1,
        str_strip_whitespace=True,
    )

    name: str = Field(..., description="Deep model name")
    reason_model: str = Field(..., description="Reasoning model name")
    answer_model: str = Field(..., description="Answering model name")
    is_origin_reasoning: bool = Field(
        default=True, description="Whether to use original reasoning"
    )


class ModelConfig(BaseModel):
    """Model Configuration"""

    model_config = ConfigDict(
        str_min_length=1,
        str_strip_whitespace=True,
    )

    providers: List[Provider] = Field(..., description="List of providers")
    base_models: List[BasicModel] = Field(..., description="List of base models")
    deep_models: List[DeepModel] = Field(..., description="List of deep models")
    _provider_map: Dict[str, Provider] = Field(default_factory=dict, exclude=True)
    _base_model_map: Dict[str, BasicModel] = Field(
        default_factory=dict, exclude=True
    )
    _deep_model_map: Dict[str, DeepModel] = Field(
        default_factory=dict, exclude=True
    )
    _context_map: Dict[str, int] = Field(default_factory=dict, exclude=True)

    @model_validator(mode="after")
    def _validate_unique_names(self) -> "ModelConfig":
        """Validate unique names for providers, base models, and deep models"""
        provider_names = [p.name for p in self.providers]
        if len(provider_names) != len(set(provider_names)):
            raise ValidationError("Provider names must be unique")

        base_model_names = [m.name for m in self.base_models]
        if len(base_model_names) != len(set(base_model_names)):
            raise ValidationError("Base model names must be unique")

        deep_model_names = [m.name for m in self.deep_models]
        if len(deep_model_names) != len(set(deep_model_names)):
            raise ValidationError("Deep model names must be unique")

        return self

    @model_validator(mode="after")
    def _validate_references(self) -> "ModelConfig":
        """Validate references between providers, base models, and deep models"""
        provider_names = {p.name for p in self.providers}
        base_model_names = {m.name for m in self.base_models}

        for model in self.base_models:
            if model.provider not in provider_names:
                raise ValidationError(f"Provider '{model.provider}' not found")

        for model in self.deep_models:
            if model.reason_model not in base_model_names:
                raise ValidationError(f"Reason model '{model.reason_model}' not found")
            if model.answer_model not in base_model_names:
                raise ValidationError(f"Answer model '{model.answer_model}' not found")

        return self

    @model_validator(mode="after")
    def _build_maps(self) -> "ModelConfig":
        """Build maps for quick lookup of providers, base models, and contexts"""
        self._provider_map = {p.name: p for p in self.providers}
        self._base_model_map = {m.name: m for m in self.base_models}
        self._deep_model_map = {m.name: m for m in self.deep_models}

        for model in self.deep_models:
            reason_context = self.get_base_model(model.reason_model).context
            answer_context = self.get_base_model(model.answer_model).context
            self._context_map[model.name] = max(reason_context, answer_context)

        return self

    def get_deep_model(self, name: str) -> DeepModel:
        """Get deep model config by name"""
        if model := self._deep_model_map.get(name):
            return model
        raise ValidationError(f"Deep model '{name}' not found")

    def get_provider(self, name: str) -> Provider:
        """Get provider config by name"""
        if provider := self._provider_map.get(name):
            return provider
        raise ValidationError(f"Provider '{name}' not found")

    def get_base_model(self, name: str) -> BasicModel:
        """Get base model config by name"""
        if model := self._base_model_map.get(name):
            return model
        raise ValidationError(f"Base model '{name}' not found")

    def get_model_request_info(
        self, model_name: str
    ) -> tuple[str, str, str, ProviderType, bool]:
        """Get request required information for a model"""
        base_model = self.get_base_model(model_name)
        provider = self.get_provider(base_model.provider)
        return (
            base_model.model_id,
            provider.base_url,
            provider.api_key,
            provider.type,
            provider.use_proxy,
        )
