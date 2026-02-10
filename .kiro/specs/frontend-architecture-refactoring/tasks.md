# Implementation Plan: Frontend Architecture Refactoring

## Overview

This implementation plan outlines the tasks for refactoring the frontend architecture of RuoYi-Vue3-FastAPI. The refactoring is executed in three phases, with each phase focusing on specific modules. The approach is to move files without modifying business logic, update import paths, and validate after each phase.

## Tasks

- [ ] 1. Pre-Migration Setup and Preparation
  - Create git branch for refactoring work
  - Create backup tags for rollback capability
  - Set up validation scripts for automated testing
  - Document current directory structure for reference
  - _Requirements: 4.5, 5.5_

- [ ] 2. Create Target Directory Structure
  - [ ] 2.1 Create `src/components/ui/` directory
    - Create directory structure for UI components
    - _Requirements: 2.1_
  
  - [ ] 2.2 Create `src/api/common.ts` file
    - Create file for global common APIs
    - _Requirements: 1.2, 13.1_
  
  - [ ] 2.3 Create module API directories for Phase 1
    - Create `views/project/api/` directory
    - Create `views/protocol/api/` directory
    - Create `views/device/api/` directory
    - _Requirements: 1.3, 10.1_

- [ ] 3. Phase 1: Migrate Project Module (Template Module)
  - [ ] 3.1 Identify and classify project module components
    - Analyze components for API calls
    - Determine UI vs business vs module classification
    - Document classification decisions
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 3.2 Move project module UI components to `src/components/ui/`
    - Use `git mv` to move identified UI components
    - Preserve git history during moves
    - _Requirements: 2.1, 4.1, 4.5_
  
  - [ ] 3.3 Update import paths in project module
    - Update imports for moved UI components
    - Apply relative path convention for intra-module imports
    - Apply absolute path convention for cross-module imports
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 3.4 Create page-level APIs for project module
    - Create `views/project/api/index.ts` entry point
    - Implement page-level API encapsulations
    - Ensure only domain API imports
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 3.5 Convert project API files from .js to .ts
    - Rename .js files to .ts in `src/api/project/`
    - Add TypeScript type annotations
    - Fix any type errors
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 3.6 Write property test for project module import paths
    - **Property 1: Import Path Convention Consistency**
    - **Validates: Requirements 3.1, 3.2, 3.5**
  
  - [ ] 3.7 Write property test for project module content preservation
    - **Property 3: Content Preservation During Moves**
    - **Validates: Requirements 4.2, 4.3, 4.4**
  
  - [ ] 3.8 Validate Phase 1 - Project Module
    - Run `yarn type-check` and verify success
    - Run `yarn lint` and verify success
    - Run `yarn build:prod` and verify success
    - _Requirements: 6.1, 6.2, 6.3, 14.1, 14.2, 14.3_

- [ ] 4. Checkpoint - Phase 1 Project Module Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Phase 1: Migrate Protocol Module
  - [ ] 5.1 Identify and classify protocol module components
    - Analyze components for API calls
    - Determine component classifications
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 5.2 Move protocol module UI components
    - Use `git mv` to move UI components
    - _Requirements: 2.1, 4.1_
  
  - [ ] 5.3 Update import paths in protocol module
    - Update all import statements
    - Apply path conventions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 5.4 Create page-level APIs for protocol module
    - Create `views/protocol/api/index.ts`
    - Implement page-level encapsulations
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 5.5 Convert protocol API files to TypeScript
    - Rename .js to .ts in `src/api/protocol/`
    - Add type annotations
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 5.6 Validate Phase 1 - Protocol Module
    - Run validation commands
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 6. Phase 1: Migrate Device Module
  - [ ] 6.1 Identify and classify device module components
    - Analyze components for API calls
    - Determine component classifications
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 6.2 Move device module UI components
    - Use `git mv` to move UI components
    - _Requirements: 2.1, 4.1_
  
  - [ ] 6.3 Update import paths in device module
    - Update all import statements
    - Apply path conventions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 6.4 Create page-level APIs for device module
    - Create `views/device/api/index.ts`
    - Implement page-level encapsulations
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 6.5 Convert device API files to TypeScript
    - Rename .js to .ts in `src/api/device/`
    - Add type annotations
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 6.6 Validate Phase 1 - Device Module
    - Run validation commands
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 7. Phase 1: Move DictSelect to Business Components
  - [ ] 7.1 Move DictSelect component
    - Use `git mv` to move from `src/components/DictSelect` to `src/components/business/DictSelect`
    - _Requirements: 2.2, 4.1_
  
  - [ ] 7.2 Update all imports of DictSelect
    - Find all files importing DictSelect
    - Update import paths to new location
    - _Requirements: 3.3_
  
  - [ ] 7.3 Write property test for DictSelect API usage
    - **Property 7: Dependency Boundary Enforcement**
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.5**

