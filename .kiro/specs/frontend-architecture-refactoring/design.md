# Design Document: Frontend Architecture Refactoring

## Overview

This design document outlines the technical approach for refactoring the frontend architecture of the RuoYi-Vue3-FastAPI project. The refactoring is a one-time structural reorganization that moves files to establish clear directory semantics and dependency boundaries without modifying business logic.

The refactoring follows a phased approach with three migration phases, each targeting specific modules. Each phase includes file movement, import path updates, and comprehensive validation before proceeding to the next phase.

## Architecture

### Current Structure Issues

The current frontend structure has several architectural issues:

1. **Mixed Component Responsibilities**: Components in `src/components/` include both pure UI components and business logic components without clear separation
2. **Unclear API Boundaries**: No distinction between domain-level APIs and page-specific API encapsulations
3. **Inconsistent Import Paths**: Mix of relative and absolute paths without clear conventions
4. **Component Classification Ambiguity**: `DictSelect` is in root components but contains API calls (should be business component)

### Target Structure

The target structure establishes three clear layers:

```
src/
├── api/                         # Domain API Layer (global)
│   ├── _shared/                 # HTTP client, common request layer
│   ├── common.ts                # Global common APIs
│   └── <domain>/                # Domain-specific APIs
│
├── components/
│   ├── ui/                      # Pure UI components (no API calls)
│   │   └── index.ts             # Unified export
│   └── business/                # Business components (can call src/api)
│
└── views/                       # Page Layer
    └── <module>/
        ├── api/                 # Page-level API (module-specific)
        ├── components/          # Module-private components
        └── *.vue                # Page components
```

