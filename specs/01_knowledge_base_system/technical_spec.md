# Technical Specification: Knowledge Base System

## Document Info

| Field | Value |
|-------|-------|
| Version | 1.0 |
|| Last Updated | 2026-02-28 (Reviewed) |
|| Status | Review Complete |
| Author | Technical Architecture Team |
| Product Spec | specs/01_knowledge_base_system/product_spec.md |

---

## 1. Overview

### 1.1 Purpose

The Knowledge Base System is a Git-based content management system that uses AI agents to automatically discover, generate, and maintain curated technology knowledge content. Human review via GitHub PRs ensures quality before content is published to a static site.

### 1.2 Scope

**In Scope:**
- AI content discovery from external sources (GitHub, arXiv, Hacker News)
- AI content generation with structured metadata
- Git-based content storage with Markdown + YAML frontmatter
- GitHub PR workflow for human review
- CI/CD deployment to GitHub Pages
- Content organization by domain, level, and category
- Learning level filtering (Beginner, Intermediate, Master)

**Out of Scope:**
- User authentication/accounts
- Interactive user comments (use GitHub Issues)
- Real-time content updates (polling-based only)
- Advanced search (deferred to V1.1)
- User-generated content (AI-only for MVP)

### 1.3 Key Technical Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture Style | Serverless + GitOps | No backend needed; Git is the database and CMS |
| Primary Language | Python | Rich ecosystem for AI/ML, GitHub API, arXiv API |
| Database | None (Git) | Git provides version history, branching, PR workflow |
| Hosting | GitHub Pages | Free, integrated with GitHub, no hosting costs |
| AI Model | Claude Sonnet 4.6 (primary) / Claude Opus 4.6 (high quality) / DeepSeek V3.2 (budget) | Best for tech docs: 1M context (Opus), cost-efficient (Sonnet), budget option (DeepSeek) |
| CI/CD | GitHub Actions | Native GitHub integration, free tier sufficient |
| Scheduling | External Cron + GitHub Actions | Avoids 60-day inactivity limit |

---

## 2. System Architecture

### 2.1 Architecture Style

**Serverless + GitOps Architecture**

The system follows a GitOps approach where:
- Git repository is the single source of truth
- All changes go through PR workflow
- CI/CD automates deployment
- No persistent backend servers required

### 2.2 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE BASE SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│  │   External   │     │     AI       │     │    GitHub    │          │
│  │   Sources    │────▶│    Agent     │────▶│     PR       │          │
│  │              │     │              │     │   Workflow   │          │
│  │  • GitHub    │     │  • Python    │     │              │          │
│  │  • arXiv     │     │  • OpenAI    │     │  • Create    │          │
│  │  • HN        │     │  • Claude     │     │  • Review    │          │
│  └──────────────┘     └──────┬───────┘     │  • Merge     │          │
│                              │               └──────┬───────┘          │
│                              ▼                      │                  │
│                    ┌──────────────┐                  │                  │
│                    │   Content    │                  │                  │
│                    │  Generator   │                  │                  │
│                    └──────┬───────┘                  │                  │
│                           │                          │                  │
│                           ▼                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      GIT REPOSITORY                             │  │
│  │  • Content storage (Markdown + YAML)                           │  │
│  │  • Version history                                             │  │
│  │  • Branch management                                           │  │
│  └────────────────────────────┬────────────────────────────────────┘  │
│                               │                                          │
│                               ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    CI/CD PIPELINE                               │  │
│  │  • GitHub Actions                                              │  │
│  │  • Build static site                                          │  │
│  │  • Deploy to GitHub Pages                                      │  │
│  └────────────────────────────┬────────────────────────────────────┘  │
│                               │                                          │
│                               ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    GITHUB PAGES                                 │  │
│  │  • Static site                                                │  │
│  │  • User-facing interface                                       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Overview

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| AI Discovery Agent | Poll external sources for new content | Python + GitHub API + arXiv API |
| Content Generator | Generate markdown with YAML frontmatter | Python + OpenAI API / Anthropic API |
| GitHub PR Workflow | Human review and approval | GitHub API + GitHub Actions |
| Content Storage | Version-controlled content database | Git repository |
| CI/CD Pipeline | Build and deploy static site | GitHub Actions |
| Static Site Generator | Render content as website | Docusaurus / Astro |
| Scheduling Service | Trigger agent on schedule | External Cron (Vercel/EasyCron) |
| Feedback System | User feedback collection | GitHub Issues |

### 2.4 Component Details

#### AI Discovery Agent

- **Purpose:** Discover new content from configured sources
- **Technology:** Python 3.11+, GitHub API, arXiv API
- **Dependencies:** External APIs (GitHub, arXiv, HN)
- **Interfaces:**
  - Input: Source configuration (URL, keywords, schedule)
  - Output: List of discovered content items

#### Content Generator

- **Purpose:** Generate structured markdown content from discovered items
- **Technology:** Python 3.11+, any LLM via adapter pattern
- **Dependencies:** AI API, Content templates
- **Interfaces:**
  - Input: Discovered content item
  - Output: Markdown file with YAML frontmatter

