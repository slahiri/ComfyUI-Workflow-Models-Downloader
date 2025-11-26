# Contributing to ComfyUI Workflow Models Downloader

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix

```bash
git checkout -b feature/your-feature-name
```

## Development Setup

1. Install ComfyUI
2. Clone this repo into `ComfyUI/custom_nodes/`
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Restart ComfyUI

## Making Changes

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line under 72 characters

Examples:
```
Add support for CivitAI model detection
Fix download progress not updating
Update README with new features
```

## Submitting Changes

1. Push your changes to your fork
2. Create a Pull Request against the `main` branch
3. Fill out the PR template completely
4. Wait for review

### Pull Request Guidelines
- One feature/fix per PR
- Include a clear description of changes
- Add screenshots for UI changes
- Test your changes thoroughly

## Reporting Issues

- Check existing issues before creating a new one
- Use issue templates when available
- Include steps to reproduce bugs
- Include ComfyUI version and OS information

## Adding New Model Sources

To add support for new model sources:
1. Add detection logic in `server.py`
2. Update `metadata/popular-models.json` if adding popular models
3. Test with various workflows
4. Update README if needed

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

Open an issue with the "question" label.

Thank you for contributing!
