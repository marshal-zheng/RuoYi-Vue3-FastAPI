# Testing Guide

Quick reference for running and writing tests in RuoYi-Vue3-FastAPI.

## 🚀 Quick Commands

### Backend Tests
```bash
cd ruoyi-fastapi-backend

# Run all tests with coverage
./scripts/run_tests.sh

# Quick run (no coverage)
./scripts/run_tests.sh quick

# Unit tests only
./scripts/run_tests.sh unit

# Watch mode
./scripts/run_tests.sh watch

# Specific test file
pytest tests/unit/services/test_user_service.py -v

# Specific test case
pytest tests/unit/services/test_user_service.py::TestUserService::test_get_user_by_id -v
```

### Frontend Tests
```bash
cd ruoyi-fastapi-frontend

# Run all tests with coverage
./scripts/run-tests.sh

# Quick run (no coverage)
./scripts/run-tests.sh quick

# Unit tests only
./scripts/run-tests.sh unit

# Watch mode
./scripts/run-tests.sh watch

# Specific test file
yarn test tests/unit/composables/useSimulationControl.test.ts

# UI mode
yarn test:ui
```

## 📊 Coverage Reports

### Backend
```bash
# Generate and view coverage report
cd ruoyi-fastapi-backend
./scripts/run_tests.sh
open tests/coverage/html/index.html
```

### Frontend
```bash
# Generate and view coverage report
cd ruoyi-fastapi-frontend
./scripts/run-tests.sh
open tests/coverage/index.html
```

## ✍️ Writing Tests

### Backend Test Template

```python
"""
Unit tests for <module> service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_dao():
    """Create mock DAO."""
    dao = MagicMock()
    dao.get_by_id = AsyncMock()
    return dao

@pytest.fixture
def service(mock_dao):
    """Create service with mocked dependencies."""
    service = MyService()
    service.dao = mock_dao
    return service

class TestMyService:
    """Test suite for my service."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_dao):
        """Test getting item by ID successfully."""
        mock_dao.get_by_id.return_value = sample_item
        
        result = await service.get_by_id(1)
        
        assert result is not None
        assert result.id == 1
```

### Frontend Test Template

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock dependencies
vi.mock('@/api/module/api')

describe('MyComposable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Feature Name', () => {
    it('should do something', () => {
      const composable = useMyComposable()
      
      composable.doSomething()
      
      expect(composable.state.value).toBe(expected)
    })

    it('should handle errors', async () => {
      const composable = useMyComposable()
      
      await expect(composable.doSomething()).rejects.toThrow()
    })
  })
})
```

## 🎯 Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| Backend Utils | 80% | ~75% |
| Backend Services | 70% | ~60% |
| Backend Repositories | 60% | ~0% |
| Backend Controllers | 60% | ~0% |
| Frontend Composables | 80% | ~70% |
| Frontend Utils | 80% | ~50% |
| Frontend API Services | 60% | ~40% |
| Frontend Components | 60% | ~0% |

## 🔧 Common Issues

### Backend

**Import Error**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async Test Not Running**:
```python
@pytest.mark.asyncio  # Don't forget this!
async def test_async_function():
    result = await my_async_function()
    assert result is not None
```

**Mock Not Working**:
```python
# Use AsyncMock for async functions
mock_dao.get_by_id = AsyncMock(return_value=expected)
```

### Frontend

**Module Not Found**:
```bash
rm -rf node_modules && yarn install
```

**Test Timeout**:
```typescript
// Increase timeout for slow tests
it('slow test', async () => {
  // test code
}, 10000) // 10 second timeout
```

**Mock Not Applied**:
```typescript
// Mock before importing the module that uses it
vi.mock('@/api/module/api')
import { useMyComposable } from '@/composables/useMyComposable'
```

## 📚 Documentation

- **Full Guide**: `.kiro/specs/unit-testing-coverage/README.md`
- **Requirements**: `.kiro/specs/unit-testing-coverage/requirements.md`
- **Implementation**: `.kiro/specs/unit-testing-coverage/implementation-guide.md`
- **Summary**: `.kiro/specs/unit-testing-coverage/summary.md`

## 🎓 Best Practices

1. ✅ Write tests for new features
2. ✅ Mock external dependencies
3. ✅ Test edge cases and errors
4. ✅ Keep tests fast and independent
5. ✅ Use descriptive test names
6. ✅ Review coverage reports
7. ✅ Run tests before committing

## 🚦 CI/CD Integration

Tests will run automatically on:
- Every commit (unit tests)
- Pull requests (full test suite)
- Before deployment (all tests + coverage check)

Coverage must be ≥ 70% to pass.

---

For detailed information, see `.kiro/specs/unit-testing-coverage/`