### Dependency Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         views/module                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Can import:                                            │ │
│  │ - views/module/api (page-level)                       │ │
│  │ - src/api/<domain> (domain-level)                     │ │
│  │ - src/components/* (all components)                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   components/business                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Can import:                                            │ │
│  │ - src/api/<domain> (domain-level only)                │ │
│  │ - src/utils, src/constants                            │ │
│  │ - components/ui                                        │ │
│  │                                                         │ │
│  │ Cannot import:                                         │ │
│  │ - views/*/api (page-level APIs)                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      components/ui                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Can import:                                            │ │
│  │ - src/utils, src/constants, src/types                 │ │
│  │                                                         │ │
│  │ Cannot import:                                         │ │
│  │ - Any src/api/* (no API calls allowed)                │ │
│  │ - views/* (no page dependencies)                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Component Classification System

#### UI Components (`src/components/ui/`)

**Characteristics:**
- Pure presentational components
- Only accept props and emit events
- No API calls or business logic
- Can use utility functions and constants

**Examples:**
- Pagination
- FileUpload
- ImageUpload
- Breadcrumb
- SvgIcon

**Interface Pattern:**
```typescript
// src/components/ui/Pagination/index.vue
interface Props {
  total: number
  page: number
  limit: number
}

interface Emits {
  (e: 'update:page', value: number): void
  (e: 'update:limit', value: number): void
  (e: 'pagination', value: { page: number; limit: number }): void
}
```

#### Business Components (`src/components/business/`)

**Characteristics:**
- Can call domain APIs (`src/api/<domain>`)
- Contain business logic
- Reusable across multiple modules (2+)
- Cannot call page-level APIs

**Examples:**
- DictSelect (moved from root)
- Protocol components
- Dag components
- Device components
- Monitor components

**Interface Pattern:**
```typescript
// src/components/business/DictSelect/index.vue
import { getDictData } from '@/api/common'

interface Props {
  dictType: string
  modelValue: string | number
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
}
```

#### Module Components (`views/module/components/`)

**Characteristics:**
- Private to specific module
- Can call both page-level and domain APIs
- Not reusable across modules

**Examples:**
- ProjectFormDialog
- NodeEditDrawer
- VersionList

### API Layer Organization

#### Domain API (`src/api/<domain>/`)

**Purpose:** Direct mapping to backend endpoints, pure data access

**Structure:**
```
src/api/project/
├── project.ts       # Project CRUD operations
├── version.ts       # Version management
└── topology.ts      # Topology operations
```

**Interface Pattern:**
```typescript
// src/api/project/project.ts
export interface ProjectQuery {
  pageNum?: number
  pageSize?: number
  projectName?: string
  status?: string
}

export interface ProjectData {
  projectId: number
  projectName: string
  description: string
  status: string
}

export function listProject(query: ProjectQuery): Promise<ApiResponse<ProjectData[]>>
export function getProject(projectId: number): Promise<ApiResponse<ProjectData>>
export function addProject(data: ProjectData): Promise<ApiResponse<void>>
export function updateProject(data: ProjectData): Promise<ApiResponse<void>>
export function delProject(projectId: number): Promise<ApiResponse<void>>
```

#### Page-Level API (`views/module/api/`)

**Purpose:** Encapsulate multiple domain API calls for page-specific logic

**Structure:**
```
views/project/api/
├── index.ts         # Aggregated exports
├── listPage.ts      # List page encapsulation
└── export.ts        # Export functionality
```

**Interface Pattern:**
```typescript
// views/project/api/listPage.ts
import { listProject, type ProjectQuery } from '@/api/project/project'
import { getDictData } from '@/api/common'

export interface EnhancedProjectQuery extends ProjectQuery {
  // Additional page-specific fields
}

export async function fetchProjectListWithDict(params: EnhancedProjectQuery) {
  const [projectRes, statusDict] = await Promise.all([
    listProject(params),
    getDictData('project_status')
  ])
  
  return {
    rows: projectRes.rows,
    total: projectRes.total,
    statusOptions: statusDict
  }
}
```

#### Common API (`src/api/common.ts`)

**Purpose:** Global common APIs used across multiple modules

**Interface Pattern:**
```typescript
// src/api/common.ts
export interface DictData {
  dictCode: number
  dictLabel: string
  dictValue: string
  dictType: string
}

export function getDictData(dictType: string): Promise<ApiResponse<DictData[]>>
export function getUserList(): Promise<ApiResponse<UserData[]>>
export function getDeptList(): Promise<ApiResponse<DeptData[]>>
export function getRoleList(): Promise<ApiResponse<RoleData[]>>
```

## Data Models

### File Movement Record

```typescript
interface FileMoveOperation {
  sourcePath: string
  targetPath: string
  fileType: 'component' | 'api' | 'other'
  phase: 1 | 2 | 3
  status: 'pending' | 'completed' | 'failed'
}
```

### Import Path Update Record

```typescript
interface ImportPathUpdate {
  filePath: string
  oldImport: string
  newImport: string
  importType: 'relative' | 'absolute'
  status: 'pending' | 'completed' | 'failed'
}
```

### Component Classification

```typescript
type ComponentType = 'ui' | 'business' | 'module'

interface ComponentClassification {
  componentPath: string
  componentName: string
  type: ComponentType
  hasApiCalls: boolean
  usedInModules: string[]
  targetPath: string
}
```

### Migration Phase

```typescript
interface MigrationPhase {
  phaseNumber: 1 | 2 | 3
  modules: string[]
  priority: 'high' | 'medium' | 'low'
  fileMoves: FileMoveOperation[]
  importUpdates: ImportPathUpdate[]
  validationStatus: 'pending' | 'passed' | 'failed'
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified the following redundancies and consolidations:

**Redundancy Analysis:**

1. **Import Path Properties (3.1, 3.2, 3.3, 3.4, 3.5)**: These can be consolidated into two comprehensive properties:
   - One for path convention consistency (covers 3.1, 3.2, 3.5)
   - One for import correctness after moves (covers 3.3, 3.4)

2. **File Movement Properties (4.1, 4.2, 4.3, 4.4, 4.5)**: These can be consolidated into two properties:
   - One for content preservation (covers 4.2, 4.3, 4.4)
   - One for git history preservation (covers 4.1, 4.5)

3. **Validation Properties (6.1, 6.2, 6.3, 14.1, 14.2, 14.3)**: These are duplicates and can be consolidated into one comprehensive validation property

4. **Component Classification Properties (7.1, 7.2, 7.3)**: These can be consolidated into one property about correct component placement based on characteristics

5. **API Boundary Properties (8.1, 8.2, 8.3, 8.4, 8.5)**: Properties 8.3 and 8.4 are subsumed by the more general dependency boundary property

6. **TypeScript Migration Properties (9.1, 9.2, 9.3, 9.4)**: These can be consolidated into one property about API files being TypeScript

7. **Page-Level API Properties (10.2, 10.3, 10.4, 10.5)**: Properties 10.3 and 10.5 are related to dependency boundaries and can be consolidated

**Consolidated Property Set:**

After reflection, we have the following unique, non-redundant properties:

1. Import path convention consistency
2. Import correctness after file moves
3. Content preservation during moves
4. Git history preservation
5. Phase validation success
6. Component classification correctness
7. Dependency boundary enforcement
8. TypeScript migration completeness
9. Page-level API isolation
10. UI component unified export
11. No duplicate files after migration
12. Module API directory structure

### Correctness Properties

Property 1: Import Path Convention Consistency
*For any* import statement in the codebase, if the import is within the same module, it should use a relative path; if the import is across modules, it should use an absolute path starting with `@/`
**Validates: Requirements 3.1, 3.2, 3.5**

Property 2: Import Correctness After File Moves
*For any* file that is moved, all import statements referencing that file should be updated to the new path, and TypeScript compilation should succeed without import resolution errors
**Validates: Requirements 3.3, 3.4**

Property 3: Content Preservation During Moves
*For any* file that is moved, the file content (excluding import statements) should remain identical to the original, with no business logic modifications or reimplementations
**Validates: Requirements 4.2, 4.3, 4.4**

Property 4: Git History Preservation
*For any* file that is moved, the git history should show the operation as a rename (not delete + add), preserving the file's commit history
**Validates: Requirements 4.1, 4.5**

Property 5: Phase Validation Success
*For any* completed migration phase, running `yarn type-check`, `yarn lint`, and `yarn build:prod` should all exit with code 0 before proceeding to the next phase
**Validates: Requirements 5.4, 6.1, 6.2, 6.3, 14.1, 14.2, 14.3**

Property 6: Component Classification Correctness
*For any* component in the codebase, if it contains API calls, it should be in `components/business/` or `views/module/components/`; if it only accepts props and emits events, it should be in `components/ui/`; if it's used in only one module, it should be in `views/module/components/`
**Validates: Requirements 7.1, 7.2, 7.3**

Property 7: Dependency Boundary Enforcement
*For any* component or module, UI components should not import any API modules, business components should only import domain APIs (not page-level APIs), and page-level APIs should only be imported within their own module
**Validates: Requirements 8.2, 8.3, 8.4, 8.5, 10.3, 10.5**

Property 8: TypeScript Migration Completeness
*For any* file in `src/api/` or `views/*/api/` directories, the file extension should be `.ts` (not `.js`), and all API functions should have TypeScript type annotations
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

Property 9: Page-Level API Isolation
*For any* page-level API in `views/module/api/`, it should only import from domain APIs in `src/api/`, and should only be imported by files within the same module
**Validates: Requirements 1.5, 10.3, 10.5**

Property 10: UI Component Unified Export
*For any* UI component in `src/components/ui/`, it should be exported from `src/components/ui/index.ts`, and all imports of UI components should use the unified export pattern
**Validates: Requirements 11.1, 11.2, 11.4**

Property 11: No Duplicate Files After Migration
*For any* file that is moved, the file should exist only at the new location and not at the old location after the migration is complete
**Validates: Requirements 6.5**

Property 12: Module API Directory Structure
*For any* module with page-level APIs, the directory `views/module/api/` should exist with an `index.ts` entry point that aggregates exports
**Validates: Requirements 10.2**

Property 13: Domain API Accessibility
*For any* domain API in `src/api/<domain>/`, it should be successfully importable by both view components and business components without errors
**Validates: Requirements 1.4, 8.1**

Property 14: All Routes Accessible
*For any* route defined in the router configuration, the route should be accessible and render without import errors after refactoring
**Validates: Requirements 14.4**

Property 15: No API Calls in UI Components
*For any* component in `src/components/ui/`, the component source code should not contain any imports from `src/api/` or `views/*/api/`
**Validates: Requirements 2.5**

## Error Handling

### File Movement Errors

**Error Type:** File Not Found
- **Scenario:** Source file doesn't exist when attempting to move
- **Handling:** Log error with source path, skip move, mark operation as failed
- **Recovery:** Verify file list before starting phase, provide manual intervention option

**Error Type:** Target Path Conflict
- **Scenario:** Target path already exists with different content
- **Handling:** Log conflict, create backup of existing file, prompt for resolution
- **Recovery:** Manual review and merge if needed, or skip conflicting file

**Error Type:** Permission Denied
- **Scenario:** Insufficient permissions to move file
- **Handling:** Log permission error, skip file, continue with other files
- **Recovery:** Fix permissions and retry phase

### Import Update Errors

**Error Type:** Import Pattern Not Found
- **Scenario:** Expected import pattern doesn't match actual code
- **Handling:** Log warning with file path and expected pattern, skip update
- **Recovery:** Manual review of import statements, update pattern matching logic

**Error Type:** Circular Dependency Created
- **Scenario:** Import update creates circular dependency
- **Handling:** Detect cycle, log error, revert import update
- **Recovery:** Analyze dependency graph, restructure imports to break cycle

**Error Type:** Type Resolution Failure
- **Scenario:** TypeScript cannot resolve types after import update
- **Handling:** Log type error with file and line number, mark validation as failed
- **Recovery:** Manual type definition updates, verify import paths

### Validation Errors

**Error Type:** TypeScript Compilation Failure
- **Scenario:** `yarn type-check` exits with non-zero code
- **Handling:** Capture error output, identify failing files, halt phase progression
- **Recovery:** Fix type errors, re-run validation

**Error Type:** Lint Failure
- **Scenario:** `yarn lint` exits with non-zero code
- **Handling:** Capture lint errors, categorize by severity, halt if errors exist
- **Recovery:** Fix lint errors or update lint rules if appropriate, re-run validation

**Error Type:** Build Failure
- **Scenario:** `yarn build:prod` exits with non-zero code
- **Handling:** Capture build errors, identify root cause, halt phase progression
- **Recovery:** Fix build errors, verify all imports resolve, re-run build

### Phase Rollback

**Error Type:** Phase Validation Failed
- **Scenario:** Any validation check fails after phase completion
- **Handling:** Log all validation errors, initiate rollback procedure
- **Recovery:** Revert all file moves using git, restore original import paths, verify rollback success

**Rollback Procedure:**
1. Identify all file moves in failed phase
2. Use `git revert` or `git reset` to undo moves
3. Restore original import paths from backup
4. Run validation to confirm rollback success
5. Document failure reason for analysis

## Testing Strategy

This refactoring requires a dual testing approach combining automated validation and manual verification.

### Automated Testing

#### Property-Based Tests

Property-based tests will validate universal properties across all files and components. Each test will run with a minimum of 100 iterations to ensure comprehensive coverage.

**Test Configuration:**
- Framework: Vitest with fast-check for property-based testing
- Minimum iterations: 100 per property test
- Tag format: `Feature: frontend-architecture-refactoring, Property {number}: {property_text}`

**Property Test Coverage:**

1. **Import Path Convention Test**
   - Generate random file paths and import statements
   - Verify intra-module imports use relative paths
   - Verify cross-module imports use absolute paths
   - Tag: `Feature: frontend-architecture-refactoring, Property 1: Import path convention consistency`

2. **Import Resolution Test**
   - For all moved files, verify imports resolve correctly
   - Run TypeScript compiler and check for import errors
   - Tag: `Feature: frontend-architecture-refactoring, Property 2: Import correctness after file moves`

3. **Content Preservation Test**
   - For all moved files, compare content (excluding imports)
   - Verify no business logic changes
   - Tag: `Feature: frontend-architecture-refactoring, Property 3: Content preservation during moves`

4. **Component Classification Test**
   - For all components, analyze source code for API calls
   - Verify components are in correct directories based on characteristics
   - Tag: `Feature: frontend-architecture-refactoring, Property 6: Component classification correctness`

5. **Dependency Boundary Test**
   - For all components, analyze import statements
   - Verify UI components don't import APIs
   - Verify business components don't import page-level APIs
   - Tag: `Feature: frontend-architecture-refactoring, Property 7: Dependency boundary enforcement`

6. **TypeScript Migration Test**
   - For all API directories, verify no .js files exist
   - Verify all API functions have type annotations
   - Tag: `Feature: frontend-architecture-refactoring, Property 8: TypeScript migration completeness`

7. **No Duplicate Files Test**
   - For all moved files, verify file exists only at new location
   - Verify old location is empty or deleted
   - Tag: `Feature: frontend-architecture-refactoring, Property 11: No duplicate files after migration`

8. **UI Component API Isolation Test**
   - For all UI components, scan source code for API imports
   - Verify no imports from src/api/ or views/*/api/
   - Tag: `Feature: frontend-architecture-refactoring, Property 15: No API calls in UI components`

