"""Chat API"""

from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ..services.deepclaude import ChatService
from ..config.manager import ConfigManager
from ..utils.auth import validate_api_key

# 创建APIRouter实例
router = APIRouter(
    prefix="/v1/chat",  # 路由前缀
    tags=["Chat"],  # OpenAPI标签
    dependencies=[Depends(validate_api_key)],  # 路由级别的依赖
)

# 初始化服务层
chat_service = ChatService()


# 聊天补全接口
@router.post("/completions", response_model=dict)
async def create_chat_completion(request: dict):
    """
    处理聊天补全请求
    :param request: 请求体，包含消息和模型信息
    :return: 聊天补全结果
    """
    try:
        # 调用服务层处理请求
        result = await chat_service.generate_completion(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# 获取模型列表接口
@router.get("/models", response_model=List[str])
async def get_models():
    """
    获取可用的模型列表
    :return: 模型名称列表
    """
    try:
        # 从配置管理器中获取模型列表
        models = ConfigManager.instance().get_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
