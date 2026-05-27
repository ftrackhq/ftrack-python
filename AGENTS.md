# ftrack Python API - Agent Specifications

## Project Overview

**ftrack-python-api** is the official Python client library for interacting with ftrack, a project management and media review platform. This API provides a high-level, Pythonic interface for creating, querying, updating, and managing entities in ftrack.

- **Repository**: https://github.com/ftrackhq/ftrack-python
- **Documentation**: https://developer.ftrack.com/api-clients/python/
- **API Reference**: https://ftrack-python-api.readthedocs.io/en/stable/api_reference/index.html
- **Package**: ftrack-python-api (distributed via PyPI)
- **License**: Apache-2.0
- **Python Support**: 3.8 - 3.13

## Architecture

### Core Components

1. **Session** (`session.py`) - Main entry point
   - Manages connection to ftrack server
   - Handles authentication (API key + user)
   - Provides entity querying, creation, and updates
   - Manages event hub for real-time updates
   - Implements caching layer
   - Thread-safe operations

2. **Entity System** (`entity/`)
   - Factory pattern for creating entity types
   - Base entity classes with attribute management
   - Location system for file storage
   - Dynamic entity type construction from schema

3. **Event System** (`event/`)
   - Event hub for publish/subscribe pattern
   - WebSocket-based real-time event streaming
   - Event handlers and listeners

4. **Storage System** (`accessor/`, `structure/`)
   - **Accessors**: Abstract file I/O (disk, server)
   - **Structures**: Define file organization patterns
   - Centralized storage scenario support

5. **Query System** (`query.py`)
   - Query language parser (uses pyparsing)
   - Expression building and filtering
   - Projection and selection

6. **Cache System** (`cache.py`)
   - In-memory entity caching
   - Cache key generation
   - Layered cache support

### Module Structure

```
source/ftrack_api/
├── __init__.py              # Main package exports (Session, mixin)
├── __init__.pyi             # Type stubs for main exports
├── py.typed                 # PEP 561 marker for typed package
├── session.py               # Core session implementation (2,700+ lines)
├── session.pyi              # Type stubs for Session
├── entity/                  # Entity type system
│   ├── factory.py          # Entity creation
│   ├── base.py             # Base entity class
│   ├── location.py         # Location management
│   └── *.pyi               # Type stubs for entities
├── event/                   # Event system
│   ├── hub.py              # Event hub
│   ├── base.py             # Event classes
│   └── *.pyi               # Type stubs for events
├── accessor/                # Storage accessors
│   ├── disk.py             # Local disk I/O
│   ├── server.py           # Server-based storage
│   └── *.pyi               # Type stubs for accessors
├── structure/               # File structure patterns
│   ├── origin.py
│   ├── entity_id.py
│   └── *.pyi               # Type stubs for structures
├── resource_identifier_transformer/
├── attribute.py             # Entity attributes
├── cache.py                # Caching layer
├── collection.py           # Entity collections
├── query.py                # Query language
├── exception.py            # Custom exceptions
├── plugin.py               # Plugin system
├── operation.py            # Operation tracking
└── _centralized_storage_scenario.py
```

## Development Setup

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Installation

```bash
# Install runtime + all dependency groups (dev + test)
uv sync --all-groups

# Install runtime only
uv sync --no-default-groups

# Install with only the dev group
uv sync --group dev

# Install with only the test group
uv sync --group test
```

### Environment Variables

