# Unit Testing Implementation Guide

## Overview
This guide provides instructions for running and maintaining the unit test suite to achieve 70%+ coverage.

## Quick Start

### Backend Tests

```bash
# Navigate to backend directory
cd ruoyi-fastapi-backend

# Make test script executable
chmod +x scripts/run_tests.sh

# Run all tests with coverage
./scripts/run_tests.sh

# Run only unit tests
./scripts/run_tests.sh unit

# Run quick tests (no coverage)
./scripts/run_tests.sh quick

# Watch mode for development
./scripts/run_tests.sh watch
```

### Frontend Tests

```bash
# Navigate to frontend directory
cd ruoyi-fastapi-frontend

# Make test script executable
chmod +x scripts/run-tests.sh

# Run all tests with coverage
./scripts/run-tests.sh

# Run only unit tests
./scripts/run-tests.sh unit

# Run quick tests (no coverage)
./scripts/run-tests.sh quick

# Watch mode for development
./scripts/run-tests.sh watch
```

## Test Structure

### Backend Test Organization

```
ruoyi-fastapi-backend/tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── utils/
│   │   ├── test_pwd_util.py      # Password utility tests
│   │   └── test_common_util.py   # Common utility tests
│   ├── services/
│   │   ├── test_user_service.py  # User service tests
│   │   ├── test_project_service.py
│   │   └── test_protocol_service.py
│   └── repositories/
└── integration/
```

### Frontend Test Organization

```
ruoyi-fastapi-frontend/tests/
├── setup.ts                       # Test setup
├── unit/
│   ├── composables/
│   │   ├── useSimulationControl.test.ts
│   │   └── useBandwidthData.test.ts
│   ├── utils/
│   │   ├── timeFormatter.test.ts
│   │   └── request.test.ts
│   ├── api/
│   │   └── project.test.ts
│   └── components/
└── integration/
```

## Writing Tests

### Backend Test Example

```python
import pytest
from hypothesis import given, strategies as st

class TestUserService:
    """Test suite for user service."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_service, mock_dao):
        """Test getting user by ID."""
        mock_dao.get_user_by_id.return_value = sample_user
        
        result = await user_service.get_user_by_id(1)
        
        assert result is not None
        assert result.user_id == 1

    @given(st.text(min_size=1, max_size=100))
    def test_password_validation(self, password: str):
        """Property test: password validation."""
        hashed = PwdUtil.hash_password(password)
        assert PwdUtil.verify_password(password, hashed)
```

### Frontend Test Example

```typescript
import { describe, it, expect, vi } from 'vitest'

describe('useSimulationControl', () => {
  it('should start simulation', async () => {
    const control = useSimulationControl(1)
    
    await control.start()
    
    expect(control.isRunning.value).toBe(true)
  })

  it('should handle errors gracefully', async () => {
    const control = useSimulationControl(1)
    
    await expect(control.start()).rejects.toThrow()
  })
})
```

## Coverage Requirements

### Target Coverage by Module

| Module | Target | Priority |
|--------|--------|----------|
| Backend Utils | 80%+ | High |
| Backend Services | 70%+ | High |
| Backend Repositories | 60%+ | Medium |
| Backend Controllers | 60%+ | Medium |
| Frontend Composables | 80%+ | High |
| Frontend Utils | 80%+ | High |
| Frontend API Services | 60%+ | Medium |
| Frontend Components | 60%+ | Medium |

### Coverage Thresholds

Both backend and frontend are configured to fail if coverage drops below 70%.

## Best Practices

### 1. Test Naming
- Use descriptive test names that explain what is being tested
- Follow pattern: `test_<action>_<expected_result>`
- Example: `test_add_user_validates_email`

### 2. Test Organization
- Group related tests in classes (backend) or describe blocks (frontend)
- Use fixtures/setup for common test data
- Keep tests independent and isolated

### 3. Mocking
- Mock external dependencies (database, API calls, etc.)
- Use fixtures for reusable mocks
- Verify mock calls when testing interactions

### 4. Property-Based Testing
- Use Hypothesis (backend) or fast-check (frontend) for property tests
- Test invariants and edge cases automatically
- Useful for validation logic and data transformations

### 5. Async Testing
- Use `@pytest.mark.asyncio` for async backend tests
- Properly await all async operations
- Handle async errors correctly

### 6. Coverage Gaps
- Review coverage reports regularly
- Focus on critical business logic first
- Don't chase 100% coverage - focus on meaningful tests

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd ruoyi-fastapi-backend
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd ruoyi-fastapi-backend
          pytest --cov --cov-fail-under=70

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd ruoyi-fastapi-frontend
          yarn install
      - name: Run tests
        run: |
          cd ruoyi-fastapi-frontend
          yarn test:run --coverage
```

## Troubleshooting

### Common Issues

#### Backend: Import Errors
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Backend: Database Connection Errors
- Tests use SQLite in-memory database
- Check `conftest.py` for database setup
- Ensure async fixtures are properly configured

#### Frontend: Module Not Found
```bash
# Clear cache and reinstall
rm -rf node_modules
yarn install
```

#### Frontend: Test Timeout
- Increase timeout in `vitest.config.ts`
- Check for unresolved promises
- Ensure proper cleanup in tests

### Debugging Tests

#### Backend
```bash
# Run with verbose output
pytest -vv tests/

# Run specific test
pytest tests/unit/services/test_user_service.py::TestUserService::test_get_user_by_id

# Run with debugger
pytest --pdb tests/
```

#### Frontend
```bash
# Run with UI
yarn test:ui

# Run specific test file
yarn test tests/unit/composables/useSimulationControl.test.ts

# Debug in browser
yarn test --browser
```

## Maintenance

### Adding New Tests

1. Create test file following naming convention
2. Import necessary fixtures and utilities
3. Write test cases covering:
   - Happy path
   - Error cases
   - Edge cases
   - Property-based tests (where applicable)
4. Run tests locally
5. Check coverage report
6. Commit with descriptive message

### Updating Existing Tests

1. Identify failing or outdated tests
2. Update test logic to match new implementation
3. Ensure all tests pass
4. Verify coverage hasn't decreased
5. Update documentation if needed

### Coverage Reports

#### Backend
- HTML report: `ruoyi-fastapi-backend/tests/coverage/html/index.html`
- JSON report: `ruoyi-fastapi-backend/tests/coverage/coverage.json`

#### Frontend
- HTML report: `ruoyi-fastapi-frontend/tests/coverage/index.html`
- JSON report: `ruoyi-fastapi-frontend/tests/coverage/coverage-summary.json`

## Next Steps

### Phase 1: Complete Core Coverage (Current)
- [x] Set up test infrastructure
- [x] Implement utility tests (80%+)
- [x] Implement service tests (70%+)
- [x] Implement composable tests (80%+)
- [x] Implement API tests (60%+)

### Phase 2: Expand Coverage
- [ ] Add repository tests
- [ ] Add controller tests
- [ ] Add component tests
- [ ] Add integration tests

### Phase 3: CI/CD Integration
- [ ] Set up GitHub Actions
- [ ] Add coverage badges
- [ ] Configure automatic test runs
- [ ] Set up coverage tracking

### Phase 4: Maintenance
- [ ] Regular coverage reviews
- [ ] Update tests for new features
- [ ] Refactor flaky tests
- [ ] Document testing patterns
