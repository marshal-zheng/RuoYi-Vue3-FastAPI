# DAG Component Refactoring - Requirements Document

## Introduction

This document specifies requirements for refactoring the DAG (Directed Acyclic Graph) visualization component in the RuoYi-Vue3-FastAPI system. The DAG component is a mission-critical graph editor built on AntV X6, enabling users to create, visualize, and manage complex node-edge relationships for device topology, workflow design, and data flow modeling.

**Current State Analysis:**
- **Component Size**: index.vue contains ~850 lines (template + script + style)
- **Architecture**: Monolithic component with embedded business logic
- **Technology**: Pure JavaScript without type safety
- **Performance**: Layout algorithm performs full recalculation on every change
- **State Management**: Scattered across component refs, X6 internal state, and parent components
- **Reusability**: Tightly coupled subcomponents limit independent usage

**Business Impact:**
- Used in 3+ critical features: Project Topology, Device Management, Simulation Visualization
- Handles graphs with 50-200 nodes in production
- Performance degradation reported with 100+ nodes
- Maintenance velocity decreased due to code complexity

## Glossary

- **DAG Component**: The graph visualization component at `ruoyi-fastapi-frontend/src/components/business/Dag/`
- **X6 Graph Engine**: AntV X6 - the underlying canvas-based graph rendering library
- **XFlow**: Vue 3 wrapper layer providing reactive integration with X6
- **Layout Algorithm**: Dagre-inspired topological sorting algorithm that positions nodes in hierarchical layers
- **Composable**: Vue 3 Composition API function encapsulating reusable stateful logic
- **Graph Instance**: The X6 Graph object managing the canvas, nodes, edges, and interactions
- **Matrix View**: Alternative tree-table representation synchronized with graph data
- **Port**: Connection anchor point on a node where edges attach (top/bottom/left/right)
- **Smart Port Management**: Algorithm that shows/hides ports based on layout direction and connection state
- **Snapline**: Visual alignment guide displayed during node dragging
- **DagDnd**: Drag-and-drop sidebar component for adding operator nodes to canvas
- **Operator**: Reusable node template that can be instantiated via drag-and-drop
- **Device Node**: Specialized node type representing hardware devices with multiple typed ports
- **Topological Sort**: Algorithm ensuring DAG property by detecting and preventing cycles
- **Batch Update**: X6 optimization technique grouping multiple DOM operations into single render cycle

## Requirements

### Requirement 1: Component Architecture Decomposition

**User Story:** As a developer maintaining the DAG component, I want the codebase organized into focused, single-responsibility modules, so that I can understand, modify, and test each concern independently without risking unintended side effects.

#### Acceptance Criteria

1. WHEN the index.vue file contains more than 400 lines of script logic THEN the system SHALL extract layout management into a dedicated useGraphLayout composable
2. WHEN event handling logic exceeds 150 lines THEN the system SHALL extract it into a useGraphEvents composable that manages node clicks, double-clicks, edge connections, and keyboard shortcuts
3. WHEN import/export functionality is needed THEN the system SHALL provide a useGraphIO composable handling PNG, PDF, and Xmind export with consistent error handling
4. WHEN graph-to-business data synchronization is required THEN the system SHALL provide a useGraphSync composable managing bidirectional data flow and format transformations
5. WHEN fullscreen and toolbar interactions are needed THEN the system SHALL extract them into a useGraphUI composable managing UI state and browser APIs

### Requirement 2: Type Safety and Developer Experience

**User Story:** As a developer integrating the DAG component, I want comprehensive TypeScript definitions with IntelliSense support, so that I can catch errors at compile time and discover available APIs without reading documentation.

#### Acceptance Criteria

1. WHEN defining node data structures THEN the system SHALL provide a TypeScript interface `NodeData` with discriminated union types for different node kinds (dag-node, device-port-node, leaf-node, branch-node)
2. WHEN defining edge data structures THEN the system SHALL provide a TypeScript interface `EdgeData` with required fields (id, sourceNodeId, targetNodeId) and optional styling properties
3. WHEN configuring the graph THEN the system SHALL provide a TypeScript interface `GraphConfig` with all 20+ configuration options properly typed and documented
4. WHEN passing operators to DagDnd THEN the system SHALL provide a TypeScript interface `OperatorData` supporting both simple ({name, value}) and complex ({name, value, ports[], deviceType}) formats
5. WHEN the component emits events THEN the system SHALL use TypeScript to define event payload types ensuring type-safe event handlers

