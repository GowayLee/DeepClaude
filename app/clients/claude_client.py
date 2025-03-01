"""Claude API 客户端"""

import json
from typing import AsyncGenerator

from typing_extensions import override

from app.config.model_config import BaseModelConfig, ProviderType
from app.utils.config.manager import ModelConfigManager
from app.utils.logger import logger

from .base_client import BaseClient


class ClaudeClient(BaseClient):
    def __init__(self):
        super().__init__()
        self._model_config = ModelConfigManager.get_model_config()

    @override
    async def chat(
        self,
        base_model: BaseModelConfig,
        messages: list,
        model_arg: tuple[float, float, float, float],
        is_origin_reasoning: bool = False,
        stream: bool = True,
        system_prompt: str = None,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """流式或非流式对话

        Args:
            messages: 消息列表
            model_arg: 模型参数元组[temperature, top_p, presence_penalty, frequency_penalty]
            model: 模型名称。如果是 OpenRouter, 会自动转换为 'anthropic/claude-3.5-sonnet' 格式
            stream: 是否使用流式输出，默认为 True
            system_prompt: 系统提示

        Yields:
            tuple[str, str]: (内容类型, 内容)
                内容类型: "answer"
                内容: 实际的文本内容
        """

        # Obtain relevant information from model_config
        model_id, base_url, api_key, provider_type , use_proxy= (
            self._model_config.get_model_request_info(base_model.name)
        )

        if provider_type == ProviderType.OPENROUTER:
            # 转换模型名称为 OpenRouter 格式
            model = "anthropic/claude-3.5-sonnet"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ErlichLiu/DeepClaude",  # OpenRouter 需要
                "X-Title": "DeepClaude",  # OpenRouter 需要
            }

            # 传递 OpenRouterOneAPI system prompt
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

            data = {
                "model": model,  # OpenRouter 使用 anthropic/claude-3.5-sonnet 格式
                "messages": messages,
                "stream": True,
                "temperature": 1
                if model_arg[0] < 0 or model_arg[0] > 1
                else model_arg[0],
                "top_p": model_arg[1],
                "presence_penalty": model_arg[2],
                "frequency_penalty": model_arg[3],
            }
        elif provider_type == ProviderType.OPENAI_COMPATIBLE:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 传递 OneAPI system prompt
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

            data = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "temperature": 1
                if model_arg[0] < 0 or model_arg[0] > 1
                else model_arg[0],
                "top_p": model_arg[1],
                "presence_penalty": model_arg[2],
                "frequency_penalty": model_arg[3],
            }
        elif provider_type == ProviderType.ANTHROPIC:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "accept": "text/event-stream",
            }

            data = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 8192,
                "stream": True,
                "temperature": 1
                if model_arg[0] < 0 or model_arg[0] > 1
                else model_arg[0],  # Claude仅支持temperature与top_p
                "top_p": model_arg[1],
            }

            # Anthropic 原生 API 支持 system 参数
            if system_prompt:
                data["system"] = system_prompt
        else:
            raise ValueError(f"不支持的Claude Provider: {provider_type}")

        logger.debug("开始对话：%s", data)

        if stream:
            async for chunk in self._make_request(
                base_url, headers, data, use_proxy=use_proxy
            ):
                chunk_str = chunk.decode("utf-8")
                if not chunk_str.strip():
                    continue

                for line in chunk_str.split("\n"):
                    if line.startswith("data: "):
                        json_str = line[6:]  # 去掉 'data: ' 前缀
                        if json_str.strip() == "[DONE]":
                            return

                        try:
                            data = json.loads(json_str)
                            if provider_type in (
                                ProviderType.OPENROUTER,
                                ProviderType.OPENAI_COMPATIBLE,
                            ):
                                # OpenRouter/OneApi 格式
                                content = (
                                    data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    yield "answer", content
                            elif provider_type == ProviderType.ANTHROPIC:
                                # Anthropic 格式
                                if data.get("type") == "content_block_delta":
                                    content = data.get("delta", {}).get("text", "")
                                    if content:
                                        yield "answer", content
                            else:
                                raise ValueError(
                                    f"不支持的Claude Provider: {provider_type}"
                                )
                        except json.JSONDecodeError as e:
                            logger.error("JSON 解析错误: %s", e)
                            raise RuntimeError from e
        else:
            # 非流式输出
            async for chunk in self._make_request(
                base_url, headers, data, use_proxy=use_proxy
            ):
                try:
                    response = json.loads(chunk.decode("utf-8"))
                    if provider_type in (
                        ProviderType.OPENROUTER,
                        ProviderType.OPENAI_COMPATIBLE,
                    ):
                        content = (
                            response.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )
                        if content:
                            yield "answer", content
                    elif provider_type == ProviderType.ANTHROPIC:
                        content = response.get("content", [{}])[0].get("text", "")
                        if content:
                            yield "answer", content
                    else:
                        raise ValueError(f"不支持的Claude Provider: {provider_type}")
                except json.JSONDecodeError as e:
                    logger.error("JSON 解析错误: %s", e)
                    raise RuntimeError from e