- [ ] 8. Phase 1: Final Validation and Testing
  - [ ] 8.1 Write property test for component classification
    - **Property 6: Component Classification Correctness**
    - **Validates: Requirements 7.1, 7.2, 7.3**
  
  - [ ] 8.2 Write property test for TypeScript migration
    - **Property 8: TypeScript Migration Completeness**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
  
  - [ ] 8.3 Write property test for no duplicate files
    - **Property 11: No Duplicate Files After Migration**
    - **Validates: Requirements 6.5**
  
  - [ ] 8.4 Run comprehensive Phase 1 validation
    - Execute `yarn type-check`
    - Execute `yarn lint`
    - Execute `yarn build:prod`
    - Verify all Phase 1 modules function correctly
    - _Requirements: 5.4, 6.1, 6.2, 6.3_

- [ ] 9. Checkpoint - Phase 1 Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Phase 2: Setup and Preparation
  - [ ] 10.1 Create module API directories for Phase 2
    - Create `views/system/api/` directory
    - Create `views/monitor/api/` directory
    - _Requirements: 1.3, 10.1_
  
  - [ ] 10.2 Create git checkpoint for Phase 2
    - Create tag for Phase 1 completion
    - Create branch for Phase 2 work
    - _Requirements: 5.5_

- [ ] 11. Phase 2: Migrate System Module
  - [ ] 11.1 Identify and classify system module components
    - Analyze all system module components
    - Determine classifications
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 11.2 Move system module UI components
    - Use `git mv` to move UI components
    - _Requirements: 2.1, 4.1_
  
  - [ ] 11.3 Update import paths in system module
    - Update all import statements
    - Apply path conventions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 11.4 Create page-level APIs for system module
    - Create `views/system/api/index.ts`
    - Implement page-level encapsulations
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 11.5 Convert system API files to TypeScript
    - Rename .js to .ts in `src/api/system/`
    - Add type annotations
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 11.6 Validate Phase 2 - System Module
    - Run validation commands
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 12. Phase 2: Migrate Monitor Module
  - [ ] 12.1 Identify and classify monitor module components
    - Analyze monitor module components
    - Determine classifications
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 12.2 Move monitor module UI components
    - Use `git mv` to move UI components
    - _Requirements: 2.1, 4.1_
  
  - [ ] 12.3 Update import paths in monitor module
    - Update all import statements
    - Apply path conventions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 12.4 Create page-level APIs for monitor module
    - Create `views/monitor/api/index.ts`
    - Implement page-level encapsulations
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 12.5 Convert monitor API files to TypeScript
    - Rename .js to .ts in `src/api/monitor/`
    - Add type annotations
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 12.6 Validate Phase 2 - Monitor Module
    - Run validation commands
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 13. Phase 2: Consolidate Common APIs
  - [ ] 13.1 Extract dictionary APIs to common.ts
    - Move dictionary-related functions to `src/api/common.ts`
    - _Requirements: 13.2_
  
  - [ ] 13.2 Extract user list APIs to common.ts
    - Move user list functions to `src/api/common.ts`
    - _Requirements: 13.3_
  
  - [ ] 13.3 Extract department list APIs to common.ts
    - Move department list functions to `src/api/common.ts`
    - _Requirements: 13.4_
  
  - [ ] 13.4 Update all modules to import from common.ts
    - Find all usages of moved APIs
    - Update import statements
    - _Requirements: 13.5_
  
  - [ ] 13.5 Write property test for common API imports
    - **Property 13: Domain API Accessibility**
    - **Validates: Requirements 1.4, 8.1**

- [ ] 14. Phase 2: Final Validation
  - [ ] 14.1 Write property test for page-level API isolation
    - **Property 9: Page-Level API Isolation**
    - **Validates: Requirements 1.5, 10.3, 10.5**
  
  - [ ] 14.2 Run comprehensive Phase 2 validation
    - Execute `yarn type-check`
    - Execute `yarn lint`
    - Execute `yarn build:prod`
    - Verify all Phase 2 modules function correctly
    - _Requirements: 5.4, 6.1, 6.2, 6.3_
  
  - [ ] 14.3 Regression test Phase 1 modules
    - Verify Phase 1 modules still work correctly
    - Test cross-module interactions
    - _Requirements: 14.4_