#### Unit Tests

Unit tests will verify specific examples and edge cases that complement property-based tests.

**Unit Test Coverage:**

1. **Specific File Move Verification**
   - Test: DictSelect moved to components/business/
   - Test: Common.ts created with expected exports
   - Test: UI components moved to components/ui/

2. **Phase Execution Order**
   - Test: Phase 1 modules (project, protocol, device)
   - Test: Phase 2 modules (system, monitor)
   - Test: Phase 3 modules (tool)

3. **Validation Command Execution**
   - Test: yarn type-check exits with code 0
   - Test: yarn lint exits with code 0
   - Test: yarn build:prod exits with code 0

4. **Module API Structure**
   - Test: views/project/api/index.ts exists
   - Test: views/protocol/api/index.ts exists
   - Test: Each module API has proper exports

5. **UI Component Unified Export**
   - Test: components/ui/index.ts exports all UI components
   - Test: Unified import pattern works correctly

### Manual Verification

Manual verification is required for aspects that cannot be fully automated:

1. **Visual Inspection**
   - Verify UI renders correctly after refactoring
   - Check that all pages load without errors
   - Verify component styling is preserved

2. **Functional Testing**
   - Test critical user workflows (login, CRUD operations)
   - Verify form submissions work correctly
   - Test navigation between pages

