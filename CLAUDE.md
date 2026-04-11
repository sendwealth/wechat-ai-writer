# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WeChat Official Account AI article writer. A LangGraph-based pipeline that searches for tech news, generates Chinese-language articles via LLM, creates images, and publishes drafts to WeChat.

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

**7-step linear LangGraph StateGraph** defined in `src/core/workflow.py`:

1. `search_tech_news` — SerpAPI Google search
2. `extract_topic` — LLM extracts core topic and highlights
3. `deep_search` — Follow-up search for facts/data
4. `generate_article` — LLM writes full article
5. `generate_images` — Creates images (CogView/DALL-E/placeholder)
6. `add_images` — Inserts images into HTML article
7. `publish_to_wechat` — Publishes draft via WeChat API

Each node is a pure function: `(state: GlobalState, config: RunnableConfig) -> Dict[str, Any]`. Nodes return partial state dicts that LangGraph merges back into `GlobalState` (Pydantic model in `src/core/state.py`).

**Running the pipeline**: `main_workflow.invoke(input_data)` invokes the compiled graph synchronously.

## Key Design Patterns

- **Factory pattern**: `create_llm()` (`src/llm/__init__.py`), `create_search()` (`src/search/__init__.py`), `create_image_generator()` (`src/image/generator.py`) — all selected via env vars (`LLM_PROVIDER`, `SEARCH_PROVIDER`, `IMAGE_PROVIDER`)
- **All LLM providers use `langchain_openai.ChatOpenAI`** with different `base_url`/`api_key` — they all speak the OpenAI-compatible protocol
- **Config layering**: env vars for secrets/providers, JSON files in `config/llm/` for per-task LLM params (temperature, max_tokens), YAML in `config/title_templates.yaml` for title patterns, Markdown in `config/prompts/` for article structure
- **Error handling**: Every node has try/except with fallback values so the workflow always completes

## Working Directory Note

`main.py` uses bare imports like `from core.workflow import ...`. Run it from the project root as `python src/main.py` — Python adds the script's directory (`src/`) to `sys.path`.

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
