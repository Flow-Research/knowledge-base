# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-28

### Added
- Initial implementation of Knowledge Base System
- Model adapter pattern supporting Anthropic, OpenAI, DeepSeek, and Ollama
- Discovery agents for GitHub and arXiv
- Content generator with YAML frontmatter support
- Deduplication system using SHA-256 hashing
- GitHub PR workflow automation
- Configuration system with YAML
- Main orchestrator (agent.py)
- GitHub Actions workflows for content discovery and deployment
- Docusaurus static site generator
- Comprehensive unit tests
- README and documentation

### Features
- Extensible LLM support with factory pattern
- Multiple discovery sources with plugin architecture
- Automated PR workflow with human review
- Content credibility scoring (1-10)
- Rate limiting and structured logging
- CI/CD integration via GitHub Actions

[0.1.0]: https://github.com/your-org/knowledge-base/releases/tag/v0.1.0