Required for API access:
- `FTRACK_SERVER` - ftrack server URL (e.g., https://mycompany.ftrackapp.com)
- `FTRACK_API_USER` - API username
- `FTRACK_API_KEY` - API key for authentication

### Key Dependencies

**Runtime:**
- `requests>=2,<3` - HTTP client
- `arrow>=0.4.4,<1` - Date/time handling
- `pyparsing>=2.0,<3` - Query language parser
- `clique==1.6.1` - Sequence management
- `websocket-client>=0.40.0,<1` - Event hub WebSocket
- `platformdirs>=4.0.0,<5` - Platform-specific directories

**Development:**
- `black==24.0` - Code formatting (updated from legacy versions)
- `pre-commit` - Git hooks
- `sphinx` + `sphinx_rtd_theme` - Documentation
- `twine` - Package validation and upload

**Testing:**
- `pytest` - Test framework
- `pytest-mock` - Mocking support
- `mock` - Mock objects
- `flaky` - Retry flaky tests

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ftrack_api

# Run specific test file
uv run pytest test/unit/test_session.py

# Disable warnings (CI mode)
uv run pytest --disable-pytest-warnings
```

### Test Structure

```
test/
├── fixture/
│   └── plugin/              # Test plugins
├── unit/
│   ├── accessor/            # Accessor tests
│   ├── entity/              # Entity tests
│   ├── conftest.py          # Test configuration
│   └── test_*.py            # Unit tests
└── integration/             # Integration tests (require live server)
```

### Test Configuration

- **pytest.ini**: Test discovery patterns, JUnit XML output
- Tests write reports to `test-reports/junit.xml`
- Mock mode available via `mock_use_standalone_module = true`

### Important Test Notes

- Integration tests require live ftrack server credentials
- Use `@pytest.mark.flaky` for tests that may be unreliable
- Tests should clean up entities they create
- Mock external dependencies (network, filesystem) in unit tests

## Build & Release

### Version Management

Uses **hatch-vcs** (via the `hatchling` build backend) for automatic versioning:
- Version extracted from git tags
- Format: `v{major}.{minor}.{patch}` (e.g., v2.5.1)
- Written to `source/ftrack_api/_version.py` at build time

### Building

```bash
# Build wheel
uv build --wheel

# Validate distribution
uvx twine check dist/*
```

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/cicd.yml`):

1. **check-formatting**: Black formatting validation
2. **run-tests**: Matrix testing across Python 3.8-3.13
3. **build**: Package distribution build
4. **publish-test**: Deploy to test.pypi.org (on tag push)
5. **publish-prod**: Deploy to pypi.org (on tag push, production env)

**Branch Strategy:**
- `main` - Primary development branch
- Tags trigger PyPI releases: `v*`
- PRs run full test suite

**Publishing Process:**
1. Create and push version tag: `git tag v2.5.1 && git push origin v2.5.1`
2. CI builds and tests across all Python versions
3. Publishes to test PyPI (staging environment)
4. Publishes to production PyPI (production environment)

## Key Concepts & Patterns

### Session Management

```python
import ftrack_api

# Basic session
session = ftrack_api.Session(
    server_url='https://mycompany.ftrackapp.com',
    api_key='your-api-key',
    api_user='user@email.com'
)

# With event hub
session = ftrack_api.Session(auto_connect_event_hub=True)

# With custom cache
session = ftrack_api.Session(cache=custom_cache)
```

### Entity Operations

- **Query**: `session.query('Task where project.name is "MyProject"')`
- **Create**: `session.create('Task', {...})`
- **Update**: `entity['name'] = 'New Name'; session.commit()`
- **Delete**: `session.delete(entity); session.commit()`

### Plugin System

- Plugins in `resource/plugin/`
- Loaded via `plugin_paths` argument
- Hooks for session lifecycle events
- Can extend entity types and behaviors

### Mixin Pattern

The `mixin()` function dynamically adds functionality to entity instances:

```python
ftrack_api.mixin(entity, CustomMixin, name='CustomEntity')
```

### Thread Safety

- Sessions should not be shared across threads
- Use `threading.Lock` for shared resources
- Event hub manages its own thread for WebSocket

## Important Files & Locations

### Configuration
- `pyproject.toml` - PEP 621 project config (build via `hatchling` + `hatch-vcs`), runtime + dev/test dependency groups
- `pytest.ini` - Test configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `setup.cfg` - Legacy setuptools config
- `readthedocs.yaml` - ReadTheDocs build config

### Documentation
- `doc/` - Sphinx documentation source
- `doc/api_reference/` - API reference docs
- `README.rst` - Package overview

### Type Safety
- `source/ftrack_api/**/*.pyi` - Type stub files (PEP 561)
- `source/ftrack_api/py.typed` - Marker file indicating typed package
- `test/unit/test_stubs.py` - Type stub validation tests

### Code Quality
- `.git-blame-ignore-revs` - Git blame configuration
- `CODEOWNERS` - GitHub code ownership

### Build Artifacts
- `dist/` - Built distributions
- `test-reports/` - JUnit test results
- `.pytest_cache/` - Pytest cache

## Common Development Tasks

### Adding New Features

1. Understand the entity schema from ftrack server
2. Implement in appropriate module (`entity/`, `accessor/`, etc.)
3. Add unit tests in `test/unit/`
4. Update type stubs (`.pyi` files) alongside implementation for type safety
5. Document in `doc/`

### Fixing Bugs

1. Write failing test that reproduces the bug
2. Implement fix
3. Ensure test passes
4. Check for similar issues in related code

### Code Style

- **Black 24.0** formatting (enforced in CI)
- Run `black .` before committing
- Pre-commit hooks auto-format
- Type hints: Use `.pyi` stub files for type annotations (PEP 561 compliant)

### Adding Dependencies

```bash
# Runtime dependency
uv add package-name

# Dev dependency
uv add --group dev package-name

# Test dependency
uv add --group test package-name
```

## Integration Points

### ftrack Server API
- REST API for entity operations
- WebSocket for event streaming
- Schema endpoint for entity type definitions
- File upload/download endpoints

### Storage Systems
- Local disk via `ftrack_api.accessor.disk`
- ftrack server storage via `ftrack_api.accessor.server`
- Custom accessors can be implemented

### Event System
- Subscribe to server events
- Publish custom events
- Action handlers for UI extensions

## Troubleshooting

### Common Issues

1. **Authentication failures**
   - Check `FTRACK_SERVER`, `FTRACK_API_KEY`, `FTRACK_API_USER`
   - Verify API key is active and has permissions

2. **Connection timeouts**
   - Adjust `timeout` parameter in Session
   - Check network connectivity
   - Recent fix in commit 60d77d0 for server accessor timeout

3. **Event hub not connecting**
   - Ensure `auto_connect_event_hub=True`
   - Check WebSocket ports (typically 443/80)
   - Verify firewall rules

4. **Thread safety issues**
   - Don't share sessions across threads
   - Use separate session per thread
   - Recent fix in commit 95ac2ae for thread-safe session sharing

5. **Cache inconsistencies**
   - Clear cache: `session.reset()`
   - Disable cache: `session = Session(cache=None)`
   - Use custom cache with invalidation logic

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Session with strict API (raises on deprecations)
session = Session(strict_api=True)

# Inspect operations before commit
print(session.recorded_operations)
```

## Recent Changes

Based on recent commits (2025-2026):
- **51e8c27** (Apr 2026): Added comprehensive Python type stubs (.pyi files) for full type safety (#64)
  - All modules now have corresponding `.pyi` stub files
  - Package marked as typed with `py.typed` marker (PEP 561)
  - Includes stubs for Session, entities, events, accessors, structures, and more
  - Enables better IDE autocompletion and static type checking
- **fa82e38** (Apr 2026): Updated Black formatter to version 24.0 (#65)
- **79a5596** (2025): Enabled Python 3.13 in CI testing (#53)
- **b2c1c36** (2025): Fixed restricted projections not being properly hidden (#49)
- **576d2db** (2025): Augmented source event with additional data (#40)
- **60d77d0** (2024): Fixed server accessor timeout issue
- **47730e4** (2024): Fixed UnboundLocalError in python-api (#59)
- **4f26f7f** (2024): Added support for date type (#57)
- **89dc2c6** (2024): Fixed publish jobs picking up correct tag (#56)
- **95ac2ae** (2024): Fixed thread-safe session sharing across threads (#55)

## Resources

- **GitHub Issues**: Report bugs and request features
- **Developer Docs**: https://developer.ftrack.com/api-clients/python/
- **API Reference**: https://ftrack-python-api.readthedocs.io/
- **ftrack Community**: Support forum and discussion

## Notes for AI Agents

1. **Session is central**: Almost all operations go through the Session object
2. **Schema-driven**: Entity types are dynamically constructed from server schema
3. **Lazy loading**: Entities populate attributes on access, not at creation
4. **Query language**: Custom DSL, not SQL - use session.query() examples
5. **Event-driven**: Many ftrack operations trigger events that can be subscribed to
6. **Location system**: File storage abstraction - understand accessor vs structure
7. **Thread model**: One session per thread, event hub runs in separate thread
8. **Cache implications**: Cached entities may be stale, use session.reset() or disable
9. **Commit required**: Changes are tracked but not saved until session.commit()
10. **Plugin system**: Extensible via plugins - check resource/plugin/ for examples
11. **Type safety**: Package is fully typed with `.pyi` stub files (PEP 561 compliant)
    - Use type stubs for better IDE support and static analysis
    - When adding new code, create or update corresponding `.pyi` files
    - Type stubs are distributed with the package in wheels and sdist