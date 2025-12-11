# Requirements Document

## Introduction

本规范定义了对项目中导入导出功能的工程化重构需求。当前项目中存在多处导入导出实现，代码分散、重复度高、缺乏统一抽象。本次重构旨在抽象出通用的导入导出工具库，提升代码复用性、可维护性和可扩展性，同时为后续项目开发提供可沉淀的基础设施。

## Glossary

- **IO_Toolkit**: 导入导出工具库，包含后端和前端的通用导入导出功能封装
- **Exporter**: 导出器，负责将数据转换为特定格式（Excel/JSON/ZIP/XML等）的组件
- **Importer**: 导入器，负责解析特定格式文件并转换为系统数据的组件
- **ExportResult**: 导出结果数据模型，包含导出内容、文件名、MIME类型等
- **ImportResult**: 导入结果数据模型，包含成功/失败状态、导入数据、错误信息等
- **ExportStrategy**: 导出策略接口，定义导出行为的抽象
- **ImportStrategy**: 导入策略接口，定义导入行为的抽象
- **SchemaValidator**: 数据结构验证器，用于验证导入数据的格式和完整性

## Requirements

### Requirement 1

**User Story:** As a developer, I want a unified export toolkit, so that I can implement data export functionality without writing repetitive code.

#### Acceptance Criteria

1. WHEN a developer needs to export data to Excel format THEN the IO_Toolkit SHALL provide an ExcelExporter class that accepts a list of data and a field mapping dictionary
2. WHEN a developer needs to export data to JSON format THEN the IO_Toolkit SHALL provide a JsonExporter class that serializes Pydantic models to JSON bytes
3. WHEN a developer needs to package multiple files into a ZIP archive THEN the IO_Toolkit SHALL provide a ZipExporter class that accepts multiple file entries
4. WHEN any exporter completes an export operation THEN the IO_Toolkit SHALL return an ExportResult object containing content bytes, filename, and content_type
5. WHEN an export operation fails THEN the IO_Toolkit SHALL raise an ExportException with a descriptive error message

### Requirement 2

**User Story:** As a developer, I want a unified import toolkit, so that I can implement data import functionality with consistent validation and error handling.

#### Acceptance Criteria

1. WHEN a developer needs to import data from Excel format THEN the IO_Toolkit SHALL provide an ExcelImporter class that parses Excel files and returns structured data
2. WHEN a developer needs to import data from JSON format THEN the IO_Toolkit SHALL provide a JsonImporter class that deserializes JSON to Pydantic models
3. WHEN a developer needs to extract files from a ZIP archive THEN the IO_Toolkit SHALL provide a ZipImporter class that extracts and processes contained files
4. WHEN any importer completes an import operation THEN the IO_Toolkit SHALL return an ImportResult object containing success status, imported data, and error details
5. WHEN an import operation encounters invalid data THEN the IO_Toolkit SHALL raise an ImportValidationException with field-level error information

### Requirement 3

**User Story:** As a developer, I want export data models with version control, so that I can ensure backward compatibility when import formats change.

#### Acceptance Criteria

1. WHEN creating an export data model THEN the IO_Toolkit SHALL require an export_version field in the model definition
2. WHEN importing data THEN the IO_Toolkit SHALL validate the export_version against supported versions
3. WHEN the export_version is incompatible THEN the IO_Toolkit SHALL raise a VersionIncompatibleException with migration guidance
4. WHEN defining a new export format THEN the IO_Toolkit SHALL provide a base class ExportDataModel that enforces version metadata

### Requirement 4

**User Story:** As a developer, I want Excel template generation utilities, so that I can create import templates with proper formatting and validation rules.

#### Acceptance Criteria

1. WHEN generating an Excel template THEN the IO_Toolkit SHALL support defining column headers with Chinese labels
2. WHEN generating an Excel template THEN the IO_Toolkit SHALL support adding dropdown validation for specific columns
3. WHEN generating an Excel template THEN the IO_Toolkit SHALL support setting column widths and header styles
4. WHEN generating an Excel template THEN the IO_Toolkit SHALL support adding sample data rows

