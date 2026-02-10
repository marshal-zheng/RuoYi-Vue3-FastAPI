# Requirements Document

## Introduction

This document specifies the requirements for a one-time frontend architecture refactoring of the RuoYi-Vue3-FastAPI project. The refactoring aims to establish clear directory semantics, enforce dependency boundaries, and eliminate path confusion and responsibility ambiguity. This is a structural reorganization that moves files without modifying business logic.

## Glossary

- **Frontend_System**: The Vue 3 frontend application located in `ruoyi-fastapi-frontend/`
- **API_Layer**: The data access layer that communicates with backend services
- **Domain_API**: API modules in `src/api/<domain>/` that correspond to backend domains
- **Page_Level_API**: API modules in `views/module/api/` that encapsulate domain APIs for specific pages
- **UI_Component**: Pure presentational components that only accept props and emit events
- **Business_Component**: Components that can call APIs and contain business logic
- **Module_Component**: Components private to a specific view module
- **Import_Path**: The path used in import statements to reference modules
- **File_Move_Operation**: Moving files using `git mv` or `mv` commands without modifying content

## Requirements

### Requirement 1: API Layer Reorganization

**User Story:** As a developer, I want a clear separation between domain APIs and page-level APIs, so that I can understand which APIs are reusable across modules and which are page-specific.

#### Acceptance Criteria

1. THE Frontend_System SHALL maintain `src/api/<domain>/` as Domain_API directories
2. THE Frontend_System SHALL create `src/api/common.ts` for global common APIs (dictionaries, user lists, department lists)
3. WHEN a module needs page-specific API encapsulation, THE Frontend_System SHALL create `views/module/api/` directories
4. THE Frontend_System SHALL ensure Domain_API can be used by both views and Business_Components
5. THE Frontend_System SHALL ensure Page_Level_API is only used within its own module

### Requirement 2: Component Layer Reorganization

**User Story:** As a developer, I want components organized by their responsibility level, so that I can quickly identify pure UI components versus business logic components.

#### Acceptance Criteria

1. THE Frontend_System SHALL move all pure UI components to `src/components/ui/`
2. THE Frontend_System SHALL move `DictSelect` from `src/components/DictSelect` to `src/components/business/DictSelect`
3. THE Frontend_System SHALL maintain existing Business_Components in `src/components/business/` (Protocol, Dag, Device, Monitor)
4. THE Frontend_System SHALL create `src/components/ui/index.ts` as a unified export point
5. WHEN a component is classified as UI_Component, THE Frontend_System SHALL ensure it does not call any API

### Requirement 3: Import Path Updates

**User Story:** As a developer, I want consistent import path conventions, so that I can easily understand module dependencies.

#### Acceptance Criteria

1. WHEN importing within the same module, THE Frontend_System SHALL use relative paths (e.g., `./api/project`)
2. WHEN importing across modules, THE Frontend_System SHALL use absolute paths (e.g., `@/api/project`)
3. WHEN a file is moved, THE Frontend_System SHALL update all import statements that reference it
4. THE Frontend_System SHALL ensure no broken imports exist after refactoring
5. THE Frontend_System SHALL maintain consistent path conventions throughout the codebase

### Requirement 4: File Movement Without Logic Changes

**User Story:** As a developer, I want files moved without modifying their internal logic, so that I can verify the refactoring through structural changes only.

#### Acceptance Criteria

1. THE Frontend_System SHALL use File_Move_Operations to relocate files
2. THE Frontend_System SHALL NOT modify business logic during file moves
3. THE Frontend_System SHALL NOT reimplement any existing functionality
4. THE Frontend_System SHALL preserve all file contents except import paths
5. WHEN moving files, THE Frontend_System SHALL maintain git history through `git mv` commands

### Requirement 5: Phased Migration Execution

**User Story:** As a developer, I want the refactoring executed in phases, so that I can validate each phase before proceeding.

#### Acceptance Criteria

1. THE Frontend_System SHALL execute Phase 1 migrations first (project, protocol, device modules)
2. THE Frontend_System SHALL execute Phase 2 migrations after Phase 1 validation (system, monitor modules)
3. THE Frontend_System SHALL execute Phase 3 migrations after Phase 2 validation (tool module)
4. WHEN a phase is complete, THE Frontend_System SHALL pass all validation checks before proceeding
5. THE Frontend_System SHALL allow rollback of individual phases if validation fails

### Requirement 6: Validation and Quality Assurance

**User Story:** As a developer, I want automated validation after each phase, so that I can ensure the refactoring maintains code quality.

#### Acceptance Criteria

1. WHEN a phase completes, THE Frontend_System SHALL run TypeScript type checking without errors
2. WHEN a phase completes, THE Frontend_System SHALL run ESLint without errors
3. WHEN a phase completes, THE Frontend_System SHALL build successfully for production
4. THE Frontend_System SHALL ensure all moved files are accessible at their new locations
5. THE Frontend_System SHALL ensure no duplicate files exist after migration

### Requirement 7: Component Classification Rules

**User Story:** As a developer, I want clear rules for classifying components, so that I can place new components in the correct directory.