### Requirement 3: Layout Algorithm Performance Optimization

**User Story:** As a user working with production-scale graphs (100-200 nodes), I want layout calculations to complete within 1 second and UI interactions to remain responsive, so that I can work efficiently without experiencing lag or freezing.

#### Acceptance Criteria

1. WHEN the graph contains 100 nodes THEN the layout calculation SHALL complete within 1000ms measured from layout trigger to final node positioning
2. WHEN switching layout direction (horizontal ↔ vertical) THEN the system SHALL use incremental updates preserving unchanged node positions rather than full recalculation
3. WHEN the smartPortManagement function processes ports THEN the system SHALL reduce iteration count by caching port groups and using Map lookups instead of array iterations
4. WHEN batch updating node positions THEN the system SHALL use X6's batchUpdate API to group all DOM operations into a single repaint cycle
5. WHEN calculating node positions THEN the system SHALL memoize intermediate results (level assignments, cross-axis sizes) to avoid redundant calculations during the same layout pass

### Requirement 4: State Management Architecture

**User Story:** As a developer debugging data synchronization issues, I want a single source of truth for graph state with clear data flow, so that I can trace how changes propagate and identify the root cause of bugs.

#### Acceptance Criteria

1. WHEN graph data changes from any source THEN the system SHALL update through a centralized reactive state object serving as the single source of truth
2. WHEN the matrix view modifies node properties THEN the system SHALL emit a state change event that the graph view observes and applies automatically
3. WHEN the graph view adds/removes nodes THEN the system SHALL emit a state change event that the matrix view observes and reflects automatically
4. WHEN multiple components need read access to graph state THEN the system SHALL provide a readonly reactive reference preventing accidental mutations
5. WHEN state changes need to be persisted THEN the system SHALL provide a serialization method producing a clean JSON structure without internal X6 metadata

### Requirement 5: Configuration Externalization and Theming

**User Story:** As a product designer customizing the DAG component for different use cases, I want all visual styling and behavior parameters defined in configuration files, so that I can adjust appearance without modifying component code.

#### Acceptance Criteria

1. WHEN node visual styles are defined THEN the system SHALL store colors, borders, shadows, and spacing in CSS custom properties (--dag-node-bg, --dag-node-border, etc.)
2. WHEN port visibility rules are needed THEN the system SHALL extract the logic from layout.js into a declarative configuration object mapping layout directions to visible port groups
3. WHEN edge styles vary by state THEN the system SHALL use the existing edgeConfig.js pattern with state-based style objects (normal, hover, selected, connecting)
4. WHEN the DagDnd component renders operators THEN the system SHALL accept a template prop allowing custom HTML/Vue component rendering per operator type
5. WHEN theme switching is required THEN the system SHALL support CSS variable overrides at the component root enabling light/dark/custom themes without code changes

### Requirement 6: Layout Algorithm Correctness and Robustness

**User Story:** As a user creating complex graph structures, I want the layout algorithm to handle all valid DAG topologies correctly, so that my graphs are always readable and properly organized regardless of complexity.

#### Acceptance Criteria

1. WHEN the graph contains cycles (despite validation) THEN the layout algorithm SHALL detect them using the existing isAcyclic check and place cyclic nodes in a separate layer with a warning indicator
2. WHEN nodes have varying widths/heights THEN the layout algorithm SHALL calculate cross-axis spacing using actual node dimensions rather than assuming uniform sizes
3. WHEN a node has multiple parents (diamond pattern) THEN the layout algorithm SHALL position it in the layer immediately after the latest parent to minimize edge crossings
4. WHEN the graph contains disconnected subgraphs THEN the layout algorithm SHALL process each connected component independently and arrange them horizontally with configurable spacing
5. WHEN port positions are calculated THEN the system SHALL ensure ports are centered on their respective edges (top/bottom at 50% width, left/right at 50% height) using the existing getPortPositionConfig pattern

### Requirement 7: Component Reusability and Composition

