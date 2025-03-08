"""Logger Module"""

import sys

import logging
import colorlog


class Logger:
    """Logger Class"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # 显式初始化_logger
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_logger"):
            self._logger = None

    @property
    def logger(self) -> logging.Logger:
        """获取logger实例, Lazy Loading"""
        if not hasattr(self, "_logger") or self._logger is None:
            self._logger = self.setup_logger()
        return self._logger

    def setup_logger(self, name: str = "DeepClaude") -> logging.Logger:
        """
        配置并返回一个logger实例。

        Args:
            name (str, optional): logger的名称. Defaults to "DeepClaude".

        Returns:
            logging.Logger: 配置好的logger实例
        """
        logger_instance = colorlog.getLogger(name)

        if logger_instance.handlers:
            return logger_instance

        # 设置日志级别
        logger_instance.setLevel(logging.DEBUG)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # 设置彩色日志格式
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )

        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)

        return logger_instance

    def set_level(self, level: int):
        """
        动态设置日志级别。

        Args:
            level (int): 日志级别，例如 logging.DEBUG, logging.INFO 等。
        """
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)


LOGGER = Logger().logger
