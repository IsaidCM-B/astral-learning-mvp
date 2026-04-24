# Astral Learning Platform - Setup Guide

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker Desktop
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd astral-learning-mvp
```

### 2. Environment Setup
```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - PINECONE_API_KEY
# - JWT_SECRET (generate a secure key)
```

### 3. Start Development Environment
```bash
# Start all services with Docker
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

### 4. Access Services
- **Backend API**: http://localhost:3000/docs
- **AI Orchestrator**: http://localhost:8000/docs
- **Parent Dashboard**: http://localhost:3001
- **Database**: localhost:5432 (PostgreSQL)
- **Redis**: localhost:6379

## Development Workflow

### Backend Development
```bash
cd backend

# Start development server
npm run start:dev

# Run tests
npm test

# Run e2e tests
npm run test:e2e

# Generate migration
npm run migration:generate -n MigrationName

# Run migrations
npm run migration:run
```

### AI Orchestrator Development
```bash
cd ai-orchestrator

# Start development server
uvicorn src.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Format code
black src/
isort src/
```

### Frontend Development
```bash
cd frontend-parent

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint

# Type check
npm run type-check
```

## Database Setup

### PostgreSQL
```bash
# Connect to database
docker exec -it astral-postgres psql -U postgres -d astral_learning

# Create tables (handled by TypeORM)
npm run migration:run
```

### Redis
```bash
# Connect to Redis
docker exec -it astral-redis redis-cli

# Clear cache
FLUSHALL
```

## API Integration

### Backend → AI Orchestrator
```typescript
// Example API call from backend to AI orchestrator
const response = await fetch('http://localhost:8000/api/v1/orchestrate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    userId: user.id,
    context: 'learning',
    data: userBehavior,
  }),
});
```

### Frontend → Backend
```typescript
// Example API call from frontend to backend
const response = await fetch('/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

## Testing

### Unit Tests
```bash
# Backend
cd backend && npm test

# AI Orchestrator
cd ai-orchestrator && pytest

# Frontend
cd frontend-parent && npm test
```

### Integration Tests
```bash
# Backend
cd backend && npm run test:e2e

# AI Orchestrator
cd ai-orchestrator && pytest tests/integration/
```

### End-to-End Tests
```bash
# Frontend
cd frontend-parent && npm run test:e2e
```

## Deployment

### Development
```bash
docker-compose up -d
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Health Checks
- Backend: http://localhost:3000/health
- AI Orchestrator: http://localhost:8000/health
- Frontend: http://localhost:3001/api/health

### Logs
```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f ai-orchestrator
docker-compose logs -f frontend-parent
```

### Metrics
- Backend: http://localhost:3000/metrics
- AI Orchestrator: http://localhost:8000/metrics

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :3001

# Kill processes using ports
sudo kill -9 <PID>
```

#### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
npm run migration:run
```

#### Dependency Issues
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Clear Python cache
pip cache purge
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Contributing

### Code Standards
- TypeScript for backend and frontend
- Python for AI orchestrator
- ESLint + Prettier for TypeScript
- Black + isort for Python
- 80%+ test coverage required

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

### Pull Request Requirements
- All tests pass
- Code coverage maintained
- Documentation updated
- API docs updated (if applicable)

## Security

### Environment Variables
Never commit `.env` file. Use `.env.example` as template.

### API Keys
Rotate API keys regularly. Use different keys for development and production.

### Dependencies
Regularly update dependencies and check for vulnerabilities:
```bash
# Backend
npm audit
npm update

# AI Orchestrator
pip-audit
pip install --upgrade -r requirements.txt

# Frontend
npm audit
npm update
```

## Performance

### Optimization Tips
- Use Redis for caching
- Implement database indexes
- Optimize API response times
- Use CDN for static assets
- Implement lazy loading in frontend

### Monitoring
- Set up application monitoring
- Track API response times
- Monitor database performance
- Set up alerts for errors

## Support

For issues and questions:
1. Check this documentation
2. Search existing issues
3. Create new issue with detailed description
4. Include error logs and environment details
