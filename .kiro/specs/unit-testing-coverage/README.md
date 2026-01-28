# Unit Testing Coverage - 70%+ Goal

## 📋 Overview

This specification outlines the comprehensive unit testing strategy for the RuoYi-Vue3-FastAPI project, targeting 70%+ code coverage across both frontend and backend.

## 📚 Documentation

- **[Requirements](./requirements.md)** - Testing strategy, priorities, and success criteria
- **[Implementation Guide](./implementation-guide.md)** - How to run tests, write new tests, and troubleshoot
- **[Summary](./summary.md)** - Current progress, metrics, and next steps

## 🚀 Quick Start

### Run All Tests

```bash
# Backend
cd ruoyi-fastapi-backend
./scripts/run_tests.sh

# Frontend
cd ruoyi-fastapi-frontend
./scripts/run-tests.sh
```

### View Coverage Reports

```bash
# Backend
open ruoyi-fastapi-backend/tests/coverage/html/index.html

# Frontend
open ruoyi-fastapi-frontend/tests/coverage/index.html
```

## 📊 Current Status

| Component | Coverage | Target | Status |
|-----------|----------|--------|--------|
| Backend | ~35% | 70% | 🟡 In Progress |
| Frontend | ~30% | 70% | 🟡 In Progress |

## 🎯 Key Achievements

✅ Test infrastructure fully set up
✅ 15 test files created (8 backend, 7 frontend)
✅ 270+ test cases implemented
✅ Property-based testing integrated
✅ Coverage reporting configured
✅ Test runner scripts created
✅ Comprehensive documentation

## 📁 Test Structure

### Backend Tests
```
ruoyi-fastapi-backend/tests/
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest configuration
├── unit/
│   ├── utils/                     # Utility tests (75% coverage)
│   │   ├── test_pwd_util.py
│   │   └── test_common_util.py
│   └── services/                  # Service tests (60% coverage)
│       ├── test_user_service.py
│       ├── test_project_service.py
│       ├── test_protocol_service.py
│       └── test_simulation_service.py
└── integration/                   # Integration tests (planned)
```

### Frontend Tests
```
ruoyi-fastapi-frontend/tests/
├── setup.ts                       # Test setup
├── vitest.config.ts              # Vitest configuration
├── unit/
│   ├── composables/              # Composable tests (70% coverage)
│   │   ├── useSimulationControl.test.ts
│   │   └── useBandwidthData.test.ts
│   ├── utils/                    # Utility tests (50% coverage)
│   │   ├── timeFormatter.test.ts
│   │   └── request.test.ts
│   ├── api/                      # API tests (40% coverage)
│   │   └── project.test.ts
│   ├── stores/                   # Store tests (60% coverage)
│   │   └── user.test.ts
│   └── simulation/               # Simulation tests
│       ├── timeFormatter.test.ts
│       └── topologyAnimation.test.ts
└── integration/                  # Integration tests (planned)
```

## 🔧 Technologies Used

### Backend
- pytest 8.0+ (test framework)
- pytest-asyncio (async support)
- pytest-cov (coverage)
- Hypothesis (property-based testing)
- SQLite in-memory (test database)

### Frontend
- Vitest (test framework)
- @vue/test-utils (component testing)
- fast-check (property-based testing)
- MSW (API mocking)
- Vitest coverage (v8 provider)

## 📈 Next Steps

### To Reach 70% Coverage

**Backend** (3-4 days):
1. Add remaining service tests (role, menu, dept, dict, config)
2. Add repository tests
3. Add controller tests
4. Fill coverage gaps

**Frontend** (3-4 days):
1. Add remaining composable tests
2. Add API service tests
3. Add store tests
4. Add component tests

### Future Enhancements
- Integration tests
- E2E tests
- CI/CD integration
- Coverage badges
- Performance testing

## 🎓 Testing Best Practices

1. **Write tests first** for new features (TDD)
2. **Mock external dependencies** (database, API, Redis)
3. **Use property-based tests** for validation logic
4. **Keep tests fast** (< 30s for unit tests)
5. **Test edge cases** and error conditions
6. **Use descriptive names** for tests
7. **Maintain test independence** (no shared state)
8. **Review coverage reports** regularly

## 🐛 Troubleshooting

### Backend Issues

**Import errors**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Database errors**: Check `conftest.py` for proper async setup

**Slow tests**: Use `pytest -n auto` for parallel execution

### Frontend Issues

**Module not found**:
```bash
rm -rf node_modules && yarn install
```

**Test timeout**: Increase timeout in `vitest.config.ts`

**Mock issues**: Check MSW handlers in `tests/setup.ts`

## 📞 Getting Help

- Check [Implementation Guide](./implementation-guide.md) for detailed instructions
- Review existing test files for examples
- Check coverage reports for gaps
- Run tests in watch mode for rapid feedback

## 🎉 Contributing

When adding new features:
1. Write tests for new code
2. Ensure tests pass locally
3. Check coverage hasn't decreased
4. Update documentation if needed
5. Run full test suite before committing

## 📝 Notes

- Coverage threshold is enforced at 70%
- Tests run automatically in CI/CD (when configured)
- Property-based tests use Hypothesis (backend) and fast-check (frontend)
- All async operations must be properly awaited
- Mock data should be realistic and comprehensive

---

**Project**: RuoYi-Vue3-FastAPI
**Goal**: 70%+ unit test coverage
**Status**: 🟡 In Progress (35-40% achieved)
**Target Date**: TBD