- [ ] 15. Checkpoint - Phase 2 Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Phase 3: Setup and Preparation
  - [ ] 16.1 Create module API directory for Phase 3
    - Create `views/tool/api/` directory
    - _Requirements: 1.3, 10.1_
  
  - [ ] 16.2 Create git checkpoint for Phase 3
    - Create tag for Phase 2 completion
    - Create branch for Phase 3 work
    - _Requirements: 5.5_

- [ ] 17. Phase 3: Migrate Tool Module
  - [ ] 17.1 Identify and classify tool module components
    - Analyze tool module components
    - Determine classifications
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [ ] 17.2 Move tool module UI components
    - Use `git mv` to move UI components
    - _Requirements: 2.1, 4.1_
  
  - [ ] 17.3 Update import paths in tool module
    - Update all import statements
    - Apply path conventions
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 17.4 Create page-level APIs for tool module
    - Create `views/tool/api/index.ts`
    - Implement page-level encapsulations
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 17.5 Convert tool API files to TypeScript
    - Rename .js to .ts in `src/api/tool/`
    - Add type annotations
    - _Requirements: 9.1, 9.3, 9.4_
  
  - [ ] 17.6 Validate Phase 3 - Tool Module
    - Run validation commands
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 18. Phase 3: Create UI Component Unified Export
  - [ ] 18.1 Create `src/components/ui/index.ts`
    - Create file with exports for all UI components
    - _Requirements: 2.4, 11.1_
  
  - [ ] 18.2 Update all UI component imports to use unified export
    - Find all imports of UI components
    - Update to use `import { Component } from '@/components/ui'` pattern
    - _Requirements: 11.2, 11.4_
  
  - [ ] 18.3 Write property test for UI component unified export
    - **Property 10: UI Component Unified Export**
    - **Validates: Requirements 11.1, 11.2, 11.4**

- [ ] 19. Phase 3: Final Cleanup and Validation
  - [ ] 19.1 Verify no duplicate files exist
    - Check that all old file locations are empty
    - Verify files only exist at new locations
    - _Requirements: 6.5_
  
  - [ ] 19.2 Verify all moved files are accessible
    - Check that all target paths exist
    - Verify files are readable
    - _Requirements: 6.4_
  
  - [ ] 19.3 Write property test for import resolution
    - **Property 2: Import Correctness After File Moves**
    - **Validates: Requirements 3.3, 3.4**
  
  - [ ] 19.4 Write property test for UI component API isolation
    - **Property 15: No API Calls in UI Components**
    - **Validates: Requirements 2.5**
  
  - [ ] 19.5 Write property test for git history preservation
    - **Property 4: Git History Preservation**
    - **Validates: Requirements 4.1, 4.5**

- [ ] 20. Phase 3: Comprehensive Final Validation
  - [ ] 20.1 Run full test suite
    - Execute all property-based tests
    - Execute all unit tests
    - _Requirements: 5.4_
  
  - [ ] 20.2 Run all validation commands
    - Execute `yarn type-check`
    - Execute `yarn lint`
    - Execute `yarn build:prod`
    - _Requirements: 6.1, 6.2, 6.3, 14.1, 14.2, 14.3_
  
  - [ ] 20.3 Verify all routes are accessible
    - Test navigation to all routes
    - Verify no import errors
    - _Requirements: 14.4_
  
  - [ ] 20.4 Write property test for route accessibility
    - **Property 14: All Routes Accessible**
    - **Validates: Requirements 14.4**
  
  - [ ] 20.5 Full regression testing
    - Test all Phase 1 modules
    - Test all Phase 2 modules
    - Test all Phase 3 modules
    - Test cross-module interactions
    - _Requirements: 14.4_

- [ ] 21. Documentation and Finalization
  - [ ] 21.1 Document final directory structure
    - Create documentation showing new structure
    - _Requirements: 15.1_
  
  - [ ] 21.2 Document component classification rules
    - Write guide for classifying components
    - _Requirements: 7.4, 15.2_
  
  - [ ] 21.3 Document import path conventions
    - Write guide for import path usage
    - _Requirements: 15.3_
  
  - [ ] 21.4 Document dependency boundary rules
    - Write guide for dependency boundaries
    - _Requirements: 15.4_
  
  - [ ] 21.5 Provide examples of correct placement
    - Create examples for component placement
    - Create examples for API placement
    - _Requirements: 15.5_

- [ ] 22. Final Checkpoint - Refactoring Complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive refactoring with full test coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation between phases
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All file moves must use `git mv` to preserve history
- Import path updates must happen in the same commit as file moves
- Validation must pass before proceeding to next phase
- Rollback capability is maintained through git tags at each phase boundary
