# Contributing to Lunaris Civitas 🌙

Thank you for your interest in contributing to Lunaris Civitas! We welcome contributions from everyone, whether you're fixing bugs, adding features, improving documentation, or just asking questions.

## 🤝 How to Contribute

### Reporting Issues

Found a bug? Have a feature request? Please open an issue on GitHub! When reporting:

- **Be clear and descriptive** - Help us understand what's happening
- **Include steps to reproduce** - If it's a bug, tell us how to reproduce it
- **Check existing issues** - Someone might have already reported it
- **Be patient** - We're a small project, but we'll get to it!

### Suggesting Features

Have an idea for a new feature? We'd love to hear it! Please:

- Check the [Roadmap](docs/public/Roadmap/PHASES.md) first - it might already be planned
- Open an issue with the `enhancement` label
- Explain the use case and why it would be valuable
- Consider how it fits with our design principles

### Contributing Code

1. **Fork the repository** and clone your fork
2. **Create a branch** for your changes (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following our guidelines below
4. **Test your changes** (`make test`)
5. **Update documentation** if needed
6. **Commit your changes** with clear, descriptive messages
7. **Push to your fork** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request** with a clear description of what you changed and why

## 📋 Development Guidelines

### Design Principles

When contributing, please follow our core design principles:

1. **No system talks directly to another system** - All interaction via world state
2. **Everything is config + stats** - Data-driven behavior
3. **Humans never "decide"** - Systems decide probabilistically
4. **Every feature must be disable-able** - Modular and optional
5. **If it can't be graphed, it's not real** - Analytics-first design
6. **Complexity is allowed only when isolated** - Systems are independent

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write clear, descriptive variable and function names
- Add docstrings to classes and functions
- Keep functions focused and small

### Testing

- Write tests for new features
- Ensure existing tests still pass (`make test`)
- Test edge cases and error conditions
- Maintain determinism - same seed should produce same results

### Documentation

- Update relevant documentation when adding features
- Add examples to docstrings
- Update the README if adding major features
- Keep the roadmap updated if adding new phases

### System Development

When adding a new system:

1. **Follow the System contract** - See [Systems documentation](docs/public/Systems/README.md)
2. **Make it configurable** - All behavior should be driven by config
3. **Make it disable-able** - Systems should be optional
4. **Add to the appropriate phase** - Follow the [Roadmap](docs/public/Roadmap/PHASES.md)
5. **Update system documentation** - Add to Systems README

See [Adding Systems](docs/public/Systems/ADDING_SYSTEMS.md) for detailed instructions.

### Commit Messages

Write clear, descriptive commit messages:

```
Good: "Add JobSystem for resource production through human jobs"
Bad: "fix stuff"
```

Use present tense ("Add feature" not "Added feature") and be specific about what changed.

## 🧪 Testing

Before submitting a PR:

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/path/to/test_file.py

# Run with verbose output
python -m pytest -v
```

## 📝 Pull Request Process

1. **Update documentation** - If you're adding features, update the docs
2. **Add tests** - New features should have tests
3. **Ensure tests pass** - All tests must pass before merging
4. **Update CHANGELOG** - If we have one, add your changes
5. **Be responsive** - Respond to feedback and questions

### PR Description Template

When opening a PR, please include:

- **What changed** - Brief description
- **Why** - Motivation and use case
- **How to test** - Steps to verify the changes
- **Breaking changes** - If any, document them clearly

## 🎯 Current Priorities

We're actively working on:

- **Phase 3: Job System** - Enable humans to produce resources
- **Phase 4: Reproduction System** - Proper population dynamics

If you want to contribute to these areas, check the [Roadmap](docs/public/Roadmap/PHASES.md) and [Future Tickets](docs/public/Roadmap/FUTURE_TICKETS.md) for specific tasks!

## ❓ Questions?

Not sure about something? Have questions about the codebase? Feel free to:

- Open an issue with the `question` label
- Check existing documentation
- Look at similar code in the codebase

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

## 🙏 Thank You!

Every contribution, no matter how small, helps make Lunaris Civitas better. Thank you for taking the time to contribute! 🚀