##### Model Adapter Architecture (Extensible)

The content generator uses a **model adapter pattern** to support ANY LLM:

```python
# scripts/generators/model_adapter.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class GenerationRequest:
    prompt: str
    max_tokens: int
    temperature: float
    system_prompt: Optional[str] = None

@dataclass
class GenerationResponse:
    content: str
    model: str
    usage: dict  # input_tokens, output_tokens

class BaseModelAdapter(ABC):
    """Abstract base for all model adapters"""
    
    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass

# Implementations:
class AnthropicAdapter(BaseModelAdapter):
    """Claude 4.x models"""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # Implementation
        ...
    
    def get_name(self) -> str:
        return f"anthropic:{self.model}"

class OpenAIAdapter(BaseModelAdapter):
    """GPT-4/5 models"""
    def __init__(self, api_key: str, model: str = "gpt-5"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # Implementation
        ...

class DeepSeekAdapter(BaseModelAdapter):
    """DeepSeek V3, R1 models"""
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model

class OllamaAdapter(BaseModelAdapter):
    """Local/self-hosted models via Ollama"""
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model

class HuggingFaceAdapter(BaseModelAdapter):
    """HuggingFace Inference API"""
    def __init__(self, api_key: str, model: str = "meta-llama/Llama-3-70b"):
        self.client = InferenceClient(api_key=api_key)
        self.model = model

class TogetherAIAdapter(BaseModelAdapter):
    """Together AI (Llama, Mistral, Qwen, etc.)"""
    def __init__(self, api_key: str, model: str = "meta-llama/Llama-3-70b-Instruct"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.together.ai/v1")
        self.model = model

# Factory for creating adapters
class ModelFactory:
    _adapters = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "deepseek": DeepSeekAdapter,
        "ollama": OllamaAdapter,
        "huggingface": HuggingFaceAdapter,
        "together": TogetherAIAdapter,
    }
    
    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseModelAdapter:
        adapter_class = cls._adapters.get(provider.lower())
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._adapters.keys())}")
        return adapter_class(**kwargs)
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        """Register new adapter"""
        cls._adapters[name.lower()] = adapter_class
```

**Supported Providers:**

| Provider | Models | Deployment | Cost | Notes |
|----------|--------|------------|------|-------|
| anthropic | Claude 4.x | Cloud | $$ | Primary recommendation |
| openai | GPT-4/5 | Cloud | $$ | Well-tested |
| deepseek | V3, R1 | Cloud | $ | Budget option |
| ollama | Llama, Mistral | Local | Free | Self-hosted |
| huggingface | Llama, Qwen, Mistral | Cloud/Local | $ | Many models |
| together | Llama, Mistral, Qwen | Cloud | $ | Competitive pricing |
| vertex | Gemini | Google Cloud | $$ | Enterprise |
| azure | OpenAI | Azure | $$ | Enterprise |

**Config Usage:**

```yaml
ai:
  provider: "anthropic"  # or any registered provider
  model: "claude-sonnet-4-20250514"
  # Provider-specific settings
  api_key_env: "ANTHROPIC_API_KEY"
```

**Adding New Models:**

1. Create adapter class inheriting from `BaseModelAdapter`
2. Implement `generate()` and `get_name()` methods
3. Register: `ModelFactory.register("provider_name", MyAdapter)`
4. Add to config: `provider: "provider_name"`

No code changes needed to the core generator!

- **Purpose:** Generate structured markdown content from discovered items
- **Technology:** Python 3.11+, OpenAI SDK / Anthropic SDK
- **Dependencies:** AI API (OpenAI/Anthropic), Content templates
- **Interfaces:**
  - Input: Discovered content item
  - Output: Markdown file with YAML frontmatter

#### GitHub PR Workflow

- **Purpose:** Human review before content publication
- **Technology:** GitHub API, GitHub Actions
- **Dependencies:** GitHub repository, reviewers
- **Interfaces:**
  - Input: Generated content (via branch push)
  - Output: Merged or closed PR

#### Static Site Generator

- **Purpose:** Render content as navigable website
- **Technology:** Docusaurus 3.x or Astro
- **Dependencies:** Node.js 18+, content files
- **Interfaces:**
  - Input: Markdown content files
  - Output: Static HTML/CSS/JS

### 2.5 Agent Implementation Specification

#### Module Structure

```python
knowledge_base_agent/
├── __init__.py
├── agent.py              # Main orchestrator
├── discovery/
│   ├── __init__.py
│   ├── base.py          # Abstract discoverer
│   ├── github.py        # GitHub API integration
│   ├── arxiv.py         # arXiv API integration
│   └── hackernews.py    # HN API integration (V1.1)
├── generation/
│   ├── __init__.py
│   ├── generator.py     # Content generation logic
│   ├── prompts.py       # AI prompt templates
│   └── validator.py     # Content quality validation
├── github_ops/
│   ├── __init__.py
│   ├── pr_manager.py    # PR creation and management
│   └── content_ops.py   # Git file operations
├── utils/
│   ├── __init__.py
│   ├── deduplication.py # Hash-based deduplication
│   ├── rate_limiter.py  # Rate limiting utilities
│   └── logger.py        # Structured logging
└── config.py            # Configuration management
```

