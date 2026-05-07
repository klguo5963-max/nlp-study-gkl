"""
请求与响应的 Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Union


class TextClassifyRequest(BaseModel):
    """分类请求"""
    request_id: Optional[str] = Field(None, description="请求 id，用于追踪调试")
    request_text: Union[str, list[str]] = Field(..., description="待分类文本，支持单条字符串或批量列表")


class TextClassifyResponse(BaseModel):
    """分类响应"""
    request_id: Optional[str] = Field(None, description="请求 id")
    request_text: Union[str, list[str]] = Field(default="", description="原始输入文本")
    classify_result: Union[str, list[str]] = Field(default="", description="分类结果")
    classify_time: float = Field(default=0.0, description="分类耗时（秒）")
    error_msg: str = Field(default="", description="异常信息，成功时为 ok")
