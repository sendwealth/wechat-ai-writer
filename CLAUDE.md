# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WeChat Official Account AI article writer. A LangGraph-based multi-agent pipeline that searches for tech news, generates Chinese-language articles via LLM, creates images, and publishes drafts to WeChat.

All prompts, templates, and generated content are in Chinese. The UI language is Chinese.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API keys

# Run workflow (dry-run = no publishing)
python src/main.py --keyword "AI" --dry-run

# Full run (generates and publishes)
python src/main.py --keyword "AI"

# HTTP API server
python src/main.py --server --port 5000

# Quick test shortcut
bash scripts/test.sh
```

There is no test suite in the repo (`test_*.py` is gitignored). No linter or type checker is configured.

## Architecture

**Production workflow** is the v2 multi-agent pipeline defined in `src/graph/workflow.py`:

```
orchestrator ──→ research (parallel)
               ──→ title_generator (parallel)

research ──→ create_outline
title_generator ──→ create_outline

create_outline ──→ writer ──→ critic ──→ editor ──→ visual ──→ layout ──→ final_check ──→ publisher
                              ↑          │
                              └──rewrite─┘  (score < 7.5, up to 5 rounds)

final_check ──→ regroup ──→ orchestrator  (score < 7.0, switch pattern, up to 2 times)
```

12 nodes, 2 conditional edges, `MemorySaver` checkpointer. State is `WorkflowState` (TypedDict in `src/graph/state.py`). Routing logic in `src/graph/routers.py`.

Each node is a pure function: `(state: dict, config) -> dict`. Nodes return partial state dicts that LangGraph merges back.

**Legacy v1 pipeline** exists in `src/core/` (7-node linear graph) but is not used by `main.py`.

## Key Design Patterns

- **Factory pattern**: `create_llm()` (`src/llm/base.py`), `create_search()` (`src/search/__init__.py`), `create_image_generator()` (`src/image/generator.py`) — all selected via env vars
- **All LLM providers use `langchain_openai.ChatOpenAI`** with different `base_url`/`api_key` — they all speak the OpenAI-compatible protocol
- **UnifiedLLM with retry**: `src/llm/base.py` wraps all LLM calls with exponential backoff retry for 429/5xx errors
- **Unified JSON parser**: `src/utils/json_parser.py` — `parse_llm_json()` handles markdown code blocks, truncated JSON (unterminated strings), bracket completion, and regex fallback. All agents use this instead of inline `split("```json")` patterns
- **Editor separator format**: Editor outputs article as plain text + `---EDIT_NOTES---` separator + JSON notes. Avoids wrapping full articles in JSON which causes truncation
- **Config layering**: env vars for secrets/providers, `config/settings.yaml` for per-agent LLM params (temperature, max_tokens), Markdown in `config/prompts/` for prompts
- **Error handling**: Every node has try/except with fallback values so the workflow always completes
- **Score stagnation exit**: Writer-critic loop exits early if score doesn't improve for 2 consecutive rounds

## Working Directory Note

`main.py` uses bare imports like `from graph.workflow import ...`. Run it from the project root as `python src/main.py` — Python adds the script's directory (`src/`) to `sys.path`.

## Environment Variables

Key variables (see `.env.example` for full list):
- `LLM_PROVIDER` — `glm` (default/recommended), `openai`, or `doubao`
- `ZAI_API_KEY` — Zhipu AI key (for GLM-5 + CogView)
- `SERPAPI_KEY` — Required for web search
- `WECHAT_APPID` / `WECHAT_APPSECRET` — For WeChat publishing (auto token management)
- `IMAGE_PROVIDER` — `placeholder` (free), `cogview` (recommended), or `dalle3`
- `NUM_IMAGES` — Number of images to generate (default: 2)

## HTTP API

FastAPI server with two endpoints:
- `POST /run` — `{"keyword": "...", "dry_run": false}` — runs full workflow
- `GET /health` — health check

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health