#### Agent State Management

**State Storage:**
- **File:** `.agent-state/state.json` (stored in repo, not in content)
- **Structure:**
  ```json
  {
    "last_run": "2026-02-28T10:00:00Z",
    "sources": {
      "github_ai_releases": {
        "last_processed_id": "release-12345",
        "last_processed_date": "2026-02-27T15:30:00Z"
      },
      "arxiv_cs_ai": {
        "last_processed_id": "2602.12345",
        "last_processed_date": "2026-02-28T08:00:00Z"
      }
    },
    "processed_hashes": "deduplication_hashes.json"
  }
  ```

#### Retry Logic

**Generation Failures:**
```python
class RetryConfig:
    max_retries: int = 3
    backoff_strategy: str = "exponential"  # 1s, 2s, 4s, 8s
    retry_on_errors: List[str] = [
        "rate_limit",
        "timeout",
        "service_unavailable"
    ]
    skip_on_errors: List[str] = [
        "invalid_content",
        "duplicate_detected"
    ]
```

**Partial Failure Handling:**
- Continue processing remaining items if one fails
- Log failed items to `.agent-state/failed_items.json`
- Summary report at end: X succeeded, Y failed, Z skipped

#### Concurrency Model

**MVP (Phase 1-2):** Sequential processing
- Process sources one at a time
- Simpler, easier to debug
- Sufficient for weekly runs with <50 items/run

**V1.1 (Phase 3+):** Parallel processing
- Use `asyncio` for concurrent API calls
- Process up to 5 items in parallel
- Shared rate limiter across workers

#### Agent Configuration Schema

**File:** `scripts/config.yaml`

```yaml
# Agent Configuration
agent:
  name: "knowledge-base-agent"
  version: "1.0.0"
  log_level: "INFO"

# Discovery Sources
sources:
  - id: "github_ai_releases"
    type: "github"
    enabled: true
    query:
      repos:
        - "openai/openai-python"
        - "anthropic/anthropic-sdk-python"
        - "huggingface/transformers"
      event_types: ["release", "tag"]
    keywords: ["AI", "machine learning", "LLM", "transformer"]
    domain: "ai"
    level: "intermediate"
    schedule: "weekly"

  - id: "arxiv_cs_ai"
    type: "arxiv"
    enabled: true
    query:
      categories: ["cs.AI", "cs.LG", "cs.CL"]
      max_results: 10
      sort_by: "submittedDate"
      sort_order: "descending"
    keywords: ["transformer", "attention mechanism", "neural network"]
    domain: "ai"
    level: "master"
    schedule: "weekly"

  - id: "youtube_ai"
    type: "youtube"
    enabled: false  # Enable for V1.1
    query:
      channels: []
      playlists: []
      max_results: 10
    keywords: ["machine learning", "deep learning", "tutorial"]
    domain: "ai"
    level: "beginner"
    schedule: "weekly"

  - id: "podcasts_ai"
    type: "podcast"
    enabled: false  # Enable for V1.1
    query:
      feeds: []
      max_episodes: 10
    keywords: ["AI", "machine learning", "data science"]
    domain: "ai"
    level: "intermediate"
    schedule: "weekly"

# Extensibility: Add new sources by adding entries to this config
# Supported types: github, arxiv, hn, youtube, podcast, rss, twitter
    type: "arxiv"
    enabled: true
    query:
      categories: ["cs.AI", "cs.LG", "cs.CL"]
      max_results: 10
      sort_by: "submittedDate"
      sort_order: "descending"
    keywords: ["transformer", "attention mechanism", "neural network"]
    domain: "ai"
    level: "master"
    schedule: "weekly"

# AI Generation Settings
# Recommended: Claude Sonnet 4.6 for cost/quality balance
# Claude Opus 4.6 for highest quality (1M context)
# DeepSeek V3.2 for budget option ($0.26/$0.42 per 1M tokens)
ai:
  provider: "anthropic"  # or "deepseek" for budget
  model: "claude-sonnet-4-20250514"  # claude-opus-4-20250514 / deepseek-v3-2
  max_tokens: 4000  # Increased for longer content
  temperature: 0.3
  timeout: 120
  # Enable prompt caching for cost savings (90% on repeated content)
  prompt_caching: true
  rate_limit:
    requests_per_minute: 50
    tokens_per_minute: 150000
ai:
  provider: "openai"  # or "anthropic"
  model: "gpt-5.2"
  max_tokens: 2000
  temperature: 0.3
  timeout: 60
  rate_limit:
    requests_per_minute: 50
    tokens_per_minute: 150000

# GitHub Settings
github:
  owner: "your-org"
  repo: "knowledge-base"
  branch_prefix: "agent/content/"
  pr_labels: ["ai-generated", "needs-review"]
  auto_merge: false
  reviewers: ["@domain-experts"]

# Content Quality Settings
quality:
  min_sources: 2
  max_similarity: 0.7
  min_word_count: 500
  max_word_count: 2000
  required_sections: ["introduction", "conclusion"]

# Deduplication Settings
deduplication:
  hash_algorithm: "sha256"
  hash_fields: ["title", "body_preview"]  # First 500 chars
  storage: ".agent-state/deduplication_hashes.json"
```