**User Story:** As a developer building new features, I want to reuse DAG subcomponents independently, so that I can compose custom graph editors without duplicating code or fighting tight coupling.

#### Acceptance Criteria

1. WHEN the DagDnd component is needed in isolation THEN the system SHALL allow it to function independently by accepting a graph instance ref and emitting drag events without requiring the full DAG page context
2. WHEN custom context menu logic is needed THEN the system SHALL accept a customMenuHandler prop receiving (node, position, graph) and returning menu items, enabling full menu customization
3. WHEN custom node rendering is required THEN the system SHALL support registering custom X6 shapes via the existing registerDagShapes pattern without modifying core component code
4. WHEN custom connection validation is needed THEN the system SHALL accept a validateConnection prop allowing business logic to approve/reject connections beyond the built-in cycle detection
5. WHEN the graph control toolbar is needed elsewhere THEN the system SHALL extract DagGraphControl into a standalone component accepting only a graph instance prop

### Requirement 8: Testing Infrastructure and Quality Assurance

**User Story:** As a developer refactoring the DAG component, I want comprehensive automated tests covering core algorithms and interactions, so that I can refactor confidently knowing regressions will be caught immediately.

#### Acceptance Criteria

1. WHEN the layout algorithm is modified THEN the system SHALL have unit tests verifying correct node positioning for standard topologies (linear chain, binary tree, diamond, disconnected components)
2. WHEN graph constraint functions are changed THEN the system SHALL have unit tests verifying cycle detection (willCreateCycle) and reachability (canReach) with edge cases (self-loops, transitive cycles)
3. WHEN data transformation occurs THEN the system SHALL have unit tests verifying graph-to-matrix and matrix-to-graph conversions preserve all node properties and parent-child relationships
4. WHEN composables are created THEN the system SHALL have unit tests using @vue/test-utils to verify reactive behavior, lifecycle hooks, and cleanup
5. WHEN critical user workflows are implemented THEN the system SHALL have integration tests using Vitest + Testing Library verifying end-to-end scenarios (drag node, connect nodes, export graph)

### Requirement 9: Performance Monitoring and Optimization

**User Story:** As a system administrator monitoring production performance, I want the DAG component to expose performance metrics, so that I can identify bottlenecks and optimize based on real usage patterns.

#### Acceptance Criteria

1. WHEN layout calculations execute THEN the system SHALL measure and log execution time using performance.mark/measure with labels (layout-start, layout-end, layout-duration)
2. WHEN the graph contains more than 50 nodes THEN the system SHALL log a performance warning if layout takes longer than 500ms
3. WHEN smartPortManagement processes ports THEN the system SHALL count iterations and log a warning if any node requires more than 20 port operations
4. WHEN the component mounts THEN the system SHALL measure time-to-interactive (from mount to first layout complete) and expose it via a ready event
5. WHEN memory leaks are suspected THEN the system SHALL properly cleanup all X6 event listeners, timers, and DOM references in onUnmounted lifecycle hook

### Requirement 10: Backward Compatibility and Migration Path

**User Story:** As a developer maintaining existing features using the DAG component, I want the refactored version to maintain API compatibility, so that I can upgrade without rewriting integration code.

#### Acceptance Criteria

1. WHEN the component is refactored THEN the system SHALL maintain all 15 existing props (operators, layout, readonly, showSidebar, showToolbar, etc.) with identical names, types, and default values
2. WHEN the component is refactored THEN the system SHALL maintain all 10 existing events (node-click, node-dblclick, save, ready, etc.) with identical names and payload structures
3. WHEN the component is refactored THEN the system SHALL maintain all 2 exposed methods (getSaveData, getGraph) with identical signatures and return types
4. WHEN the component is refactored THEN the system SHALL maintain the existing slot structure (toolbar-left, toolbar-right) with identical slot props
5. WHEN breaking changes are unavoidable THEN the system SHALL provide a migration guide documenting changes, provide console warnings for deprecated APIs, and maintain deprecated APIs for one major version

### Requirement 11: Error Handling and Resilience

**User Story:** As a user working with the DAG component, I want graceful error handling and helpful error messages, so that I can understand what went wrong and how to fix it without losing my work.

#### Acceptance Criteria