3. **Git History Review**
   - Verify files show as renamed in git log
   - Check that commit history is preserved
   - Verify no accidental deletions

4. **Documentation Review**
   - Verify all documentation is updated
   - Check that examples reflect new structure
   - Verify README and guides are accurate

### Testing Execution Plan

**Phase 1 Testing:**
1. Run property-based tests for moved files
2. Run unit tests for Phase 1 modules
3. Execute validation commands (type-check, lint, build)
4. Manual verification of Phase 1 modules
5. Document any issues found

**Phase 2 Testing:**
1. Run property-based tests for all files (Phase 1 + Phase 2)
2. Run unit tests for Phase 2 modules
3. Execute validation commands
4. Manual verification of Phase 2 modules
5. Regression testing of Phase 1 modules

**Phase 3 Testing:**
1. Run property-based tests for entire codebase
2. Run unit tests for Phase 3 modules
3. Execute validation commands
4. Manual verification of Phase 3 modules
5. Full regression testing of all modules
6. Final documentation review

### Test Data Generation

For property-based tests, we'll generate:

- **File Paths:** Random valid file paths within project structure
- **Import Statements:** Various import patterns (relative, absolute, named, default)
- **Component Code:** Synthetic component code with/without API calls
- **API Files:** Synthetic API files with various export patterns