### 2.6 Content Deduplication Implementation

#### Algorithm

1. **Normalize Content:**
   ```python
   normalized = {
       "title": content.title.lower().strip(),
       "body_preview": content.body[:500].lower().strip()
   }
   ```

2. **Generate Hash:**
   ```python
   import hashlib
   hash_input = f"{normalized['title']}||{normalized['body_preview']}"
   content_hash = hashlib.sha256(hash_input.encode()).hexdigest()
   ```

3. **Check Against Existing:**
   - Load `.agent-state/deduplication_hashes.json`
   - If hash exists: skip content generation, log as duplicate
   - If hash new: proceed with generation, add hash to storage

#### Hash Storage Format

**File:** `.agent-state/deduplication_hashes.json`

```json
{
  "hashes": {
    "a1b2c3d4e5f6...": {
      "title": "Introduction to Transformers",
      "domain": "ai",
      "level": "beginner",
      "file_path": "content/ai/beginner/articles/intro-transformers.md",
      "created_at": "2026-02-28T10:00:00Z"
    }
  },
  "last_updated": "2026-02-28T10:00:00Z",
  "total_hashes": 142
}
```

#### Hash Collision Handling

- SHA-256 collision probability is negligible (~2^-256)
- If collision suspected (same hash, different content):
  - Log warning
  - Append timestamp suffix to hash
  - Proceed with generation

### 2.7 GitHub PR Workflow Implementation

#### Branch Naming Convention

```
agent/content/{timestamp}/{domain}/{level}/{slug}
```

**Example:** `agent/content/20260228-100000/ai/beginner/transformer-intro`

#### PR Creation Process

1. **Create Branch:**
   ```python
   branch_name = f"agent/content/{timestamp}/{domain}/{level}/{slug}"
   github_client.create_ref(
       ref=f"refs/heads/{branch_name}",
       sha=main_branch_sha
   )
   ```

2. **Commit Content:**
   ```python
   file_path = f"content/{domain}/{level}/{category}/{slug}.md"
   github_client.create_or_update_file(
       path=file_path,
       message=f"Add {category}: {title}",
       content=markdown_content,
       branch=branch_name
   )
   ```

3. **Create PR:**
   ```python
   pr = github_client.create_pull_request(
       title=f"[AI Generated] {title}",
       body=pr_template.render(content_metadata),
       head=branch_name,
       base="main",
       labels=["ai-generated", "needs-review", domain],
       reviewers=config.github.reviewers
   )
   ```

#### PR Merge Strategy

**Manual Merge (MVP):**
- `auto_merge: false` in config
- Human reviewer approves PR via GitHub UI
- Human reviewer clicks "Merge" button
- Branch deleted automatically after merge

**Auto-Merge (V1.1):**
- `auto_merge: true` in config
- Enable GitHub auto-merge on PR creation
- PR merges automatically when:
  - At least 1 approval from configured reviewers
  - All CI checks pass (schema validation, link checking)
  - No requested changes pending
- Merge method: "squash" (single commit on main)

#### Conflict Resolution Strategy

1. **Conflict Detection:**
   - Agent checks if main branch has diverged before pushing
   - If conflict detected: rebase branch on latest main

2. **Automatic Resolution:**
   - Content files never conflict (unique filenames with timestamp)
   - If `.agent-state/` conflicts: use latest from main

3. **Manual Escalation:**
   - If unexpected conflicts: label PR as "needs-manual-review"
   - Comment on PR with conflict details
   - Alert repo admins via GitHub notification

### 2.8 Credibility Score Calculation

#### Scoring Algorithm

**Factors (weighted):**

```python
def calculate_credibility_score(content) -> int:
    score = 0
    
    # Source reputation (40%)
    for source in content.sources:
        if source.type == "arxiv":
            score += 4
        elif source.type == "github" and source.stars > 10000:
            score += 4
        elif source.type == "github" and source.stars > 1000:
            score += 3
        else:
            score += 2
    score = min(score / len(content.sources), 4)
    
    # Recency (30%)
    days_old = (now() - content.source_published_date).days
    if days_old < 30:
        score += 3
    elif days_old < 180:
        score += 2
    elif days_old < 365:
        score += 1
    else:
        score += 0.5
    
    # Citation count (20%)
    if content.citation_count > 100:
        score += 2
    elif content.citation_count > 10:
        score += 1.5
    elif content.citation_count > 0:
        score += 1
    
    # Content completeness (10%)
    if len(content.body) >= 1500 and has_code_examples(content):
        score += 1
    elif len(content.body) >= 1000:
        score += 0.5
    
    return min(round(score), 10)
```

