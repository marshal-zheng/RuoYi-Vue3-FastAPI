# Project Structure

## Root Directory Layout
```
RuoYi-Vue3-FastAPI/
├── ruoyi-fastapi-frontend/    # Vue 3 frontend application
├── ruoyi-fastapi-backend/     # FastAPI backend application
├── dev-docs/                  # Development documentation
├── setup.sh                   # Environment initialization script
├── start.sh                   # Quick startup script
├── theme.md                   # Theme integration guide
├── QUICK_START.md            # Quick start guide
└── README.md                 # Project documentation
```

## Backend Structure (`ruoyi-fastapi-backend/`)

### Core Architecture Pattern
The backend follows a **layered architecture** with clear separation of concerns:

```
ruoyi-fastapi-backend/
├── app.py                     # Application entry point
├── server.py                  # FastAPI server configuration
├── requirements.txt           # Python dependencies
├── ruff.toml                 # Code linting configuration
├── .env.dev/.env.prod        # Environment configurations
├── config/                   # Configuration modules
│   ├── database.py           # Database configuration
│   ├── env.py               # Environment settings
│   ├── get_db.py            # Database dependency injection
│   ├── get_redis.py         # Redis dependency injection
│   └── enums.py             # System enumerations
├── module_admin/            # Admin module (main business logic)
│   ├── controller/          # API controllers (FastAPI routers)
│   ├── service/            # Business logic layer
│   ├── dao/                # Data access layer
│   ├── entity/             # Data models
│   │   ├── do/             # Database objects (SQLAlchemy models)
│   │   └── vo/             # View objects (Pydantic models)
│   ├── aspect/             # Cross-cutting concerns (auth, data scope)
│   └── annotation/         # Decorators and annotations
├── module_generator/        # Code generation module
├── module_task/            # Scheduled task module
├── middlewares/            # FastAPI middlewares
├── exceptions/             # Custom exception handling
├── utils/                  # Utility functions
├── sql/                    # Database schema files
└── vf_admin/              # File storage directories
```

### Backend Naming Conventions
- **Controllers**: `{module}_controller.py` (e.g., `user_controller.py`)
- **Services**: `{module}_service.py` (e.g., `user_service.py`)
- **DAOs**: `{module}_dao.py` (e.g., `user_dao.py`)
- **Models**: `{module}_do.py` for database objects, `{module}_vo.py` for view objects
- **API Routes**: Use APIRouter with prefix `/system/{module}`

### Backend Code Patterns
- **Dependency Injection**: Use FastAPI's `Depends()` for database sessions, authentication, permissions
- **Async/Await**: All database operations use async SQLAlchemy
- **Permission Control**: Use `CheckUserInterfaceAuth` decorator for API endpoints
- **Data Scope**: Use `GetDataScope` for row-level security
- **Logging**: Use `@Log` decorator for operation logging

## Frontend Structure (`ruoyi-fastapi-frontend/`)

### Vue 3 Architecture
```
ruoyi-fastapi-frontend/
├── index.html                # HTML entry point
├── package.json             # Node.js dependencies
├── vite.config.ts           # Vite build configuration
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── src/
│   ├── main.ts              # Application entry point
│   ├── App.tsx              # Root component
│   ├── settings.ts          # Application settings
│   ├── permission.ts        # Route permission guard
│   ├── api/                 # API service layer
│   │   ├── system/          # System module APIs
│   │   ├── monitor/         # Monitoring APIs
│   │   └── tool/            # Tool APIs
│   ├── components/          # Reusable Vue components
│   ├── views/               # Page components
│   │   ├── system/          # System management pages
│   │   ├── monitor/         # Monitoring pages
│   │   └── tool/            # Tool pages
│   ├── router/              # Vue Router configuration
│   ├── store/               # Pinia state management
│   │   └── modules/         # Store modules
│   ├── utils/               # Utility functions
│   ├── directive/           # Custom Vue directives
│   ├── plugins/             # Vue plugins
│   └── assets/              # Static assets
├── public/                  # Public static files
├── tests/                   # Test files
└── vite/                    # Vite plugin configurations
```

### Frontend Naming Conventions
- **Components**: PascalCase (e.g., `UserList.vue`, `DeptTree.vue`)
- **Views**: kebab-case directories with `index.vue` (e.g., `system/user/index.vue`)
- **API Services**: `{module}.js` (e.g., `user.js`, `role.js`)
- **Store Modules**: `{module}.js` (e.g., `user.js`, `app.js`)
- **Utils**: camelCase functions (e.g., `formatDate`, `checkPermi`)

### Frontend Code Patterns
- **Composition API**: Use `<script setup>` syntax for Vue 3 components
- **TypeScript**: Strongly typed components and API interfaces
- **Permission Directives**: Use `v-hasPermi` and `v-hasRole` for UI permissions
- **State Management**: Use Pinia stores for global state
- **API Layer**: Centralized API calls in `/src/api/` directory

## Module Organization

### Admin Module (`module_admin/`)
Contains all core system functionality:
- **User Management**: User CRUD, role assignment, password management
- **Role Management**: Role CRUD, permission assignment
- **Menu Management**: Menu tree, permission configuration
- **Department Management**: Organization structure
- **System Configuration**: Parameters, dictionaries, notices
- **Monitoring**: Logs, online users, system info

### Generator Module (`module_generator/`)
Code generation functionality:
- **Templates**: Jinja2 templates for code generation
- **Database Introspection**: Table structure analysis
- **Code Generation**: Controller, Service, DAO, VO generation

### Task Module (`module_task/`)
Scheduled task management:
- **Job Scheduling**: APScheduler integration
- **Task Monitoring**: Execution logs and status

## Configuration Management

### Environment-Based Configuration
- **Development**: `.env.dev` for local development
- **Production**: `.env.prod` for production deployment
- **Configuration Classes**: Pydantic models for type-safe configuration

### Database Configuration
- **Multi-Database Support**: MySQL and PostgreSQL
- **Connection Pooling**: SQLAlchemy async engine with connection pooling
- **Migration**: SQL files in `/sql/` directory

## File Upload Structure
```
vf_admin/
├── upload_path/             # User uploaded files
├── download_path/           # Generated download files
└── gen_path/               # Code generation output
```

## Development Documentation
```
dev-docs/
├── backend/                 # Backend-specific documentation
├── frontend/               # Frontend-specific documentation
└── common/                 # Shared documentation
```

## Best Practices

### Backend Development
- Follow the Controller → Service → DAO pattern
- Use async/await for all database operations
- Implement proper error handling with custom exceptions
- Apply permission decorators to all protected endpoints
- Use Pydantic models for request/response validation

### Frontend Development
- Use TypeScript for type safety
- Implement proper error handling in API calls
- Follow Vue 3 Composition API patterns
- Use permission directives for UI access control
- Maintain consistent component structure and naming