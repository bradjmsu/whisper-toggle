# Contributing to Whisper Toggle

Thank you for your interest in contributing to Whisper Toggle! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests locally
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/whisper-toggle.git
cd whisper-toggle

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks (optional)
pre-commit install
```

### Code Style

- Follow PEP 8
- Use Black for formatting (`black whisper_toggle/`)
- Run flake8 for linting (`flake8 whisper_toggle/`)
- Add type hints where possible
- Keep line length under 88 characters

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=whisper_toggle

# Run specific test
pytest tests/test_specific.py::test_function
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions and classes
- Update CHANGELOG.md for notable changes
- Include examples where helpful

## Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated for new functionality
- [ ] Documentation updated
- [ ] All tests pass locally
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the changes

## Areas to Contribute

- **Bug fixes**: Check the issue tracker
- **Feature requests**: Discuss in issues first
- **Documentation**: Improve clarity, add examples
- **Tests**: Increase coverage, add edge cases
- **Performance**: Optimize audio processing or transcription
- **Platform support**: Extend beyond Linux/GNOME

## Questions?

Feel free to open an issue for discussion or clarification.

Thank you for contributing! 🎤