**Score Interpretation:**
- 9-10: Highly authoritative (arxiv + recent + high citations)
- 7-8: Reliable (reputable source + recent)
- 5-6: Good (valid sources, older content)
- 1-4: Basic (low-reputation sources)

**Storage:** Stored in frontmatter `credibility_score` field
---

## 3. Data Architecture

### 3.1 Database Selection

- **Type:** None (Git-based)
- **Product:** Git (embedded)
- **Rationale:**
  - Git provides built-in version history
  - GitHub PRs provide review workflow
  - No additional database needed
  - Content is text (Markdown), ideal for Git storage

### 3.2 Data Models

#### Content Entity

```yaml
---
# Required frontmatter fields
title: string (required, max 200 chars)
domain: string (required, enum: ai|blockchain|protocol)
level: string (required, enum: beginner|intermediate|master)
category: string (required, enum: article|tool|resource|video|audio|podcast|youtube|arxiv|extensible)
tags: string[] (required, max 10 tags)

# Metadata fields
created: ISO-8601 date (auto-generated)
updated: ISO-8601 date (auto-updated)
sources: Source[] (required)
ai_reviewed: boolean (default: true)
human_reviewed: boolean (default: false)
status: string (enum: pending-review|approved|rejected|published)

# Optional fields
description: string (max 500 chars)
author: string (AI agent name)
reviewer: string (GitHub username)
pr_number: integer (GitHub PR number)
media_url: string (optional - video/audio content URL)
media_type: string (enum: text|video|audio, optional)

# Progression / Learning Path fields
series: string (optional - group related content, e.g., "Deep Learning 101")
sequence: integer (optional - order within series, e.g., 1, 2, 3)
prerequisites: string[] (optional - content slugs that should be read first)
next: string (optional - suggested next content slug)
learning_outcomes: string[] (optional - what reader will learn)
difficulty_score: integer (1-10, auto-calculated based on level + prerequisites)
---
```
media_url: string (optional - video/audio content URL)
media_type: string (enum: text|video|audio, optional)
---
```
---
```

#### Source Entity

```yaml
- url: string (required, valid URL)
  title: string (required)
  accessed_at: ISO-8601 date
```

#### Domain Configuration

```yaml
# domain/_meta.yaml
name: string
description: string
keywords: string[]
color: string (hex code for UI)
icon: string (emoji or icon name)
```

### 3.3 Data Flow Diagram

```
Discovery Phase
───────────────
[External Sources] → [Discovery Agent] → [Filter by Keywords] → [Discovered Items]

Generation Phase
────────────────
[Discovered Items] → [Content Generator] → [Markdown + Frontmatter] → [New Branch]

Review Phase
────────────
[New Branch] → [Create PR] → [Human Review] → [Approved/Rejected]

Publish Phase
────────────
[Approved PR] → [Merge to Main] → [CI/CD Trigger] → [Deploy to Pages]
```

### 3.4 Content Structure

```
knowledge-base/
├── .github/
│   └── workflows/
│       ├── content-agent.yml    # Main agent workflow
│       └── deploy.yml           # Deploy workflow
├── content/
│   ├── _meta.yaml               # Site configuration
│   ├── ai/
│   │   ├── _meta.yaml           # Domain config
│   │   ├── beginner/
│   │   │   ├── articles/
│   │   │   ├── tools/
│   │   │   ├── resources/
│   │   │   └── videos/
│   │   ├── intermediate/
│   │   │   ├── articles/
│   │   │   ├── tools/
│   │   │   ├── resources/
│   │   │   └── videos/
│   │   └── master/
│   │       ├── articles/
│   │       ├── tools/
│   │       ├── resources/
│   │       └── videos/
│   ├── blockchain/
│   │   └── ... (same structure)
│   └── protocol/
│       └── ... (same structure)
├── scripts/
│   ├── discover.py              # Discovery agent
│   ├── generate.py              # Content generator
│   └── config.yaml              # Agent configuration
├── docusaurus.config.js         # Site configuration
├── package.json
└── README.md
```

---

## 4. API Specification

### 4.1 API Style

**Not Applicable**

This is a static site with no backend API. All interactions occur through:
- GitHub API (for content management)
- GitHub Actions (for automation)

### 4.2 External APIs Consumed

| Service | Purpose | Auth Method |
|---------|---------|-------------|
| GitHub REST API | Repository operations, PRs | GitHub Token (PAT or App) |
| GitHub GraphQL API | Advanced queries | GitHub Token |
| arXiv API | Paper discovery | None (public) |
| Hacker News API | Trending content | None (public) |
| OpenAI API | Content generation | API Key |
| Anthropic API | Content generation | API Key |

### 4.3 API Rate Limits & Handling

| API | Limit | Strategy |
|-----|-------|----------|
| GitHub REST | 5000/hr (authenticated) | Exponential backoff, queue requests |
| arXiv | None documented | Respect 1 req/sec |
| Hacker News | 300/sec (implied) | Rate limit to 10/sec |
| OpenAI | Varies by tier | Budget capping, caching |

---