1. WHEN layout calculation fails THEN the system SHALL catch the error, log details to console, display a user-friendly toast message, and preserve the previous valid layout
2. WHEN invalid graph data is loaded THEN the system SHALL validate the structure (nodes array, edges array, required fields) and show specific error messages identifying missing/invalid fields
3. WHEN a cycle is detected during connection THEN the system SHALL prevent the connection, show a toast message explaining the cycle, and optionally highlight the cycle path
4. WHEN export operations fail THEN the system SHALL catch errors, log the stack trace, show a user-friendly message, and provide a fallback (e.g., copy JSON to clipboard)
5. WHEN X6 throws internal errors THEN the system SHALL wrap X6 operations in try-catch blocks, log the error with context (operation name, node/edge IDs), and attempt graceful recovery

### Requirement 12: Accessibility and Keyboard Navigation

**User Story:** As a user relying on keyboard navigation, I want full keyboard access to DAG functionality, so that I can create and edit graphs without requiring a mouse.

#### Acceptance Criteria

1. WHEN the graph has focus THEN the system SHALL support arrow keys to navigate between nodes (up/down/left/right moving focus to adjacent connected nodes)
2. WHEN a node is focused THEN the system SHALL support Delete key to remove the node after confirmation
3. WHEN a node is focused THEN the system SHALL support Ctrl+C to copy and Ctrl+V to paste the node
4. WHEN the graph has focus THEN the system SHALL support Ctrl+Z for undo and Ctrl+Shift+Z for redo using the existing XFlowHistory plugin
5. WHEN keyboard navigation is active THEN the system SHALL provide visible focus indicators (outline, highlight) on the currently focused node

### Requirement 13: Documentation and Developer Onboarding

**User Story:** As a new developer joining the team, I want comprehensive documentation with examples, so that I can understand the DAG component architecture and start contributing within one day.

#### Acceptance Criteria

1. WHEN composables are created THEN the system SHALL include JSDoc comments with @param, @returns, @example tags describing all parameters, return values, and usage patterns
2. WHEN complex algorithms are implemented THEN the system SHALL include inline comments explaining the algorithm steps, time complexity, and any non-obvious optimizations
3. WHEN the component API is documented THEN the system SHALL update README.md with current props, events, methods, and migration notes from previous versions
4. WHEN architectural decisions are made THEN the system SHALL document them in an ARCHITECTURE.md file explaining the composable pattern, state management approach, and extension points
5. WHEN code examples are provided THEN the system SHALL include at least 3 complete examples: basic usage, custom operators, and custom validation

### Requirement 14: Matrix View Synchronization

**User Story:** As a user switching between graph and matrix views, I want instant bidirectional synchronization, so that changes in one view immediately reflect in the other without manual refresh.

#### Acceptance Criteria

1. WHEN a node is added in matrix view THEN the system SHALL immediately create the corresponding graph node with correct position calculated by layout algorithm
2. WHEN a node property is edited in matrix view THEN the system SHALL immediately update the graph node's visual representation (label, color, size)
3. WHEN a node is deleted in matrix view THEN the system SHALL immediately remove the graph node and all connected edges
4. WHEN a node is dragged in graph view THEN the system SHALL immediately update the matrix view's position data (x, y coordinates)
5. WHEN the graph is re-laid out THEN the system SHALL immediately update all matrix view position data to reflect new node positions

### Requirement 15: Device Node Specialization

**User Story:** As a user working with hardware device topologies, I want device nodes to display typed ports with visual differentiation, so that I can correctly connect devices based on interface compatibility.

#### Acceptance Criteria

1. WHEN a device node is created THEN the system SHALL render ports with colors based on bus type (Ethernet=blue, CAN=green, RS422=orange, 1553B=purple) using the existing port color mapping
2. WHEN a device node has more than 8 ports THEN the system SHALL distribute ports evenly across all four sides (top/bottom/left/right) to prevent overlap
3. WHEN connecting device ports THEN the system SHALL validate bus type compatibility and prevent connections between incompatible types (e.g., Ethernet to CAN)
4. WHEN a device port label exceeds 6 characters THEN the system SHALL truncate with ellipsis and show full name in tooltip on hover
5. WHEN device nodes are in the graph THEN the system SHALL exempt them from standard port hiding rules, keeping all device ports visible regardless of layout direction
