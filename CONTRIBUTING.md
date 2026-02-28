# Contributing to Knowledge Base

Thank you for your interest in contributing! This document provides guidelines for contributing to the Knowledge Base system.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/your-org/knowledge-base/issues)
2. Create a new issue with:
   - Clear title
   - Detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)

### Suggesting Features

1. Check existing feature requests
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Proposed implementation (if any)

### Submitting Code

1. **Fork the repository**

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ruff check scripts/
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test changes
   - `refactor:` - Code refactoring

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request:**
   - Provide a clear description
   - Link related issues
   - Ensure all checks pass

## Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **Set up pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Run tests:**
   ```bash
   pytest tests/ -v --cov=scripts
   ```

## Code Style

- Python: Follow PEP 8, use Ruff for linting
- JavaScript/TypeScript: Follow Prettier defaults
- Docstrings: Google style for Python
- Comments: Explain "why", not "what"

## Testing Guidelines

- Write tests for all new features
- Maintain >80% code coverage
- Use descriptive test names
- Include both positive and negative test cases

## Documentation

- Update README.md for user-facing changes
- Update technical_spec.md for architecture changes
- Add docstrings to all public functions
- Include examples in documentation

## Pull Request Process

1. **Review Checklist:**
   - [ ] Tests pass
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Commits are clean and descriptive

2. **Review Process:**
   - Maintainer will review within 3-5 days
   - Address feedback and update PR
   - Once approved, maintainer will merge

## Questions?

Feel free to open an issue for any questions or clarifications.
