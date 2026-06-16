"""
运行指标记录 — Loop Engineering 可观测性基础设施
每次 workflow 完成后记录关键指标到 data/metrics.jsonl
"""
import json
import os
from datetime import datetime
from pathlib import Path


METRICS_PATH = Path(__file__).parent.parent.parent / "data" / "metrics.jsonl"


def record_run(state: dict, elapsed_seconds: float = 0):
    """
    记录一次完整 workflow 运行的指标。
    安全调用：任何字段缺失都不应抛异常。
    """
    try:
        METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "keyword": state.get("topic_keyword", ""),
            "pattern": state.get("article_pattern", ""),
            "selected_title": state.get("selected_title", "")[:80],
            "write_round": state.get("write_round", 0),
            "regroup_round": state.get("regroup_round", 0),
            "final_score": state.get("overall_score", 0),
            "score_history": state.get("score_history", []),
            "quality_scores": [
                {"dim": s.get("dimension", ""), "score": s.get("score", 0)}
                for s in state.get("quality_scores", [])
                if isinstance(s, dict)
            ],
            "char_count": len(state.get("edited_article", "") or state.get("draft_article", "")),
            "error_count": len(state.get("errors", [])),
            "publish_success": state.get("publish_success", False),
            "dry_run": state.get("dry_run", True),
            "elapsed_seconds": round(elapsed_seconds, 1),
        }

        with open(METRICS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record
    except Exception as e:
        # 指标记录失败不应影响主流程
        print(f"[metrics] 记录失败（已忽略）: {e}")
        return None


def get_recent_stats(n: int = 10) -> dict:
    """
    读取最近 n 次运行统计，用于 dashboard 或决策。
    返回 {avg_score, avg_rounds, common_weak_dims, total_runs}
    """
    if not METRICS_PATH.exists():
        return {"total_runs": 0}

    try:
        lines = METRICS_PATH.read_text(encoding="utf-8").strip().split("\n")
        records = []
        for line in lines[-n:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        if not records:
            return {"total_runs": 0}

        scores = [r.get("final_score", 0) for r in records]
        rounds = [r.get("write_round", 0) for r in records]

        # 维度弱点统计
        from collections import Counter
        dim_scores = {}
        for r in records:
            for qs in r.get("quality_scores", []):
                dim = qs.get("dim", "")
                sc = qs.get("score", 0)
                if dim:
                    dim_scores.setdefault(dim, []).append(sc)

        weak_dims = {}
        for dim, sc_list in dim_scores.items():
            avg = sum(sc_list) / len(sc_list)
            if avg < 7.0:
                weak_dims[dim] = round(avg, 1)

        return {
            "total_runs": len(lines),
            "recent_runs": len(records),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "avg_rounds": round(sum(rounds) / len(rounds), 1) if rounds else 0,
            "weak_dims": weak_dims,
        }
    except Exception:
        return {"total_runs": 0}