### Requirement 5

**User Story:** As a frontend developer, I want unified download utilities, so that I can trigger file downloads without writing repetitive Blob handling code.

#### Acceptance Criteria

1. WHEN downloading a file from an API response THEN the frontend IO_Toolkit SHALL provide a downloadBlob function that handles Blob creation and download triggering
2. WHEN downloading a file THEN the frontend IO_Toolkit SHALL automatically extract filename from response headers when available
3. WHEN a download fails THEN the frontend IO_Toolkit SHALL display an error message and reject the promise
4. WHEN downloading large files THEN the frontend IO_Toolkit SHALL display a loading indicator during the download process

### Requirement 6

**User Story:** As a frontend developer, I want unified upload utilities, so that I can implement file import functionality with consistent validation and preview.

#### Acceptance Criteria

1. WHEN uploading a file for import THEN the frontend IO_Toolkit SHALL provide a validateFile function that checks file type and size
2. WHEN uploading a JSON file THEN the frontend IO_Toolkit SHALL provide a parseJsonFile function that reads and parses the file content
3. WHEN uploading a ZIP file THEN the frontend IO_Toolkit SHALL provide an uploadFormData function that handles multipart form submission
4. WHEN file validation fails THEN the frontend IO_Toolkit SHALL return a descriptive error message without making an API call

### Requirement 7

**User Story:** As a frontend developer, I want reusable import/export Vue components, so that I can quickly add import/export functionality to any page.

#### Acceptance Criteria

1. WHEN adding export functionality to a page THEN the frontend IO_Toolkit SHALL provide an ExportButton component that handles loading state and error display
2. WHEN adding import functionality to a page THEN the frontend IO_Toolkit SHALL provide an ImportUploader component that handles file selection, validation, and upload
3. WHEN using the ImportUploader component THEN the component SHALL emit events for success, error, and progress updates
4. WHEN using the ExportButton component THEN the component SHALL accept an async export function and filename as props

### Requirement 8

**User Story:** As a system architect, I want the IO_Toolkit to follow SOLID principles, so that the codebase remains maintainable and extensible.

#### Acceptance Criteria

1. WHEN adding a new export format THEN the developer SHALL only need to implement the ExportStrategy interface without modifying existing code
2. WHEN adding a new import format THEN the developer SHALL only need to implement the ImportStrategy interface without modifying existing code
3. WHEN the IO_Toolkit is used THEN each class SHALL have a single responsibility (export, import, validation, or serialization)
4. WHEN extending the IO_Toolkit THEN the developer SHALL be able to inject custom validators and serializers through dependency injection

### Requirement 9

**User Story:** As a developer, I want to migrate existing export implementations to use the IO_Toolkit, so that the codebase becomes more consistent.

#### Acceptance Criteria

1. WHEN migrating user export functionality THEN the existing ExcelUtil.export_list2excel calls SHALL be replaced with ExcelExporter
2. WHEN migrating project export functionality THEN the existing ZipFile handling code SHALL be replaced with ZipExporter
3. WHEN migrating device export functionality THEN the existing JSON serialization code SHALL be replaced with JsonExporter
4. WHEN migration is complete THEN all export endpoints SHALL return consistent ExportResult-based responses

### Requirement 10

**User Story:** As a developer, I want to migrate existing import implementations to use the IO_Toolkit, so that import validation and error handling become consistent.

#### Acceptance Criteria

1. WHEN migrating user import functionality THEN the existing pandas Excel parsing code SHALL be replaced with ExcelImporter
2. WHEN migrating project import functionality THEN the existing ZipFile extraction code SHALL be replaced with ZipImporter
3. WHEN migrating protocol import functionality THEN the existing multi-sheet parsing code SHALL be replaced with ExcelImporter with sheet configuration
4. WHEN migration is complete THEN all import endpoints SHALL return consistent ImportResult-based responses
