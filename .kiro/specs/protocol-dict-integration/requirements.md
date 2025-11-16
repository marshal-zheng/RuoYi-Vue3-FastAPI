# Requirements Document

## Introduction

本需求文档定义了协议管理功能的字典集成优化。当前协议创建功能中的协议类型、传输频率、传输速率、传输方式、数据类型等字段采用硬编码或手动输入方式，不便于系统维护和扩展，且容易出现输入错误。本需求旨在将这些字段改造为使用系统字典管理，提供标准化的选项，并在系统初始化时自动创建相关字典数据，无需用户手动配置，从而提升用户体验和数据一致性。

## Glossary

- **System**: 若依FastAPI管理系统
- **Protocol_Management_Module**: 协议管理模块，负责协议的创建、编辑、查询和删除
- **Dictionary_System**: 系统字典功能，用于管理系统中的枚举类型数据
- **Protocol_Type**: 协议类型，包括以太网、RS422、CAN、1553B等通信协议类型
- **Transmission_Frequency**: 传输频率，定义协议数据的发送周期，如单次、10ms、100ms等
- **Transmission_Speed**: 传输速率，定义协议的通信速率，不同协议类型有不同的标准速率
- **Transmission_Method**: 传输方式或帧类型，如UDP组播、CAN扩展帧等
- **Data_Type**: 数据类型，定义协议字段的数据格式，如uint8、int16、float等
- **Error_Handling**: 错误处理策略，定义协议通信异常时的处理方式
- **Database_Migration**: 数据库迁移脚本，用于初始化或更新数据库结构和数据
- **Frontend_Component**: 前端组件，包括表单、选择器等UI元素
- **Backend_API**: 后端API接口，提供数据查询和操作服务
- **Protocol_Template**: 协议模板组件，根据协议类型展示不同的配置界面

## Requirements

### Requirement 1

**User Story:** 作为系统管理员，我希望协议类型通过系统字典管理，以便我可以灵活地添加、修改或删除协议类型，而无需修改代码

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create a dictionary type named "协议类型" with dict_type "sys_protocol_type"
2. WHEN THE System initializes, THE System SHALL create dictionary data entries for protocol types including "以太网", "RS422", "CAN", and "1553B" under "sys_protocol_type" with appropriate sort order
3. WHEN a user creates or edits a protocol, THE Protocol_Management_Module SHALL load protocol type options from the Dictionary_System
4. WHEN a user selects a protocol type from the dropdown, THE Frontend_Component SHALL display the corresponding Protocol_Template configuration interface
5. WHEN the dictionary data for protocol types is modified, THE Protocol_Management_Module SHALL reflect the changes without code deployment

### Requirement 2

**User Story:** 作为协议配置人员，我希望传输频率提供标准选项，以便我可以快速选择常用的传输周期，避免手动输入错误

**注意：** 协议管理不使用状态字段，所有协议默认为启用状态

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create a dictionary type named "传输频率" with dict_type "sys_protocol_frequency"
2. WHEN THE System initializes, THE System SHALL create dictionary data entries including "单次", "10ms", "20ms", "50ms", "100ms", "160ms", "200ms", "500ms", "1000ms" under "sys_protocol_frequency"
3. WHEN a user configures protocol parameters in the Protocol_Template, THE System SHALL display transmission frequency options from the Dictionary_System
4. WHEN a user selects a frequency option, THE System SHALL store the dict_value in the protocol configuration
5. WHEN displaying protocol configuration, THE System SHALL show the dict_label for better readability

### Requirement 3

**User Story:** 作为协议配置人员，我希望传输速率根据协议类型提供对应的标准速率选项，以确保配置的准确性和规范性

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create dictionary types for each protocol's transmission speeds with dict_type "sys_protocol_speed_ethernet", "sys_protocol_speed_rs422", "sys_protocol_speed_can", "sys_protocol_speed_1553b"
2. WHEN THE System initializes for Ethernet protocol, THE System SHALL create speed options "10M", "100M", "1000M" under "sys_protocol_speed_ethernet"
3. WHEN THE System initializes for RS422 protocol, THE System SHALL create speed options "9.6K", "19.2K", "38.4K", "57.6K", "115.2K", "230.4K", "460.8K", "921.6K" under "sys_protocol_speed_rs422"
4. WHEN THE System initializes for CAN protocol, THE System SHALL create speed options "125K", "250K", "500K", "1000K" under "sys_protocol_speed_can"
5. WHEN THE System initializes for 1553B protocol, THE System SHALL create speed option "1M" under "sys_protocol_speed_1553b"
6. WHEN a user selects a protocol type, THE Protocol_Template SHALL load the corresponding speed options based on the protocol type
7. WHEN a user selects a transmission speed, THE System SHALL store the dict_value with unit suffix (e.g., "100M bps")

### Requirement 4