## 5. Infrastructure & Deployment

### 5.1 Environment Overview

| Environment | Purpose | URL |
|------------|---------|-----|
| Development | Local testing | localhost |
| Production | Live system | [username].github.io/knowledge-base |

### 5.2 Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │  External   │     │   GitHub    │     │   GitHub    │      │
│   │   Cron      │────▶│   Actions   │────▶│   Pages     │      │
│   │  Service    │     │             │     │             │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│         │                   │                   │                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │  Vercel     │     │  Agent &    │     │  Static     │      │
│   │  Cron       │     │  CI/CD      │     │  Site       │      │
│   │  (free)     │     │  (free)     │     │  (free)     │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Deployment Strategy

- **Method:** Git-based (commit triggers deployment)
- **CI/CD:** GitHub Actions
- **Rollback:** Git revert + force push to main

**GitHub Actions Workflow:**

```yaml
name: Deploy
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Build
        run: npm run build
        
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

### 5.4 Scheduling Strategy

**Problem:** GitHub Actions has a 60-day limit for scheduled workflows.

**Solution:** External cron service triggers the workflow via `repository_dispatch` event.

```yaml
# Triggered by external cron
on:
  repository_dispatch:
    types: [scheduled-run]
```

**External Cron Configuration:**
- Service: Vercel Cron (free tier) or EasyCron
- Frequency: Weekly (configurable)
- Endpoint: GitHub API `POST /repos/{owner}/{repo}/dispatches`

---

## 6. Security Architecture

### 6.1 Authentication

- **GitHub Token:** GitHub App (preferred) over Personal Access Token
  - **Scopes Required:** `contents:write`, `pull_requests:write`, `workflows:write`
  - **Storage:** GitHub Secrets (`GITHUB_TOKEN`, `GH_APP_PRIVATE_KEY`)
  - **GitHub App Benefits:**
    - Granular permissions (repo-level only)
    - Automatic token rotation by GitHub
    - Audit logging per app installation
    - Revocable without affecting user account
- **AI API Keys:** Stored as encrypted repository secrets
- **Token Scope:** Minimal permissions required

### 6.1.1 Secret Rotation Strategy

**Rotation Policy:**
- **GitHub App:** Tokens auto-rotate (GitHub managed), no action needed
- **AI API Keys:** Rotate every 90 days or on suspected compromise
- **External Cron Webhook Secret:** Rotate every 180 days

**Rotation Procedure:**

1. **Generate new secret** in provider dashboard
2. **Add new secret** to GitHub Secrets with `_NEW` suffix
3. **Update workflow** to use `_NEW` secret
4. **Test workflow** with new secret
5. **Remove old secret** from GitHub Secrets
6. **Delete old secret** from provider

**Compromised Credentials Response:**

1. **Immediate Actions (< 5 minutes):**
   - Revoke compromised secret in provider
   - Generate new secret
   - Update GitHub Secrets
   - Force re-run failed workflows

2. **Investigation (< 1 hour):**
   - Review GitHub Actions logs for unauthorized usage
   - Check API usage in provider dashboards
   - Identify scope of potential data access

3. **Remediation:**
   - If content compromised: revert PRs and force-push clean history
   - Document incident in security log
   - Update detection mechanisms

### 6.1.2 Secret Audit Logging

**GitHub Actions Audit:**
- All secret usage logged in workflow runs
- Secrets masked in logs (GitHub automatic)
- Retention: 90 days (GitHub default)

**External Access:**
- AI API: Monitor usage via provider dashboards (OpenAI, Anthropic)
- GitHub API: Monitor rate limit headers and remaining quota

### 6.2.1 Input Validation & Sanitization

**External API Response Validation:**

```python
# GitHub API Response Schema
GitHubReleaseSchema = {
    "type": "object",
    "required": ["tag_name", "name", "html_url", "published_at"],
    "properties": {
        "tag_name": {"type": "string", "maxLength": 100},
        "name": {"type": "string", "maxLength": 200},
        "html_url": {"type": "string", "format": "uri"},
        "body": {"type": "string", "maxLength": 50000}
    }
}

# Validate before processing
import jsonschema
jsonschema.validate(instance=api_response, schema=GitHubReleaseSchema)
```

**Content Sanitization:**

```python
import bleach

# Sanitize markdown content
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'code', 'pre', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title'], 'code': ['class']}

