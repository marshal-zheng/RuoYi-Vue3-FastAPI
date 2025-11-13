# Technology Stack

## Frontend Stack
- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite 5.3.2
- **UI Library**: Element Plus 2.7.6
- **Language**: TypeScript
- **State Management**: Pinia 2.1.7
- **Routing**: Vue Router 4.4.0
- **HTTP Client**: Axios 0.28.1
- **Package Manager**: Yarn (preferred) or NPM
- **CSS Framework**: Tailwind CSS 4.1.12
- **Testing**: Vitest with Vue Testing Library

## Backend Stack
- **Framework**: FastAPI 0.115.8
- **Language**: Python 3.9+
- **ORM**: SQLAlchemy 2.0.38 (async)
- **Database**: MySQL 5.7+ or PostgreSQL
- **Cache**: Redis 5.2.1
- **Authentication**: JWT with OAuth2
- **Task Scheduler**: APScheduler 3.11.0
- **Logging**: Loguru 0.7.3
- **Environment Management**: python-dotenv
- **Password Hashing**: passlib with bcrypt

## Infrastructure Requirements
- **Python**: ≥ 3.9
- **Node.js**: ≥ 16
- **MySQL**: ≥ 5.7 or PostgreSQL
- **Redis**: For caching and session management

## Common Commands

### Frontend Development
```bash
cd ruoyi-fastapi-frontend

# Install dependencies
yarn install  # or npm install

# Development server
yarn dev      # or npm run dev

# Build for production
yarn build:prod  # or npm run build:prod

# Build for staging
yarn build:stage # or npm run build:stage

# Type checking
yarn type-check  # or npm run type-check

# Linting
yarn lint        # or npm run lint

# Testing
yarn test        # or npm run test
yarn test:run    # or npm run test:run
yarn test:coverage # or npm run test:coverage
```

### Backend Development
```bash
cd ruoyi-fastapi-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Development server
python app.py --env=dev

# Production server with Gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Database Setup
```bash
# Create database
mysql -u root -e "CREATE DATABASE \`ruoyi-fastapi\` CHARACTER SET utf8mb4;"

# Import schema
mysql -u root ruoyi-fastapi < sql/ruoyi-fastapi.sql
```

### Quick Start Scripts
```bash
# First-time setup (installs all dependencies and configures environment)
./setup.sh

# Daily development startup
./start.sh
```

## Environment Configuration

### Backend Environment Files
- `.env.dev` - Development environment
- `.env.prod` - Production environment
- Environment variables are loaded based on `--env` parameter

### Frontend Environment Files
- `.env.development` - Development environment
- `.env.production` - Production environment
- `.env.staging` - Staging environment

## Code Quality Tools
- **Backend**: Ruff for linting and formatting
- **Frontend**: ESLint + Prettier for code quality
- **Testing**: Vitest for frontend, built-in testing patterns for backend