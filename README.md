# Knowledge Base System

AI-powered knowledge base that automatically discovers, generates, and curates technology content using LLMs and GitHub automation.

## Overview

This system uses AI agents to:
- **Discover** new content from GitHub releases, arXiv papers, and other sources
- **Generate** well-structured markdown articles with YAML frontmatter
- **Review** content through GitHub Pull Requests
- **Publish** approved content to a static site (GitHub Pages)

## Features

- ✅ **Extensible LLM Support** - Works with Anthropic, OpenAI, DeepSeek, Ollama, and more
- ✅ **Multiple Discovery Sources** - GitHub, arXiv, with easy plugin architecture
- ✅ **Automated PR Workflow** - Human review before publication
- ✅ **Content Deduplication** - SHA-256 hash-based duplicate detection
- ✅ **Credibility Scoring** - Automatically scores content quality (1-10)
- ✅ **Static Site Generation** - Fast, SEO-friendly Docusaurus site
- ✅ **CI/CD Integration** - GitHub Actions for automation

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  External       │────▶│  Discovery   │────▶│  Content    │
│  Sources        │     │  Agents      │     │  Generator  │
│  • GitHub       │     │              │     │  (LLM)      │
│  • arXiv        │     └──────────────┘     └──────┬──────┘
└─────────────────┘                                 │
                                                    ▼
                    ┌───────────────────────────────────────┐
                    │         GitHub PR Workflow            │
                    │  • Create branch                      │
                    │  • Commit content                     │
                    │  • Human review                       │
                    └────────────────┬──────────────────────┘
                                     │
                                     ▼
                    ┌───────────────────────────────────────┐
                    │      GitHub Pages Deployment          │
                    │  • Build Docusaurus site              │
                    │  • Deploy to Pages                    │
                    └───────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- GitHub repository
- API keys for your chosen LLM provider

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/knowledge-base.git
cd knowledge-base
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Node.js dependencies:**
```bash
npm install
```

4. **Configure the agent:**

Edit `scripts/config.yaml`:
```yaml
github:
  owner: "your-org"
  repo: "knowledge-base"

ai:
  provider: "anthropic"  # or openai, deepseek
  model: "claude-sonnet-4-20250514"
```

5. **Set environment variables:**
```bash
export GITHUB_TOKEN="your-github-token"
export ANTHROPIC_API_KEY="your-anthropic-key"
# or OPENAI_API_KEY, DEEPSEEK_API_KEY
```

6. **Run the agent:**
```bash
python -m scripts.agent
```

### Development

**Run tests:**
```bash
pytest tests/ -v --cov=scripts
```

**Lint code:**
```bash
ruff check scripts/
```

**Build site locally:**
```bash
npm run start
```

## Configuration

The system is configured via `scripts/config.yaml`:

### AI Configuration

```yaml
ai:
  provider: "anthropic"  # anthropic, openai, deepseek, ollama
  model: "claude-sonnet-4-20250514"
  max_tokens: 4000
  temperature: 0.3
  rate_limit:
    requests_per_minute: 50
    tokens_per_minute: 150000
```

### Discovery Sources

```yaml
sources:
  - id: "github_ai_releases"
    type: "github"
    enabled: true
    query:
      repos:
        - "openai/openai-python"
        - "anthropic/anthropic-sdk-python"
      event_types: ["release"]
    domain: "ai"
    level: "intermediate"
```

### GitHub Settings

```yaml
github:
  owner: "your-org"
  repo: "knowledge-base"
  pr_labels: ["ai-generated", "needs-review"]
  reviewers: ["@expert1", "@expert2"]
```

## GitHub Actions Setup

### Required Secrets

Add these secrets to your GitHub repository:

- `ANTHROPIC_API_KEY` - Anthropic API key (if using Claude)
- `OPENAI_API_KEY` - OpenAI API key (if using GPT)
- `DEEPSEEK_API_KEY` - DeepSeek API key (if using DeepSeek)

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Workflow Triggers

**Content Agent** (`.github/workflows/content-agent.yml`):
- Manual: Workflow dispatch
- Scheduled: Weekly (Monday 10:00 UTC)
- External: Repository dispatch event

**Deployment** (`.github/workflows/deploy.yml`):
- Automatic: On push to `main` branch
- Manual: Workflow dispatch