### Success Criteria

All tests must pass before considering the refactoring complete:

- ✅ All property-based tests pass (100+ iterations each)
- ✅ All unit tests pass
- ✅ TypeScript compilation succeeds with no errors
- ✅ ESLint passes with no errors
- ✅ Production build succeeds
- ✅ All routes are accessible
- ✅ Critical workflows function correctly
- ✅ Git history is preserved for all moved files
- ✅ Documentation is updated and accurate

## Implementation Notes

### File Movement Strategy

1. **Use Git Commands:** Always use `git mv` instead of `mv` to preserve history
2. **Batch Operations:** Group related file moves together for atomic commits
3. **Verify Before Move:** Check source file exists and target directory is ready
4. **Update Imports Immediately:** Update imports in the same commit as file move

### Import Path Update Strategy

1. **Pattern Matching:** Use regex to identify import statements
2. **Path Resolution:** Calculate correct relative/absolute paths based on file locations
3. **Batch Updates:** Update all imports for a moved file in one operation
4. **Verification:** Run TypeScript compiler after each batch of updates

### Component Classification Strategy

1. **Static Analysis:** Scan component source code for API imports
2. **Usage Analysis:** Identify which modules use each component
3. **Decision Tree:** Apply classification rules systematically
4. **Documentation:** Document classification decision for each component

### Phase Execution Strategy

1. **Checkpoint Creation:** Create git branch/tag before each phase
2. **Incremental Progress:** Move files in small batches within each phase
3. **Continuous Validation:** Run quick validation checks after each batch
4. **Rollback Readiness:** Keep rollback scripts ready for each phase

### TypeScript Migration Strategy

1. **File Renaming:** Rename .js to .ts first
2. **Type Addition:** Add type annotations incrementally
3. **Compilation Check:** Fix type errors immediately
4. **Interface Extraction:** Extract interfaces for API responses

## Migration Phases Detail

### Phase 1: High Priority Modules (Project, Protocol, Device)

**Objectives:**
- Establish migration pattern as template
- Validate approach with real modules
- Identify and resolve common issues

**Modules:**
- `views/project/` - Project management module
- `views/protocol/` - Protocol management module
- `views/device/` - Device management module