#### Acceptance Criteria

1. WHEN a component calls any API, THE Frontend_System SHALL classify it as Business_Component
2. WHEN a component only accepts props and emits events, THE Frontend_System SHALL classify it as UI_Component
3. WHEN a component is used in only one module, THE Frontend_System SHALL classify it as Module_Component
4. THE Frontend_System SHALL document component classification rules in the codebase
5. THE Frontend_System SHALL ensure Business_Components can only call Domain_API, not Page_Level_API

### Requirement 8: Dependency Boundary Enforcement

**User Story:** As a developer, I want enforced dependency boundaries, so that I can prevent circular dependencies and maintain clean architecture.

#### Acceptance Criteria

1. THE Frontend_System SHALL allow views to call both Page_Level_API and Domain_API
2. THE Frontend_System SHALL allow Business_Components to call Domain_API only
3. THE Frontend_System SHALL prevent UI_Components from calling any API
4. THE Frontend_System SHALL prevent Business_Components from calling Page_Level_API
5. THE Frontend_System SHALL prevent cross-module imports of Page_Level_API

### Requirement 9: TypeScript Migration for API Files

**User Story:** As a developer, I want all API files in TypeScript, so that I can benefit from type safety and better IDE support.

#### Acceptance Criteria

1. THE Frontend_System SHALL convert all `.js` files in `src/api/` to `.ts`
2. THE Frontend_System SHALL ensure all files in `views/*/api/` are `.ts`
3. THE Frontend_System SHALL update import statements to reference `.ts` extensions where needed
4. THE Frontend_System SHALL maintain type definitions for all API functions
5. THE Frontend_System SHALL prohibit new `.js` files in API directories

### Requirement 10: Module-Specific API Creation

**User Story:** As a developer, I want to create page-level APIs for complex page logic, so that I can encapsulate multiple domain API calls.

#### Acceptance Criteria

1. WHEN a page needs to combine multiple Domain_API calls, THE Frontend_System SHALL create `views/module/api/` directory
2. THE Frontend_System SHALL create `views/module/api/index.ts` as the module API entry point
3. THE Frontend_System SHALL ensure Page_Level_API only imports from Domain_API
4. THE Frontend_System SHALL document the purpose of each Page_Level_API function
5. THE Frontend_System SHALL prevent Page_Level_API from being imported by other modules

### Requirement 11: UI Component Unified Export

**User Story:** As a developer, I want a single import point for UI components, so that I can import multiple components efficiently.

#### Acceptance Criteria

1. THE Frontend_System SHALL create `src/components/ui/index.ts` that exports all UI components
2. THE Frontend_System SHALL allow importing UI components using `import { Component } from '@/components/ui'`
3. THE Frontend_System SHALL maintain individual component directories under `src/components/ui/`
4. THE Frontend_System SHALL update all existing imports to use the unified export
5. THE Frontend_System SHALL document the unified export pattern in component documentation

### Requirement 12: Migration Priority Ordering

**User Story:** As a developer, I want migrations prioritized by module complexity, so that I can use simpler modules as templates for more complex ones.

#### Acceptance Criteria

1. THE Frontend_System SHALL migrate project management module first as a template
2. THE Frontend_System SHALL migrate protocol management module second
3. THE Frontend_System SHALL migrate device management module third
4. THE Frontend_System SHALL migrate system management and monitor modules in Phase 2
5. THE Frontend_System SHALL migrate tool module last in Phase 3

### Requirement 13: Common API Extraction

**User Story:** As a developer, I want commonly used APIs centralized, so that I can avoid duplicating API calls across modules.

#### Acceptance Criteria

1. THE Frontend_System SHALL create `src/api/common.ts` for global common APIs
2. THE Frontend_System SHALL move dictionary-related APIs to `src/api/common.ts`
3. THE Frontend_System SHALL move user list APIs to `src/api/common.ts`
4. THE Frontend_System SHALL move department list APIs to `src/api/common.ts`
5. THE Frontend_System SHALL update all modules to import from `src/api/common.ts`

### Requirement 14: Build and Test Verification

**User Story:** As a developer, I want comprehensive build and test verification, so that I can ensure the refactoring doesn't break functionality.

#### Acceptance Criteria

1. WHEN validation runs, THE Frontend_System SHALL execute `yarn type-check` successfully
2. WHEN validation runs, THE Frontend_System SHALL execute `yarn lint` successfully
3. WHEN validation runs, THE Frontend_System SHALL execute `yarn build:prod` successfully
4. THE Frontend_System SHALL verify that all routes are accessible after refactoring
5. THE Frontend_System SHALL verify that critical user workflows function correctly

### Requirement 15: Documentation and Migration Guide

**User Story:** As a developer, I want documentation of the new structure, so that I can understand where to place new code.

#### Acceptance Criteria

1. THE Frontend_System SHALL document the final directory structure
2. THE Frontend_System SHALL document component classification rules
3. THE Frontend_System SHALL document import path conventions
4. THE Frontend_System SHALL document dependency boundary rules
5. THE Frontend_System SHALL provide examples of correct component and API placement