def sanitize_content(markdown: str) -> str:
    # Remove script tags, event handlers
    clean = bleach.clean(markdown, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    # Validate all URLs are HTTPS
    clean = validate_urls(clean)
    return clean
```

**GitHub Issue Input Validation:**

- When agent reads user feedback from GitHub Issues:
  - Limit comment length to 5000 chars
  - Strip HTML/JavaScript
  - Validate URLs before following
  - Rate limit: max 10 issues processed per run
### 6.2 Authorization

- **Model:** GitHub-native (repository permissions)
- **Roles:**
  - Admin: Full control, settings
  - Maintain: Merge PRs, manage branches
  - Write: Push to feature branches
  - Read: Clone and browse

### 6.3 Data Protection

- **Encryption at Rest:** GitHub handles (encrypted at rest)
- **Encryption in Transit:** TLS 1.2+ (GitHub enforced)
- **PII Handling:** None collected
- **Secrets:** GitHub Secrets, never in code

### 6.4 Security Headers

Since this is a static site hosted on GitHub Pages, standard security headers are applied via `_headers` file or CDN configuration:

```
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
```
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'
  Permissions-Policy: geolocation=(), microphone=(), camera=()

### 6.5 Comprehensive Threat Model

| Threat | Likelihood | Impact | Mitigation | Residual Risk |
|--------|------------|--------|------------|---------------|
| Malicious content injection | Medium | High | Human review gate, content sanitization, input validation | Low |
| API key exposure in logs | Low | Critical | GitHub automatic secret masking, audit logging | Low |
| Supply chain attack (compromised dependency) | Medium | High | Dependabot alerts, pinned versions, CI security scans | Medium |
| Rate limit DoS | Medium | Medium | Exponential backoff, rate limiter, budget caps | Low |
| Content duplication spam | Medium | Low | SHA-256 hash deduplication, similarity checks | Very Low |
| Outdated/stale content | High | Medium | Frontmatter age tracking, automated staleness alerts | Low |

### 6.6 Security Testing Plan

**Automated Security Scanning:**

```yaml
# .github/workflows/security.yml
name: Security Scanning
on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Dependabot
        uses: github/dependabot-action@v2
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit (Python SAST)
        run: |
          pip install bandit
          bandit -r scripts/ -f json -o bandit-report.json
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run GitLeaks
        uses: gitleaks/gitleaks-action@v2

  content-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate Markdown Links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
      - name: Check for secrets in content
        run: |
          ! grep -r "api[_-]key\|secret\|password" content/
```

**Manual Security Review Requirements:**

- All PRs touching `scripts/` require security review
- GitHub Actions workflow changes require admin approval
- New dependency additions require security assessment

**Quarterly Security Audit:**

- Review GitHub audit logs for anomalies
- Verify secret rotation compliance
- Test incident response procedures
- Update threat model based on new attack vectors
| Malicious PR modification | Low | High | Branch protection rules, required reviews, CI validation | Very Low |
| GitHub token theft | Low | Critical | GitHub App with minimal scopes, rotation policy, audit logs | Low |
| AI hallucination/misinformation | High | High | Multi-source requirement (min 2), credibility scoring, human review | Medium |
| Repository hijacking | Very Low | Critical | 2FA required for admins, branch protection, audit logs | Very Low |
| External cron service compromise | Low | Medium | Webhook secret validation, IP allowlisting, monitoring | Low |
| Data exfiltration via API | Low | Low | No PII collected, all content public MIT licensed | Very Low |
---

## 7. Integration Architecture

### 7.1 External Integrations

| Service | Purpose | Auth Method | Rate Limits |
|---------|---------|-------------|------------|
| GitHub API | Content storage, PRs, Actions | Token | 5000/hr |
| arXiv API | Paper discovery | None | 1/sec |
| Hacker News API | Trending topics | None | 10/sec |
| OpenAI API | Content generation | API Key | Tier-based |
| Anthropic API | Content generation | API Key | Tier-based |

### 7.2 Integration Details

#### GitHub API

- **Documentation:** https://docs.github.com/en/rest
- **Endpoints Used:**
  - `POST /repos/{owner}/{repo}/pulls` - Create PR
  - `POST /repos/{owner}/{repo}/pulls/{pull_number}/merge` - Merge PR
  - `GET /repos/{owner}/{repo}/contents/{path}` - Read content
  - `PUT /repos/{owner}/{repo}/contents/{path}` - Write content
- **Rate Limits:** 5000 requests/hour (authenticated)
- **Rate Limit Monitoring:**
  ```python
  # Check response headers
  remaining = int(response.headers['X-RateLimit-Remaining'])
  reset_time = int(response.headers['X-RateLimit-Reset'])
  
  if remaining < 100:
      logger.warning(f"GitHub API rate limit low: {remaining} remaining")
      wait_until = datetime.fromtimestamp(reset_time)
      time.sleep((wait_until - datetime.now()).total_seconds())
  ```
- **Error Handling by Status Code:**
  - `200-299`: Success
  - `401`: Invalid token → Alert admins, abort
  - `403`: Rate limit → Wait until reset, resume
  - `404`: Not found → Log warning, skip
  - `422`: Validation error → Log details, skip
  - `500-599`: Server error → Exponential backoff (1s, 2s, 4s), max 3 retries
- **Circuit Breaker:** After 5 consecutive failures, pause for 5 minutes
- **Partial Failure:** Continue processing remaining items

#### arXiv API

- **Documentation:** https://arxiv.org/help/api
- **Endpoints Used:** `http://export.arxiv.org/api/query`
- **Rate Limits:** 1 request/second
- **Implementation:** Sleep 1 second between requests
- **Error Handling:**
  - Timeout (10s): Skip paper
  - HTTP 4xx/5xx: Retry once, then skip
  - Malformed XML: Log error, skip

---

## 8. Performance & Scalability

### 8.1 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load Time | < 2s | Lighthouse |
| Build Time | < 5 min | GitHub Actions |
| Time to First Byte | < 500ms | CDN |
| GitHub API Calls | < 100/run | Agent logging |

### 8.2 Scalability Strategy

- **Horizontal Scaling:** N/A (static site)
- **Caching:** CDN (GitHub Pages built-in)
- **Content Volume:** Git handles millions of files efficiently

### 8.3 Caching Strategy

- **Static Assets:** GitHub Pages CDN (automatic)
- **API Responses:** Cache discovery results for 1 hour
- **AI Generation:** Cache by content hash to avoid duplicates

---

## 9. Reliability & Operations

### 9.1 Availability Target

- **SLA:** 99.9% (GitHub Pages SLA)
- **RTO:** N/A (static content)
- **RPO:** N/A (Git is source of truth)

### 9.2 Monitoring

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| Deployment failures | GitHub Actions | Any failure |
| API rate limits | Agent logs | < 100 remaining |
| Content age | Frontmatter analysis | > 30 days |

### 9.3 Logging

- **Format:** JSON (structured)
- **Retention:** 90 days (GitHub Actions logs)
- **Aggregation:** GitHub Actions UI

### 9.4 Alerting

| Condition | Severity | Action |
|-----------|----------|--------|
| Workflow failure | Critical | GitHub notification to repo admins |
| API rate limit hit | Warning | Log and pause |
| No content generated | Info | Summary report |

### 9.5 Disaster Recovery

- **Content Recovery:** Git history + branch recovery
- **Site Recovery:** Re-run deploy workflow
- **Agent Recovery:** Re-run workflow from last successful point

---

## 10. Development Standards

### 10.1 Code Standards

- **Language:** Python 3.11+
- **Linting:** Ruff (Python)
- **Testing:** pytest
- **Coverage Target:** 80%
- **Node.js:** 18+ (for static site)

### 10.2 Git Workflow

- **Branching:** Trunk-based (main + feature branches)
- **Commit Format:** Conventional Commits
- **PR Requirements:** At least 1 reviewer approval

### 10.3 Documentation Standards

- **Code Comments:** Docstrings for all public functions
- **README:** Required sections: Overview, Setup, Usage, Contributing
- **Scripts:** --help flag and -v/--verbose options

---

## 11. Implementation Roadmap

### 11.1 Phase Overview

| Phase | Features | Duration |
|-------|----------|----------|
| 1 - Foundation | Repo setup, CI/CD, basic site | 1 week |
| 2 - Core Agent | Discovery, generation, PR workflow | 2 weeks |
| 3 - Polish | UI improvements, testing, documentation | 1 week |

### 11.2 Phase Details

#### Phase 1: Foundation

**Goal:** Establish infrastructure and basic site

**Work Items:**
- [ ] Initialize GitHub repository
- [ ] Configure GitHub Pages
- [ ] Set up CI/CD workflows
- [ ] Deploy basic static site
- [ ] Define content directory structure

**Dependencies:** None (blocking)

---

#### Phase 2: Core Agent

**Goal:** Implement AI discovery and generation

**Work Items:**
- [ ] Create discovery agent (GitHub, arXiv)
- [ ] Implement content generator
- [ ] Build GitHub PR automation
- [ ] Add external cron trigger
- [ ] Implement deduplication

**Dependencies:** Phase 1 complete

---

#### Phase 3: Polish

**Goal:** Testing, documentation, refinements

**Work Items:**
- [ ] Add unit and integration tests
- [ ] Performance optimization
- [ ] Documentation (README, CONTRIBUTING)
- [ ] Error handling improvements
- [ ] User feedback integration

**Dependencies:** Phase 2 complete

---

## 12. Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| GitOps | Infrastructure management using Git |
| Frontmatter | YAML metadata at file start |
| Static Site | Pre-rendered HTML, no server |
| CI/CD | Continuous Integration/Deployment |
| Cron | Time-based job scheduler |
| Deduplication | Preventing duplicate content |

### B. Reference Documents

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [arXiv API Documentation](https://arxiv.org/help/api)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Docusaurus Documentation](https://docusaurus.io/docs)

### C. Open Questions

- [ ] Which AI model (OpenAI vs Anthropic) performs better for this use case?
- [ ] What is optimal polling frequency to balance freshness vs. API costs?
- [ ] How to handle conflicting updates to the same topic?

### D. Decision Log

| Date | Decision | Rationale | Decided By |
|------|----------|-----------|------------|
| 2026-02-28 | Use GitHub Pages for hosting | Free, integrated, no hosting costs | Architecture Team |
| 2026-02-28 | Use Python for AI agent | Rich ecosystem for AI/ML tasks | Architecture Team |
| 2026-02-28 | Use external cron service | Avoid GitHub Actions 60-day limit | Architecture Team |
| 2026-02-28 | No database (Git is database) | Simplifies architecture, built-in version control | Architecture Team |
