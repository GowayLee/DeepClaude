"""DeepSeek API 客户端"""

import json
from typing import AsyncGenerator

from typing_extensions import override

from app.config.models.model_config import BaseModelConfig
from app.utils.config.manager import ModelConfigManager
from app.utils.logger import logger

from .base_client import BaseClient


class DeepSeekClient(BaseClient):
    def __init__(self):
        super().__init__()
        self._model_config = ModelConfigManager.get_model_config()

    def _process_think_tag_content(self, content: str) -> tuple[bool, str]:
        """处理包含 think 标签的内容

        Args:
            content: 需要处理的内容字符串

        Returns:
            tuple[bool, str]:
                bool: 是否检测到完整的 think 标签对
                str: 处理后的内容
        """
        has_start = "<think>" in content
        has_end = "</think>" in content

        if has_start and has_end:
            return True, content
        elif has_start:
            return False, content
        elif not has_start and not has_end:
            return False, content
        else:
            return True, content

    @override
    async def chat(
        self,
        base_model: BaseModelConfig,
        messages: list,
        model_arg,
        is_origin_reasoning: bool,
        stream: bool = True,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话

        Args:
            messages: 消息列表
            model: 模型名称

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "reasoning" 或 "content"
                内容: 实际的文本内容
        """

        # Obtain relevant information from model_config
        model_id, base_url, api_key, provider_type, use_proxy = (
            self._model_config.get_model_request_info(base_model.name)
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        data = {
            "model": model_id,
            "messages": messages,
            "stream": True,
        }

        logger.debug("开始流式对话：%s", data)

        accumulated_content = ""
        is_collecting_think = False

        async for chunk in self._make_request(
            base_url, headers, data, use_proxy=use_proxy
        ):
            chunk_str = chunk.decode("utf-8")

            try:
                lines = chunk_str.splitlines()
                for line in lines:
                    if line.startswith("data: "):
                        json_str = line[len("data: ") :]
                        if json_str == "[DONE]":
                            return

                        data = json.loads(json_str)
                        if (
                            data
                            and data.get("choices")
                            and data["choices"][0].get("delta")
                        ):
                            delta = data["choices"][0]["delta"]

                            if is_origin_reasoning:
                                # 处理 reasoning_content
                                if delta.get("reasoning_content"):
                                    content = delta["reasoning_content"]
                                    logger.debug("提取推理内容：%s", content)
                                    yield "reasoning", content

                                if delta.get("reasoning_content") is None and delta.get(
                                    "content"
                                ):
                                    content = delta["content"]
                                    logger.info(
                                        "提取内容信息，推理阶段结束: %s", content
                                    )
                                    yield "content", content
                            else:
                                # 处理其他模型的输出
                                if delta.get("content"):
                                    content = delta["content"]
                                    if content == "":  # 只跳过完全空的字符串
                                        continue
                                    logger.debug("非原生推理内容：%s", content)
                                    accumulated_content += content

                                    # 检查累积的内容是否包含完整的 think 标签对
                                    is_complete, processed_content = (
                                        self._process_think_tag_content(
                                            accumulated_content
                                        )
                                    )

                                    if "<think>" in content and not is_collecting_think:
                                        # 开始收集推理内容
                                        logger.debug("开始收集推理内容：%s", content)
                                        is_collecting_think = True
                                        yield "reasoning", content
                                    elif is_collecting_think:
                                        if "</think>" in content:
                                            # 推理内容结束
                                            logger.debug("推理内容结束：%s", content)
                                            is_collecting_think = False
                                            yield "reasoning", content
                                            # 输出空的 content 来触发 Claude 处理
                                            yield "content", ""
                                            # 重置累积内容
                                            accumulated_content = ""
                                        else:
                                            # 继续收集推理内容
                                            yield "reasoning", content
                                    else:
                                        # 普通内容
                                        yield "content", content

            except json.JSONDecodeError as e:
                logger.error("JSON 解析错误: %s", e)
                raise RuntimeError from e
            except Exception as e:
                logger.error("处理 chunk 时发生错误: %s", e)
                raise
