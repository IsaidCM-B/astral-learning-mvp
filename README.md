# Astral Learning Platform - MVP

## Overview

Premium AI-driven learning platform for families, combining personalized education, real-world skill development, and high security standards.

## Architecture

```
├── backend/                 # NestJS Core Platform
├── ai-orchestrator/        # Python FastAPI + LangGraph
├── frontend-parent/        # React Next.js Dashboard
├── frontend-student/       # React Native App
├── docker-compose.yml      # Development environment
└── docs/                   # API Documentation
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker Desktop
- PostgreSQL 15+
- Redis 7+

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd astral-learning-mvp

# Start services with Docker
docker-compose up -d

# Install backend dependencies
cd backend
npm install
npm run start:dev

# Install AI orchestrator dependencies
cd ../ai-orchestrator
pip install -r requirements.txt
uvicorn src.main:app --reload

# Install frontend dependencies
cd ../frontend-parent
npm install
npm run dev
```

## Services

### Backend (NestJS)
- **Port**: 3000
- **API Documentation**: http://localhost:3000/docs
- **Database**: PostgreSQL
- **Cache**: Redis

### AI Orchestrator (FastAPI)
- **Port**: 8000
- **API Documentation**: http://localhost:8000/docs
- **LLM Integration**: OpenAI, Anthropic, Gemini
- **Vector DB**: Pinecone

### Frontend Parent (Next.js)
- **Port**: 3001
- **URL**: http://localhost:3001

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Token refresh

### Users & Profiles
- `GET /users/me` - Get current user
- `PUT /users/me` - Update profile
- `GET /users/{id}/profile` - Get user profile

### Missions
- `GET /missions` - List missions
- `POST /missions/{id}/start` - Start mission
- `PUT /missions/{id}/progress` - Update progress

### AI Services
- `POST /ai/orchestrate` - AI orchestration
- `POST /ai/tutor` - Tutor copilot
- `POST /ai/analyze` - Behavioral analysis

## Development Workflow

### Git Branch Strategy
```bash
git checkout -b feature/user-authentication
git commit -m "feat: implement JWT authentication"
git push origin feature/user-authentication
# Create Pull Request
```

### Code Standards
- TypeScript for all services
- ESLint + Prettier formatting
- 80%+ test coverage
- English documentation only

## Testing

### Backend Tests
```bash
cd backend
npm test
npm run test:e2e
```

### AI Orchestrator Tests
```bash
cd ai-orchestrator
pytest
pytest --cov=src
```

### Frontend Tests
```bash
cd frontend-parent
npm test
npm run test:e2e
```

## Deployment

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Security

- JWT authentication
- API rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## Monitoring

- Health checks: `/health`
- Metrics: Prometheus
- Logs: ELK Stack
- Error tracking: Sentry

## Contributing

1. Fork repository
2. Create feature branch
3. Write tests
4. Submit pull request

## License

Private - All rights reserved
