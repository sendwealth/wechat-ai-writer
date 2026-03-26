#!/usr/bin/env python3
"""
主程序入口
"""
import argparse
import json
import asyncio
from pathlib import Path
from core.workflow import main_workflow
from utils.logger import logger


def run_workflow(keyword: str, wechat_config: dict = None, dry_run: bool = False):
    """
    运行工作流
    
    Args:
        keyword: 搜索关键词
        wechat_config: 微信配置（可选）
        dry_run: 是否测试模式
    """
    logger.info("="*60)
    logger.info("🚀 启动 WeChat AI Writer")
    logger.info("="*60)
    logger.info(f"📝 关键词: {keyword}")
    logger.info(f"🔧 测试模式: {dry_run}")
    logger.info("="*60)
    
    # 准备输入
    input_data = {
        "topic_keyword": keyword,
        "wechat_config": wechat_config or {},
        "dry_run": dry_run
    }
    
    # 运行工作流
    result = main_workflow.invoke(input_data)
    
    # 输出结果
    logger.info("\n" + "="*60)
    logger.info("✅ 工作流完成")
    logger.info("="*60)
    logger.info(f"📝 主题: {result['topic']}")
    logger.info(f"📄 文章长度: {len(result['article'])} 字符")
    logger.info(f"📊 发布状态: {'成功' if result['publish_success'] else '失败'}")
    logger.info("="*60)
    
    # 保存结果
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{keyword}_{result['topic'][:20]}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 结果已保存: {output_file}")
    
    return result


def start_server(port: int = 5000):
    """启动 HTTP 服务"""
    import uvicorn
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    app = FastAPI(title="WeChat AI Writer API")
    
    class WorkflowRequest(BaseModel):
        keyword: str
        wechat_config: dict = {}
        dry_run: bool = False
    
    @app.post("/run")
    async def api_run(request: WorkflowRequest):
        """运行工作流"""
        result = run_workflow(
            request.keyword,
            request.wechat_config,
            request.dry_run
        )
        return result
    
    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "ok"}
    
    logger.info(f"🌐 启动 HTTP 服务: http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    parser = argparse.ArgumentParser(description="WeChat AI Writer")
    parser.add_argument("--keyword", "-k", type=str, help="搜索关键词")
    parser.add_argument("--dry-run", action="store_true", help="测试模式（不发布）")
    parser.add_argument("--server", action="store_true", help="启动 HTTP 服务")
    parser.add_argument("--port", "-p", type=int, default=5000, help="HTTP 服务端口")
    
    args = parser.parse_args()
    
    if args.server:
        start_server(args.port)
    elif args.keyword:
        run_workflow(args.keyword, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
