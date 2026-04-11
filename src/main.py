#!/usr/bin/env python3
"""
WeChat AI Writer v2.0 - 多 Agent 微信公众号写作系统
入口：CLI + HTTP API
"""
import argparse
import json
import uuid
from pathlib import Path
from graph.workflow import main_workflow
from utils.logger import logger


def run_workflow(keyword: str, dry_run: bool = False):
    """
    运行多 Agent 工作流

    Args:
        keyword: 搜索关键词
        dry_run: 是否测试模式（不发布）
    """
    logger.info("=" * 60)
    logger.info("🚀 启动 WeChat AI Writer v2.0 (Multi-Agent)")
    logger.info("=" * 60)
    logger.info(f"📝 关键词: {keyword}")
    logger.info(f"🔧 测试模式: {dry_run}")
    logger.info("=" * 60)

    # 准备输入
    input_data = {
        "topic_keyword": keyword,
        "dry_run": dry_run,
        "write_round": 0,
        "regroup_round": 0,
        "errors": [],
    }

    # 运行工作流（带检查点）
    thread_id = str(uuid.uuid4())[:8]
    config = {"configurable": {"thread_id": thread_id}}

    result = main_workflow.invoke(input_data, config)

    # 输出结果
    logger.info("\n" + "=" * 60)
    logger.info("✅ 工作流完成")
    logger.info("=" * 60)
    logger.info(f"📝 标题: {result.get('selected_title', 'N/A')}")
    logger.info(f"📂 分类: {result.get('topic_category', 'N/A')}")
    logger.info(f"🏗️ 结构: {result.get('article_pattern', 'N/A')}")
    logger.info(f"📊 质量分: {result.get('overall_score', 'N/A')}/10")
    logger.info(f"🔄 写作轮次: {result.get('write_round', 0)}")
    logger.info(f"🔄 降级重做: {result.get('regroup_round', 0)}")
    logger.info(f"📄 文章长度: {len(result.get('draft_article', ''))} 字符")
    logger.info(f"📊 发布状态: {'成功' if result.get('publish_success') else '失败'}")

    errors = result.get("errors", [])
    if errors:
        logger.warning(f"⚠️ 错误 ({len(errors)}):")
        for e in errors[:5]:
            logger.warning(f"   - [{e.get('severity', '?')}] {e.get('node', '?')}: {e.get('error', '?')[:80]}")

    logger.info("=" * 60)

    # 保存结果
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    safe_name = keyword.replace("/", "_").replace(" ", "_")[:20]
    title = result.get('selected_title', 'untitled')[:20]
    output_file = output_dir / f"{safe_name}_{title}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        # 保存关键字段（排除大体积的 HTML）
        save_data = {
            "keyword": keyword,
            "title": result.get("selected_title", ""),
            "category": result.get("topic_category", ""),
            "pattern": result.get("article_pattern", ""),
            "audience": result.get("target_audience", ""),
            "overall_score": result.get("overall_score", 0),
            "quality_scores": result.get("quality_scores", []),
            "write_round": result.get("write_round", 0),
            "regroup_round": result.get("regroup_round", 0),
            "article_length": len(result.get("draft_article", "")),
            "html_length": len(result.get("article_html", "")),
            "publish_success": result.get("publish_success", False),
            "publish_result": result.get("publish_result", {}),
            "errors": result.get("errors", []),
            "article": result.get("draft_article", ""),
            "article_html": result.get("article_html", ""),
        }
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 结果已保存: {output_file}")

    return result


def start_server(port: int = 5000):
    """启动 HTTP 服务"""
    import uvicorn
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="WeChat AI Writer v2.0 API")

    class WorkflowRequest(BaseModel):
        keyword: str
        dry_run: bool = False

    @app.post("/run")
    async def api_run(request: WorkflowRequest):
        """运行工作流（异步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, run_workflow, request.keyword, request.dry_run
        )
        return {
            "title": result.get("selected_title", ""),
            "score": result.get("overall_score", 0),
            "write_round": result.get("write_round", 0),
            "publish_success": result.get("publish_success", False),
        }

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "2.0"}

    logger.info(f"🌐 启动 HTTP 服务: http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    parser = argparse.ArgumentParser(description="WeChat AI Writer v2.0")
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
