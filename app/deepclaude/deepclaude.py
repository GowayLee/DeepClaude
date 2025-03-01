"""DeepClaude 服务，用于协调 DeepSeek 和 Claude API 的调用"""

import asyncio
import json
import time
from typing import AsyncGenerator

import tiktoken

from app.clients import ClaudeClient, DeepSeekClient
from app.config.model_config import DeepModelConfig, ModelConfig
from app.utils.config.manager import ModelConfigManager
from app.utils.logger import logger


class DeepClaude:
    """处理 DeepSeek 和 Claude API 的流式输出衔接"""

    def __init__(self):
        self.deepseek_client = DeepSeekClient()
        self.claude_client = ClaudeClient()
        self._model_config: ModelConfig = ModelConfigManager.get_model_config()

    async def chat_completions_with_stream(
        self,
        deep_model: DeepModelConfig,
        messages: list,
        model_arg: tuple[float, float, float, float],
    ) -> AsyncGenerator[bytes, None]:
        """处理完整的流式输出过程

        Args:
            messages: 初始消息列表
            model: 模型名称
            model_arg: 模型参数

        Yields:
            字节流数据，格式如下：
            {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "created": timestamp,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "reasoning_content": reasoning_content,
                        "content": content
                    }
                }]
            }
        """

        # Obtain relevant information from model_config
        deepseek_model = self._model_config.get_base_model(deep_model.reason_model)
        claude_model = self._model_config.get_base_model(deep_model.answer_model)

        # 生成唯一的会话ID和时间戳
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())

        # 创建队列，用于收集输出数据
        output_queue = asyncio.Queue()
        claude_queue = asyncio.Queue()

        # 用于存储 DeepSeek 的推理累积内容
        reasoning_content = []

        async def process_deepseek():
            logger.info(
                "开始处理 DeepSeek 流，使用模型：%s, 提供商: %s",
                deepseek_model.model_id,
                self._model_config.get_provider(deepseek_model.provider).name,
            )
            try:
                async for content_type, content in self.deepseek_client.chat(
                    deepseek_model,
                    messages,
                    None,  # There is no model arg setting for deepseek_model
                    is_origin_reasoning=deep_model.is_origin_reasoning,
                    stream=True,
                ):
                    if content_type == "reasoning":
                        reasoning_content.append(content)
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": deepseek_model.model_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "reasoning_content": content,
                                        "content": "",
                                    },
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
                    elif content_type == "content":
                        # 当收到 content 类型时，将完整的推理内容发送到 claude_queue，并结束 DeepSeek 流处理
                        logger.info(
                            "DeepSeek 推理完成，收集到的推理内容长度：%d",
                            len("".join(reasoning_content)),
                        )
                        await claude_queue.put("".join(reasoning_content))
                        break
            except (ValueError, RuntimeError, Exception) as e:
                logger.error("处理 DeepSeek 流时发生错误: %s", e)
                await claude_queue.put("")
                raise
            # 用 None 标记 DeepSeek 任务结束
            logger.info("DeepSeek 任务处理完成，标记结束")
            await output_queue.put(None)

        async def process_claude():
            try:
                logger.info("等待获取 DeepSeek 的推理内容...")
                reasoning = await claude_queue.get()
                logger.debug(
                    "获取到推理内容，内容长度：%d", len(reasoning) if reasoning else 0
                )
                if not reasoning:
                    logger.warning("未能获取到有效的推理内容，将使用默认提示继续")
                    reasoning = "获取推理内容失败"

                # 构造 Claude 的输入消息
                claude_messages = messages.copy()
                combined_content = f"""
                Here's my another model's reasoning process:\n{reasoning}\n\n
                Based on this reasoning, provide your response directly to me:"""

                # 提取 system message 并同时过滤掉 system messages
                system_content = ""
                non_system_messages = []
                for message in claude_messages:
                    if message.get("role", "") == "system":
                        system_content += message.get("content", "") + "\n"
                    else:
                        non_system_messages.append(message)

                # 更新消息列表为不包含 system 消息的列表
                claude_messages = non_system_messages

                # 检查过滤后的消息列表是否为空
                if not claude_messages:
                    raise ValueError("消息列表为空，无法处理 Claude 请求")

                # 获取最后一个消息并检查其角色
                last_message = claude_messages[-1]
                if last_message.get("role", "") != "user":
                    raise ValueError("最后一个消息的角色不是用户，无法处理请求")

                # 修改最后一个消息的内容
                original_content = last_message["content"]
                fixed_content = f"Here's my original input:\n{original_content}\n\n{combined_content}"
                last_message["content"] = fixed_content

                logger.info(
                    "开始处理 Claude 流，使用模型：%s, 提供商: %s",
                    claude_model.model_id,
                    self._model_config.get_provider(claude_model.provider).name,
                )

                # 检查 system_prompt
                system_content = system_content.strip() if system_content else None
                if system_content:
                    logger.debug("使用系统提示: %s...", system_content[:100])

                async for content_type, content in self.claude_client.chat(
                    claude_model,
                    messages=claude_messages,
                    model_arg=model_arg,
                    stream=True,
                    system_prompt=system_content,
                ):
                    if content_type == "answer":
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": claude_model.model_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"role": "assistant", "content": content},
                                }
                            ],
                        }
                        await output_queue.put(
                            f"data: {json.dumps(response)}\n\n".encode("utf-8")
                        )
            except (ValueError, RuntimeError, Exception) as e:
                logger.error("处理 Claude 流时发生错误: %s", e)
                raise
            # 用 None 标记 Claude 任务结束
            logger.info("Claude 任务处理完成，标记结束")
            await output_queue.put(None)

        # 创建并发任务
        asyncio.create_task(process_deepseek())
        asyncio.create_task(process_claude())

        # 等待两个任务完成，通过计数判断
        finished_tasks = 0
        while finished_tasks < 2:
            item = await output_queue.get()
            if item is None:
                finished_tasks += 1
            else:
                yield item

        # 发送结束标记
        yield b"data: [DONE]\n\n"

    async def chat_completions_without_stream(
        self,
        deep_model: DeepModelConfig,
        messages: list,
        model_arg: tuple[float, float, float, float],
    ) -> dict:
        """处理非流式输出过程

        Args:
            messages: 初始消息列表
            model: 模型名称
            model_arg: 模型参数

        Returns:
            dict: OpenAI 格式的完整响应
        """

        # Obtain relevant information from model_config
        deepseek_model = self._model_config.get_base_model(deep_model.reason_model)
        claude_model = self._model_config.get_base_model(deep_model.answer_model)

        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())
        reasoning_content = []

        # 1. 获取 DeepSeek 的推理内容（仍然使用流式）
        try:
            async for content_type, content in self.deepseek_client.chat(
                deepseek_model,
                messages,
                None,
                is_origin_reasoning=deep_model.is_origin_reasoning,
                stream=True,
            ):
                if content_type == "reasoning":
                    reasoning_content.append(content)
                elif content_type == "content":
                    break
        except (ValueError, RuntimeError, Exception) as e:
            logger.error("获取 DeepSeek 推理内容时发生错误: %s", e)
            reasoning_content = ["获取推理内容失败"]
            raise

        # 2. 构造 Claude 的输入消息
        reasoning = "".join(reasoning_content)
        claude_messages = messages.copy()

        combined_content = f"""
            Here's my another model's reasoning process:\n{reasoning}\n\n
            Based on this reasoning, provide your response directly to me:"""

        # 提取 system message 并同时从原始 messages 中过滤掉 system messages
        system_content = ""
        non_system_messages = []
        for message in claude_messages:
            if message.get("role", "") == "system":
                system_content += message.get("content", "") + "\n"
            else:
                non_system_messages.append(message)

        # 更新消息列表为不包含 system 消息的列表
        claude_messages = non_system_messages

        # 获取最后一个消息并检查其角色
        last_message = claude_messages[-1]
        if last_message.get("role", "") == "user":
            original_content = last_message["content"]
            fixed_content = (
                f"Here's my original input:\n{original_content}\n\n{combined_content}"
            )
            last_message["content"] = fixed_content

        # 拼接所有 content 为一个字符串，计算 token
        token_content = "\n".join(
            [message.get("content", "") for message in claude_messages]
        )
        encoding = tiktoken.encoding_for_model("gpt-4o")
        input_tokens = encoding.encode(token_content)
        logger.debug(f"输入 Tokens: {len(input_tokens)}")

        logger.debug("claude messages: " + str(claude_messages))
        # 3. 获取 Claude 的非流式响应
        try:
            answer = ""
            output_tokens = []  # 初始化 output_tokens

            # 检查 system_prompt
            system_content = system_content.strip() if system_content else None
            if system_content:
                logger.debug(f"使用系统提示: {system_content[:100]}...")

            async for content_type, content in self.claude_client.chat(
                claude_model,
                messages=claude_messages,
                model_arg=model_arg,
                stream=False,
                system_prompt=system_content,
            ):
                if content_type == "answer":
                    answer += content
                    output_tokens = encoding.encode(answer)  # 更新 output_tokens
                logger.debug(f"输出 Tokens: {len(output_tokens)}")

            # 4. 构造 OpenAI 格式的响应
            return {
                "id": chat_id,
                "object": "chat.completion",
                "created": created_time,
                "model": claude_model.model_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": answer,
                            "reasoning_content": reasoning,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": len(input_tokens),
                    "completion_tokens": len(output_tokens),
                    "total_tokens": len(input_tokens + output_tokens),
                },
            }
        except (ValueError, RuntimeError, Exception) as e:
            logger.error("获取 Claude 响应时发生错误: %s", e)
            raise
