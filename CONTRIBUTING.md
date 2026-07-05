# Contributing — sonar-vision

> *Thank you for contributing to sonar-vision.*

## How to Contribute

### 1. Set Up Your Environment

```bash
git clone https://github.com/purplepincher/sonar-vision.git
cd sonar-vision
pip install -e ".[dev]"
```

### 2. Run the Tests

```bash
pytest tests/
```

### 3. Find Something to Work On

- Check the [issues page](https://github.com/purplepincher/sonar-vision/issues)
- Look for `good first issue` labels
- Read the `ARCHITECTURE.md` and `GETTING_STARTED.md` for context

### 4. Code Standards

- **Test coverage** — every public function needs at least one test
- **Documentation** — all public items must have doc comments
- **Error handling** — raise clear, specific exceptions for fallible operations

### 5. Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) spec:

```
feat: add configurable absorption model
fix: handle zero-distance edge case in ping()
docs: update architecture overview for v0.3
test: add roundtrip tests for grid serialization
```

### 6. Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass: `pytest tests/`
5. Submit a PR with a clear description of the change

### 7. Review Process

- All PRs need at least one approval from a maintainer
- Changes to public API require careful review
- Breaking changes must be discussed in an issue first

## Code of Conduct

Be respectful. We're building something useful together. Assume good intent.

## License

By contributing, you agree that your contributions will be licensed under MIT.
