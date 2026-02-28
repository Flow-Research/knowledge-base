# Knowledge Base System - Brainstorm

> **Date**: 2026-02-27
> **Status**: Initial Design

---

## Problem Statement

We need a system that maintains a database of different technology domains (AI, Blockchain, Protocol Engineering) where:
- Content is kept up to date by AI agents
- Agent-generated content is reviewed by humans before being saved
- Content is easy for users and AI agents to navigate

---

## Design Decisions

### 1. Storage & Hosting

| Decision | Choice |
|----------|--------|
| Content Storage | Git repository (versioned, reviewable) |
| Hosting | CI/CD deploys to GitHub Pages or custom host |
| Workflow | GitHub PR for human review |

**Rationale**: Git provides built-in version history, branching, and PR-based review workflow. CI can automatically build and deploy content on merge.

### 2. Learning Levels

| Level | Description |
|-------|-------------|
| Beginner | Foundational concepts, gentle introductions, step-by-step guides |
| Intermediate | Practical applications, building projects, deeper technical details |
| Master | Cutting-edge research, advanced patterns, architectural decisions |

**Rationale**: Different learners have different needs. AI agents can tailor content depth based on the target level. Users can filter content by their expertise level.

### 3. Technology Domains

**Initial Domains:**
- Artificial Intelligence
- Blockchain
- Protocol Engineering

**Expansion**: System supports adding new domains dynamically over time.

### 4. Update Trigger

| Decision | Choice |
|----------|--------|
| Mechanism | Scheduled polling |
| Schedule | Configurable (daily/weekly) |

**Rationale**: Predictable update cadence. Agent polls sources on schedule to discover new content.

### 5. Human Review

| Decision | Choice |
|----------|--------|
| Interface | GitHub PR |
| Workflow | Agent creates PR → Human reviews/comments → Merge or request changes |

**Rationale**: Familiar interface, built-in commenting, easy to track changes.

### 6. Content Types

All of the following:
- Articles / Tutorials
- Tool Reviews
- Resource Links
- Videos
- API/SDK Documentation

### 7. Content Format

- **Markdown** with YAML frontmatter
- Structured metadata for AI parsing
- Hierarchical organization by domain → level → category → topic

- **Markdown** with YAML frontmatter
- Structured metadata for AI parsing
- Hierarchical organization by domain → category → topic

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Base System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │     AI       │    │   Content    │    │    Human     │      │
│  │   Agent      │───▶│   Pipeline   │───▶│   Review     │      │
│  │ (Scheduler)  │    │              │    │   (GitHub)   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                       │                │
│         ▼                                       ▼                │
│  ┌──────────────┐                       ┌──────────────┐        │
│  │  Discovery   │                       │     PR       │        │
│  │  Sources:    │                       │   Workflow   │        │
│  │  - GitHub    │                       └──────┬───────┘        │
│  │  - Arxiv     │                              │                │
│  │  - HN        │                              ▼                │
│  │  - Twitter   │              ┌──────────────────────────┐   │
│  └──────────────┘              │   Git Repository         │   │
│                                │   (Storage + History)     │   │
│                                └────────────┬─────────────┘   │
│                                             │                  │
│                                             ▼                  │
│                                ┌──────────────────────────┐    │
│                                │   CI/CD (GitHub Actions) │   │
│                                │   Build → Deploy         │    │
│                                └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Content Structure

```
technology-domains/
├── ai/
│   ├── _meta.yaml           # Domain config
│   ├── beginner/
│   │   ├── articles/
│   │   ├── tools/
│   │   ├── resources/
│   │   └── videos/
│   ├── intermediate/
│   │   ├── articles/
│   │   ├── tools/
│   │   ├── resources/
│   │   └── videos/
│   ├── master/
│   │   ├── articles/
│   │   ├── tools/
│   │   ├── resources/
│   │   └── videos/
│   └── index.md             # Domain overview
├── blockchain/
│   └── ...
└── protocol/
    └── ...
```

```yaml
---
title: "Understanding Transformers"
domain: ai
level: beginner|intermediate|master
category: articles
tags: [nlp, deep-learning, architecture]
created: 2026-02-27
updated: 2026-02-27
sources:
  - url: "https://arxiv.org/..."
    title: "Attention Is All You Need"
ai_reviewed: true
human_reviewed: false
status: pending-review
---
```

```yaml
---
title: "Understanding Transformers"
domain: ai
category: articles
tags: [nlp, deep-learning, architecture]
created: 2026-02-27
updated: 2026-02-27
sources:
  - url: "https://arxiv.org/..."
    title: "Attention Is All You Need"
ai_reviewed: true
human_reviewed: false
status: pending-review
---


---

## Agent Workflow

1. **Schedule Trigger** → Agent wakes up on configured schedule
2. **Discover** → Poll configured sources (GitHub, arxiv, HN, etc.)
3. **Filter** → Match content against domain keywords/interests
4. **Generate** → Create markdown content with frontmatter
5. **Create PR** → Push branch + open PR with AI-generated content
6. **Notify** → Alert human reviewers (optional: GitHub notification)
7. **Human Review** → Reviewer comments/approves/requests changes
8. **Merge** → Approved content merges to main
9. **Deploy** → CI automatically builds and deploys

---

## Open Questions

- [ ] What specific sources should the agent poll initially?
- [ ] How to handle conflicting updates to the same topic?
- [ ] Should there be a staging/preview environment?
- [ ] How to handle content deletion (outdated topics)?
- [ ] What AI model should generate content?
- [ ] How to prevent spam/low-quality contributions?

---

## Next Steps

1. Create project specification (technical_spec.md)
2. Define content schema in detail
5. Create first domain template




