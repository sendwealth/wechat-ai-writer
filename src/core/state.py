"""
状态定义 - LangGraph 全局状态
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GlobalState(BaseModel):
    """全局状态定义"""
    # 输入参数
    topic_keyword: str = Field(default="科技", description="搜索关键词")
    wechat_config: Dict[str, Any] = Field(default={}, description="微信配置")
    dry_run: bool = Field(default=False, description="测试模式")
    
    # 搜索结果
    raw_articles: List[Dict[str, Any]] = Field(default=[], description="原始搜索文章列表")
    selected_article: Dict[str, Any] = Field(default={}, description="选中的文章")
    
    # 主题提取
    topic: str = Field(default="", description="提取的核心主题")
    highlights: List[str] = Field(default=[], description="文章亮点")
    
    # 深度搜索
    deep_search_results: List[Dict[str, Any]] = Field(default=[], description="深度搜索结果")
    
    # 文章生成
    article: str = Field(default="", description="生成的文章内容")
    
    # 图片
    article_images: List[Dict[str, Any]] = Field(default=[], description="配图列表")
    article_with_images: str = Field(default="", description="带图片的文章")
    
    # 发布
    publish_result: Dict[str, Any] = Field(default={}, description="发布结果")
    publish_success: bool = Field(default=False, description="是否发布成功")
    
    # 配置
    wechat_config: Dict[str, Any] = Field(default={}, description="微信配置")


class WorkflowInput(BaseModel):
    """工作流输入"""
    topic_keyword: str = Field(..., description="搜索关键词")
    wechat_config: Optional[Dict[str, Any]] = Field(default={}, description="微信配置（可选）")
    dry_run: bool = Field(default=False, description="是否测试模式（不发布）")


class WorkflowOutput(BaseModel):
    """工作流输出"""
    topic: str = Field(..., description="文章主题")
    article: str = Field(..., description="文章内容")
    article_with_images: str = Field(default="", description="带图文章")
    publish_success: bool = Field(default=False, description="发布成功")
    publish_result: Dict[str, Any] = Field(default={}, description="发布详情")


# ========== 节点输入输出定义 ==========

class SearchNewsInput(BaseModel):
    topic_keyword: str


class SearchNewsOutput(BaseModel):
    raw_articles: List[Dict[str, Any]]
    selected_article: Dict[str, Any]


class ExtractTopicInput(BaseModel):
    selected_article: Dict[str, Any]


class ExtractTopicOutput(BaseModel):
    topic: str
    highlights: List[str]


class DeepSearchInput(BaseModel):
    topic: str


class DeepSearchOutput(BaseModel):
    deep_search_results: List[Dict[str, Any]]


class GenerateArticleInput(BaseModel):
    topic: str
    highlights: List[str]
    deep_search_results: List[Dict[str, Any]]


class GenerateArticleOutput(BaseModel):
    article: str


class GenerateImagesInput(BaseModel):
    topic: str
    highlights: List[str]


class GenerateImagesOutput(BaseModel):
    article_images: List[Dict[str, Any]]


class AddImagesInput(BaseModel):
    article: str
    article_images: List[Dict[str, Any]]


class AddImagesOutput(BaseModel):
    article_with_images: str


class PublishInput(BaseModel):
    article_with_images: str
    topic: str
    wechat_config: Dict[str, Any]
    dry_run: bool = False


class PublishOutput(BaseModel):
    publish_result: Dict[str, Any]
    publish_success: bool