**File Moves:**
1. Create `views/project/api/` for page-level APIs
2. Create `views/protocol/api/` for page-level APIs
3. Create `views/device/api/` for page-level APIs
4. Move project-specific UI components to `components/ui/`
5. Verify business components remain in `components/business/`

**Import Updates:**
1. Update all imports in project module
2. Update all imports in protocol module
3. Update all imports in device module
4. Update cross-module imports from other modules

**Validation:**
- Run full test suite
- Manual testing of project workflows
- Manual testing of protocol workflows
- Manual testing of device workflows

### Phase 2: Medium Priority Modules (System, Monitor)

**Objectives:**
- Apply lessons learned from Phase 1
- Migrate larger, more complex modules
- Ensure system stability

**Modules:**
- `views/system/` - System management module (user, role, menu, dept, etc.)
- `views/monitor/` - Monitoring module (logs, online users, etc.)

**File Moves:**
1. Create `views/system/api/` for page-level APIs
2. Create `views/monitor/api/` for page-level APIs
3. Move remaining UI components to `components/ui/`
4. Consolidate common APIs to `src/api/common.ts`

**Import Updates:**
1. Update all imports in system module
2. Update all imports in monitor module
3. Update imports to use `src/api/common.ts`
4. Update cross-module imports

**Validation:**
- Run full test suite
- Manual testing of user management
- Manual testing of role/permission management
- Manual testing of monitoring features

### Phase 3: Low Priority Modules (Tool)

**Objectives:**
- Complete migration of remaining modules
- Final cleanup and optimization
- Comprehensive validation

**Modules:**
- `views/tool/` - Tool module (code generation, etc.)

**File Moves:**
1. Create `views/tool/api/` for page-level APIs
2. Final UI component organization
3. Create `components/ui/index.ts` unified export

**Import Updates:**
1. Update all imports in tool module
2. Update all imports to use unified UI component export
3. Final import path consistency check

**Validation:**
- Run full test suite
- Manual testing of code generation
- Full regression testing of all modules
- Performance testing
- Documentation review

## Rollback Procedures

### Phase Rollback

If a phase fails validation:

1. **Identify Failure Point:**
   ```bash
   # Check validation output
   yarn type-check 2>&1 | tee type-check-errors.log
   yarn lint 2>&1 | tee lint-errors.log
   yarn build:prod 2>&1 | tee build-errors.log
   ```

2. **Revert File Moves:**
   ```bash
   # Reset to pre-phase state
   git reset --hard <phase-start-tag>
   ```

3. **Verify Rollback:**
   ```bash
   # Confirm original state restored
   yarn type-check
   yarn lint
   yarn build:prod
   ```

4. **Document Failure:**
   - Record error messages
   - Identify root cause
   - Plan corrective action

### Partial Rollback

If only specific files need rollback:

1. **Identify Problem Files:**
   - Review error logs
   - Identify files causing issues

2. **Revert Specific Files:**
   ```bash
   # Revert individual files
   git checkout <phase-start-tag> -- path/to/file
   ```

3. **Update Related Imports:**
   - Restore imports for reverted files
   - Update dependent files

4. **Validate Partial Rollback:**
   - Run validation commands
   - Verify system stability

## Success Metrics

### Quantitative Metrics

1. **File Movement Success Rate:** 100% of planned file moves completed
2. **Import Update Success Rate:** 100% of imports updated correctly
3. **Validation Pass Rate:** 100% of validation checks pass
4. **Test Coverage:** All property-based tests pass with 100+ iterations
5. **Build Success:** Production build completes without errors
6. **Type Safety:** Zero TypeScript errors
7. **Code Quality:** Zero ESLint errors

### Qualitative Metrics

1. **Code Organization:** Clear separation of concerns
2. **Developer Experience:** Easier to locate and understand code
3. **Maintainability:** Reduced coupling, clearer dependencies
4. **Documentation Quality:** Comprehensive and accurate documentation
5. **Git History:** Preserved history for all moved files

## Conclusion

This design provides a comprehensive approach to refactoring the frontend architecture through a phased migration strategy. The key principles are:

1. **Structural Changes Only:** Move files without modifying business logic
2. **Clear Boundaries:** Enforce dependency boundaries through directory structure
3. **Phased Execution:** Migrate in three phases with validation between each
4. **Comprehensive Testing:** Use property-based tests and unit tests for validation
5. **Rollback Capability:** Maintain ability to rollback failed phases
6. **Documentation:** Keep documentation updated throughout the process

The design ensures that the refactoring maintains system functionality while improving code organization, maintainability, and developer experience.