### External Cron Setup

To avoid GitHub's 60-day workflow inactivity limit, use an external cron service:

**Using Vercel Cron (Free):**
```javascript
// vercel.json
{
  "crons": [{
    "path": "/api/trigger-agent",
    "schedule": "0 10 * * 1"
  }]
}

// api/trigger-agent.js
export default async function handler(req, res) {
  const response = await fetch(
    'https://api.github.com/repos/your-org/knowledge-base/dispatches',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ event_type: 'scheduled-run' })
    }
  );
  res.status(200).json({ status: 'triggered' });
}
```

## Extending the System

### Adding a New LLM Provider

1. **Create adapter class:**

```python
# scripts/adapters/custom.py
from .base import BaseModelAdapter, GenerationRequest, GenerationResponse

class CustomAdapter(BaseModelAdapter):
    def __init__(self, api_key: str, model: str = "custom-model"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # Implement your API call here
        pass
    
    def get_name(self) -> str:
        return f"custom:{self.model}"
```

2. **Register with factory:**

```python
from scripts.adapters import ModelFactory
from scripts.adapters.custom import CustomAdapter

ModelFactory.register("custom", CustomAdapter)
```

3. **Update config:**

```yaml
ai:
  provider: "custom"
  model: "custom-model"
  api_key_env: "CUSTOM_API_KEY"
```

### Adding a New Discovery Source

1. **Create discoverer class:**

```python
# scripts/discovery/custom.py
from .base import BaseDiscoverer, DiscoveredItem

class CustomDiscoverer(BaseDiscoverer):
    def discover(self, last_processed_id=None) -> list[DiscoveredItem]:
        # Implement your discovery logic
        items = []
        # ... fetch from your source ...
        return items
    
    def get_source_type(self) -> str:
        return "custom"
```

2. **Update agent to use it:**

```python
# scripts/agent.py
from scripts.discovery.custom import CustomDiscoverer

# In _discover_content method:
elif source_type == "custom":
    discoverer = CustomDiscoverer(source_id, source_config)
```

3. **Add to config:**

```yaml
sources:
  - id: "custom_source"
    type: "custom"
    enabled: true
    query:
      # Your custom configuration
    domain: "ai"
    level: "beginner"
```

## Content Structure

Generated content follows this frontmatter schema:

```yaml
---
# Required fields
title: "Article Title"
domain: "ai"  # ai, blockchain, protocol
level: "beginner"  # beginner, intermediate, master
category: "article"  # article, tool, resource, video
tags: ["machine-learning", "python"]

# Metadata
created: "2026-02-28T10:00:00Z"
updated: "2026-02-28T10:00:00Z"
sources:
  - url: "https://example.com"
    title: "Source Title"
    accessed_at: "2026-02-28T10:00:00Z"
ai_reviewed: true
human_reviewed: false
status: "pending-review"

# Optional
description: "Brief description"
author: "knowledge-base-agent"
credibility_score: 8
---

# Article content starts here
```

## Troubleshooting

### Agent fails with "API key not found"

Ensure environment variables are set:
```bash
export ANTHROPIC_API_KEY="your-key"
# or OPENAI_API_KEY, DEEPSEEK_API_KEY
export GITHUB_TOKEN="your-github-token"
```

### Rate limit errors

Adjust rate limits in `config.yaml`:
```yaml
ai:
  rate_limit:
    requests_per_minute: 30  # Lower this
    tokens_per_minute: 100000  # Lower this
```

### No content generated

Check:
1. Sources are enabled in `config.yaml`
2. Discovery sources have new content since last run
3. Check agent state: `.agent-state/state.json`

### GitHub Pages not deploying

1. Enable GitHub Pages in repository settings
2. Set source to "GitHub Actions"
3. Check workflow permissions (Settings → Actions → Workflow permissions)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/your-org/knowledge-base/issues)
- Documentation: [Full technical specification](specs/01_knowledge_base_system/technical_spec.md)

## Credits

Built with:
- [Anthropic Claude](https://www.anthropic.com/)
- [Docusaurus](https://docusaurus.io/)
- [GitHub Actions](https://github.com/features/actions)
- [PyGithub](https://github.com/PyGithub/PyGithub)
