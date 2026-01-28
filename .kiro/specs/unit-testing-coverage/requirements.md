# Unit Testing Coverage Requirements

## Goal
Achieve 70%+ unit test coverage across the full-stack application with comprehensive, maintainable tests.

## Current State
- **Frontend**: Minimal tests (2 test files for simulation module)
- **Backend**: Basic seed data tests only
- **Coverage**: < 10% estimated

## Target State
- **Frontend Coverage**: 70%+ line coverage
- **Backend Coverage**: 70%+ line coverage
- **Test Quality**: Property-based tests where applicable, comprehensive edge case coverage

## Testing Strategy

### Backend Testing Priorities

#### 1. Core Business Logic (High Priority)
- **Services Layer** (70%+ coverage target)
  - User service (authentication, CRUD)
  - Role service (permissions, data scope)
  - Menu service (tree operations)
  - Project service (CRUD, validation)
  - Protocol service (parsing, validation)
  - Simulation service (engine, runner)
  - Device service (CRUD, categories)

#### 2. Data Access Layer (Medium Priority)
- **Repositories** (60%+ coverage target)
  - Query builders
  - Specifications
  - Complex queries

#### 3. API Controllers (Medium Priority)
- **Controllers** (60%+ coverage target)
  - Request validation
  - Response formatting
  - Error handling
  - Permission checks

#### 4. Utilities (High Priority)
- **Utils** (80%+ coverage target)
  - Password utilities
  - Time formatting
  - Excel utilities
  - Common utilities

### Frontend Testing Priorities

#### 1. Composables (High Priority)
- **Simulation Composables** (80%+ coverage target)
  - useSimulationControl
  - useSimulationData
  - useTopologyAnimation
  - useBandwidthData
  - useEventTrigger

#### 2. Utilities (High Priority)
- **Utils** (80%+ coverage target)
  - Time formatters
  - Data transformers
  - Validators

#### 3. Components (Medium Priority)
- **Business Components** (60%+ coverage target)
  - Protocol templates
  - Form components
  - Data display components

#### 4. API Services (Medium Priority)
- **API Layer** (60%+ coverage target)
  - Request/response handling
  - Error handling
  - Data transformation

## Testing Approach

### Backend Testing Stack
- **Framework**: pytest + pytest-asyncio
- **Coverage**: pytest-cov
- **Property Testing**: hypothesis (already installed)
- **Mocking**: pytest fixtures + unittest.mock
- **Database**: SQLite in-memory for tests

### Frontend Testing Stack
- **Framework**: Vitest + Vue Test Utils
- **Coverage**: Vitest coverage (v8)
- **Property Testing**: fast-check (already used)
- **Mocking**: MSW for API mocking
- **Component Testing**: @vue/test-utils

## Test Organization

### Backend Structure
```
ruoyi-fastapi-backend/tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests
│   ├── services/                  # Service layer tests
│   ├── repositories/              # Repository tests
│   ├── utils/                     # Utility tests
│   └── controllers/               # Controller tests
├── integration/                   # Integration tests
│   ├── api/                       # API endpoint tests
│   └── database/                  # Database integration tests
└── property/                      # Property-based tests
    ├── services/
    └── utils/
```

### Frontend Structure
```
ruoyi-fastapi-frontend/tests/
├── setup.ts                       # Test setup
├── unit/                          # Unit tests
│   ├── composables/               # Composable tests
│   ├── utils/                     # Utility tests
│   ├── components/                # Component tests
│   └── api/                       # API service tests
├── integration/                   # Integration tests
│   └── views/                     # View integration tests
└── e2e/                          # E2E tests (future)
```

## Success Criteria

### Coverage Metrics
- [ ] Backend overall coverage: 70%+
- [ ] Frontend overall coverage: 70%+
- [ ] Critical paths coverage: 90%+
- [ ] Utility functions coverage: 80%+

### Test Quality
- [ ] All tests pass consistently
- [ ] No flaky tests
- [ ] Fast test execution (< 30s for unit tests)
- [ ] Clear test descriptions
- [ ] Property-based tests for critical logic

### CI/CD Integration
- [ ] Tests run on every commit
- [ ] Coverage reports generated
- [ ] Coverage thresholds enforced
- [ ] Test results visible in PR

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Set up test infrastructure
- Create shared fixtures and utilities
- Implement utility function tests (80%+ coverage)

### Phase 2: Core Business Logic (Week 2)
- Service layer tests (70%+ coverage)
- Repository tests (60%+ coverage)
- Composable tests (80%+ coverage)

### Phase 3: API & Components (Week 3)
- Controller tests (60%+ coverage)
- Component tests (60%+ coverage)
- API service tests (60%+ coverage)

### Phase 4: Integration & Polish (Week 4)
- Integration tests
- Property-based tests for critical paths
- Coverage gap analysis and filling
- Documentation and CI/CD setup