**User Story:** 作为协议配置人员，我希望传输方式根据协议类型提供对应的标准选项，以便我可以选择正确的通信方式

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create dictionary types for transmission methods with dict_type "sys_protocol_method_ethernet", "sys_protocol_method_can"
2. WHEN THE System initializes for Ethernet protocol, THE System SHALL create method options "UDP单播", "UDP组播", "UDP广播", "TCP" under "sys_protocol_method_ethernet"
3. WHEN THE System initializes for CAN protocol, THE System SHALL create method options "CAN标准帧", "CAN扩展帧" under "sys_protocol_method_can"
4. WHEN a user selects Ethernet as protocol type, THE Protocol_Template SHALL display transmission method options from "sys_protocol_method_ethernet"
5. WHEN a user selects CAN as protocol type, THE Protocol_Template SHALL display transmission method options from "sys_protocol_method_can"
6. WHEN a user selects RS422 or 1553B as protocol type, THE Protocol_Template SHALL display the fixed method value without dropdown selection

### Requirement 5

**User Story:** 作为协议配置人员，我希望数据类型字段提供标准的编程数据类型选项，以确保协议字段定义的准确性

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create a dictionary type named "数据类型" with dict_type "sys_protocol_data_type"
2. WHEN THE System initializes, THE System SHALL create data type options including "uint8", "uint16", "uint32", "int8", "int16", "int32", "float", "double", "string", "bool" under "sys_protocol_data_type"
3. WHEN a user adds or edits a protocol field in the field configuration table, THE System SHALL provide a dropdown selector for the data type column
4. WHEN a user selects a data type, THE System SHALL store the dict_value in the field configuration
5. WHEN displaying the field configuration table, THE System SHALL show the dict_label for the data type column

### Requirement 6

**User Story:** 作为协议配置人员，我希望错误处理策略提供标准选项，以便我可以快速配置协议的异常处理方式

#### Acceptance Criteria

1. WHEN THE System initializes, THE System SHALL create a dictionary type named "错误处理" with dict_type "sys_protocol_error_handling"
2. WHEN THE System initializes, THE System SHALL create error handling options including "不判断", "超时重传", "CRC校验", "奇偶校验", "超时重传 3 次, 100ms" under "sys_protocol_error_handling"
3. WHEN a user configures protocol parameters in the Protocol_Template, THE System SHALL display error handling options from the Dictionary_System
4. WHEN a user selects an error handling option, THE System SHALL store the dict_value in the protocol configuration
5. WHEN displaying protocol configuration, THE System SHALL show the dict_label for error handling

### Requirement 7

**User Story:** 作为开发人员，我希望系统在初始化时自动创建协议相关的所有字典数据，以便部署时无需手动配置

#### Acceptance Criteria

1. WHEN THE Database_Migration script executes, THE System SHALL check if each protocol-related dictionary type exists
2. IF a protocol dictionary type does not exist, THEN THE System SHALL create the dictionary type with appropriate metadata including dict_name and remark
3. WHEN THE Database_Migration script creates dictionary types, THE System SHALL insert all dictionary data entries with proper sort order and list_class for styling
4. WHEN THE Database_Migration script completes, THE System SHALL ensure all dictionary data is cached in Redis
5. WHEN the migration script runs multiple times, THE System SHALL not create duplicate dictionary entries by checking existing data first

### Requirement 8

**User Story:** 作为前端开发人员，我希望协议模板组件能够自动从字典加载配置选项，以减少组件维护工作和硬编码

#### Acceptance Criteria

1. WHEN THE Protocol_Template initializes, THE System SHALL fetch relevant dictionary data from the Backend_API based on the protocol type
2. WHEN THE Backend_API returns dictionary data, THE Protocol_Template SHALL render dropdown selectors with dict_label as display text and dict_value as option value
3. WHEN a user selects an option from a dictionary-based dropdown, THE Protocol_Template SHALL store the dict_value in the protocol configuration
4. WHEN the dictionary data is empty or fails to load, THE Protocol_Template SHALL display an appropriate error message or fallback to input fields
5. WHEN editing an existing protocol, THE Protocol_Template SHALL pre-select options matching the protocol's current configuration values

### Requirement 9

**User Story:** 作为系统用户，我希望协议列表页面能够显示字典标签而非原始值，以提高可读性

#### Acceptance Criteria

1. WHEN THE Protocol_Management_Module displays the protocol list, THE System SHALL show dictionary labels for protocol_type column
2. WHEN a user filters protocols by type, THE System SHALL use dictionary labels in the filter dropdown
3. WHEN a user exports protocol data, THE System SHALL include dictionary labels in the exported file
4. WHEN dictionary data is updated, THE Protocol_Management_Module SHALL refresh the display without page reload
5. WHEN displaying protocol details, THE System SHALL show dictionary labels for all dictionary-based fields

### Requirement 10

**User Story:** 作为后端开发人员，我希望后端API能够提供字典数据查询接口，以支持前端组件的数据加载

#### Acceptance Criteria

1. WHEN THE Frontend_Component requests dictionary data by dict_type, THE Backend_API SHALL return data from Redis cache if available
2. IF Redis cache is empty, THEN THE Backend_API SHALL query the database and update the cache
3. WHEN THE Backend_API returns dictionary data, THE System SHALL include dict_label, dict_value, dict_sort, list_class, and remark fields
4. WHEN THE Backend_API encounters an error, THE System SHALL return an appropriate error response with status code and error message
5. WHEN dictionary data is modified through the dictionary management interface, THE System SHALL invalidate and refresh the Redis cache automatically
