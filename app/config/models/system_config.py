"""System Configuration Classes"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, model_validator, ValidationError

from app.utils.logger import logger


class LogLevel(str, Enum):
    """Enum for Log Level"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Proxy(BaseModel):
    """Proxy Configuration Model"""

    proxy_open: bool = Field(default=False, description="Whether to enable proxy")
    proxy_address: str = Field(
        default="127.0.0.1:7890", description="Proxy address in format host:port"
    )

    @model_validator(mode="after")
    def validate_proxy(self) -> "Proxy":
        """Validate proxy configuration"""
        if self.proxy_open:
            if not self.proxy_address:
                raise ValidationError("Proxy address is required when proxy is enabled")

            proxy_address = self.__dict__.get("proxy_address", "")
            # 验证代理地址格式
            parts = proxy_address.split(":")
            if len(parts) != 2:
                raise ValidationError("Proxy address must be in the format 'host:port'")

            _, port = parts
            if not port.isdigit():
                raise ValidationError("Proxy port must be a numeric value")

            port_num = int(port)
            if 0 > port_num or port_num > 65535:
                raise ValidationError("Proxy port must be between 1 and 65535")

        return self


class SystemConfig(BaseModel):
    """System Configuration Model"""

    api_key: str = Field(..., description="API key for authentication")
    allow_origins: List[str] = Field(
        default=["*"], description="Allowed origins for CORS"
    )
    log_level: LogLevel = Field(default=LogLevel.DEBUG, description="Logging level")
    proxy: Proxy = Field(default_factory=Proxy, description="Proxy configuration")

    @model_validator(mode="after")
    def validate_system(self) -> "SystemConfig":
        """Validate system configuration"""
        if not self.api_key:
            raise ValidationError("API key cannot be empty")

        # 记录日志级别
        logger.info("System configured with log level: %s", self.log_level)

        return self
