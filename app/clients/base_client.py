"""基础客户端类,定义通用接口"""
import os

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

import aiohttp
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

from app.config.models.model_config import BaseModelConfig
from app.utils.logger import logger


class BaseClient(ABC):
    """基础客户端类"""

    # 默认超时设置(秒)
    # total: 总超时时间
    # connect: 连接超时时间
    # sock_read: 读取超时时间
    # TODO: 默认时间的设置涉及到模型推理速度，需要根据实际情况进行调整
    DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=10, sock_read=500)

    def __init__(
        self,
        timeout: Optional[aiohttp.ClientTimeout] = None,
    ):
        self.timeout = timeout or self.DEFAULT_TIMEOUT

        # 从环境变量读取代理地址
        self.proxy_url = os.getenv("PROXY_URL", None)  # 如果未设置代理地址，默认为 None
        if self.proxy_url:
            logger.info("代理地址: %s", self.proxy_url)
        else:
            logger.info("未设置代理地址, 将不使用代理地址")

    async def _make_request(
        self,
        api_url: str,
        headers: dict,
        data: dict,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        use_proxy: bool = False,
    ) -> AsyncGenerator[bytes, None]:
        """发送请求并处理响应

        Args:
            api_url: API地址
            headers: 请求头
            data: 请求数据
            timeout: 当前请求的超时设置,None则使用实例默认值
            use_proxy: 是否使用代理

        Yields:
            bytes: 原始响应数据

        Raises:
            aiohttp.ClientError: 客户端错误
            ServerTimeoutError: 服务器超时
            Exception: 其他异常
        """
        request_timeout = timeout or self.timeout

        proxy_url = self.proxy_url if use_proxy else None

        if proxy_url: # 代理地址已配置, 且服务商需要使用代理
            logger.info("使用代理地址: %s", proxy_url)
        elif use_proxy: # 代理地址未配置, 且服务商需要使用代理
            logger.warning("服务商需要代理地址，请设置环境变量 PROXY_URL")

        try:
            # 使用 connector 参数来优化连接池
            connector = aiohttp.TCPConnector(limit=100, force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=data,
                    timeout=request_timeout,
                    proxy=proxy_url
                ) as response:
                    # 检查响应状态
                    if not response.ok:
                        error_text = await response.text()
                        error_msg = f"API 请求失败: 状态码 {response.status}, 错误信息: {error_text}"
                        logger.error(error_msg)
                        raise ClientError(error_msg)

                    # 流式读取响应内容
                    async for chunk in response.content.iter_any():
                        if chunk:  # 过滤空chunks
                            yield chunk

        except ServerTimeoutError as e:
            error_msg = f"请求超时: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        except ClientError as e:
            error_msg = f"客户端错误: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        except Exception as e:
            error_msg = f"请求处理异常: {str(e)}"
            logger.error(error_msg)
            raise

    @abstractmethod
    async def chat(
        self,
        base_model: BaseModelConfig,
        messages: list,
        model_arg,
        is_origin_reasoning: bool,
        stream: bool = True,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """对话，由子类实现

        Args:
            messages: 消息列表
            model_alias_name: 模型名称 (not model_id)
            model_arg: 模型参数
            is_origin_reasoning: 是否原始推理
            stream: 是否流式返回结果

        Yields:
            tuple[str, str]: (内容类型, 内容)
        """
        pass
