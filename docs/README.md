# Multi-Agent Code Generation System

A production-ready, intelligent code generation platform powered by CrewAI and OpenAI that automatically creates complete software projects from natural language descriptions.

## 🚀 Features

- **Multi-Agent Workflow**: Intelligent agents working together for project planning, code generation, testing, and documentation
- **Real-time Collaboration**: Live WebSocket updates and interactive chat with AI agents
- **Advanced Code Editor**: Sandpack integration for live code preview and editing
- **Comprehensive Testing**: Automated test generation and execution
- **Production Ready**: JWT authentication, rate limiting, PostgreSQL, Redis caching
- **Persian/Farsi UI**: RTL-supported interface with Persian localization
- **Scalable Architecture**: Async FastAPI backend with proper error handling and monitoring
- **🤗 Hugging Face Integration**: Automatic deployment to Hugging Face Spaces with CI/CD

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    FastAPI       │    │   Database      │
│   (HTML/JS)     │◄───┤    Backend       │◄───┤   PostgreSQL    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────┤   CrewAI        │              │
                        │   Agents        │              │
                        └─────────────────┘              │
                                 │                       │
                        ┌─────────────────┐              │
                        │   OpenAI API    │              │
                        └─────────────────┘              │
                                                         │
                        ┌─────────────────┐              │
                        │   Redis Cache   │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Hugging Face    │
                        │ Spaces Deploy   │
                        └─────────────────┘
```

## 🧠 AI Agents

The system employs four specialized AI agents:

1. **PlannerAgent**: Analyzes requirements and creates detailed project plans
2. **CodeGeneratorAgent**: Generates production-ready code based on plans
3. **TesterAgent**: Creates comprehensive test suites with high coverage
4. **DocGeneratorAgent**: Generates documentation, README files, and API docs

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for frontend dependencies)
- OpenAI API key
- Hugging Face account and token (for deployment)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-agent-code-generator.git
cd multi-agent-code-generator
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Database Settings
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/multiagent

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# OpenAI Settings
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Security Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Hugging Face Token (for deployment)
HF_TOKEN=hf_your_hugging_face_token_here
```

## 🤗 Hugging Face Deployment Setup

### Quick Setup (Recommended)

Use our automated setup script for easy Hugging Face integration:

```bash
# Set your HF token and run setup
HF_TOKEN=your_hf_token_here ./scripts/setup.sh
```

This will:
- ✅ Validate your HF token
- ✅ Install dependencies
- ✅ Create environment configuration
- ✅ Prepare deployment scripts
- ✅ Generate GitHub setup instructions

### Manual Setup

1. **Get Your Hugging Face Token**
   ```bash
   # Visit: https://huggingface.co/settings/tokens
   # Create a new token with 'write' permissions
   export HF_TOKEN=your_hf_token_here
   ```

2. **Validate Your Token**
   ```bash
   python scripts/validate-token.py
   ```

3. **Configure GitHub Secrets**
   - Go to your GitHub repository settings
   - Navigate to "Secrets and variables" → "Actions"  
   - Add new secret: `HF_TOKEN` = `your_hf_token_here`

4. **Test Deployment**
   ```bash
   # Manual deployment
   ./deploy.sh "🧪 Initial deployment test"
   
   # Or push to main branch for auto-deployment
   git push origin main
   ```

### Deployment Options

#### 🔄 Automatic Deployment (Recommended)
Every push to `main` branch automatically deploys to:
**https://huggingface.co/spaces/Really-amin/ultichat-hugginigfae**

#### 🛠️ Manual Deployment
```bash
export HF_TOKEN=your_hf_token_here
./deploy.sh "Your deployment message"
```

#### 📋 Deployment Commands
```bash
# Validate token only
./deploy.sh validate

# Prepare deployment files
./deploy.sh prepare

# Full deployment with custom message
./deploy.sh deploy "🚀 New features added"
```

### Environment Variables for Hugging Face Spaces

Set these in your Hugging Face Space settings:

```env
OPENAI_API_KEY=your-openai-api-key-here
JWT_SECRET_KEY=your-secure-jwt-secret-key
DATABASE_URL=your-database-url-if-external
```

## 🚀 Quick Start

1. **Access the Interface**: Open `http://localhost:8000/static/index.html`
2. **Configure API**: Click settings (⚙️) and enter your OpenAI API key
3. **Create Project**: Fill out the project form with your requirements
4. **Watch Magic**: Observe real-time progress as AI agents work together
5. **Download Code**: Get your complete project as a ZIP file

## 📡 API Documentation

### Authentication

All API endpoints require JWT authentication:

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use the returned token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/stats
```

### Core Endpoints

#### Generate Project
```http
POST /api/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "My Web App",
  "description": "A modern web application with user authentication",
  "project_type": "web_app",
  "languages": ["python", "javascript"],
  "frameworks": ["fastapi", "react"],
  "complexity": "moderate",
  "features": ["authentication", "database"],
  "mode": "full"
}
```

#### Check Status
```http
GET /status/{job_id}
Authorization: Bearer <token>
```

#### Download Project
```http
GET /download/{job_id}
Authorization: Bearer <token>
```

#### Execute Code
```http
POST /api/execute
Content-Type: application/json
Authorization: Bearer <token>

{
  "code": "print('Hello, World!')",
  "language": "python",
  "timeout": 30
}
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=./ --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Frontend Tests

Open `tests/frontend.test.html` in your browser and click "Run All Tests".

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t multi-agent-code-gen .

# Run container
docker run -d \
  --name code-generator \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/multiagent \
  -e OPENAI_API_KEY=your-key \
  multi-agent-code-gen
```

## 🚀 Deployment

### Local Development

```bash
# Start all services
python main.py

# Or use the comprehensive deployment script
./scripts/deploy.sh
```

### Production Deployment

#### Option 1: Hugging Face Spaces (Recommended)
```bash
# Automatic deployment on git push
git push origin main

# Or manual deployment
./deploy.sh "Production deployment"
```

#### Option 2: Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or use the deployment script
./scripts/deploy.sh deploy
```

#### Option 3: Traditional Server
```bash
# Set production environment
export ENVIRONMENT=production

# Run with Gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔧 Configuration

### Environment Variables

The application supports extensive configuration through environment variables. See `.env.example` for all available options:

- **Security**: JWT secrets, HTTPS settings, CORS configuration
- **Database**: PostgreSQL connection, pool settings
- **Redis**: Cache configuration, connection settings  
- **AI Services**: OpenAI API configuration, Hugging Face tokens
- **Performance**: Worker settings, timeouts, rate limiting
- **Features**: Enable/disable specific functionality
- **Monitoring**: Logging, metrics, health checks

### Feature Flags

Control application features via environment variables:

```env
ENABLE_WEBSOCKETS=True          # Real-time updates
ENABLE_FILE_UPLOAD=True         # File upload functionality  
ENABLE_CODE_EXECUTION=False     # Code execution (use with caution)
ENABLE_METRICS_DASHBOARD=True   # Performance monitoring
```

## 🔐 Security

### Authentication & Authorization

- JWT-based authentication with configurable expiration
- Rate limiting on all endpoints
- CORS protection with configurable origins
- Request validation and sanitization

### Security Headers

```python
# Security middleware enabled
app.add_middleware(TrustedHostMiddleware)
app.add_middleware(CORSMiddleware)
```

### Input Validation

All inputs are validated using Pydantic models with strict typing and sanitization.

### Token Management

- **Never commit tokens to git**: All sensitive data should be in environment variables
- **Use GitHub Secrets**: For CI/CD deployment tokens
- **Rotate tokens regularly**: Set reminders to update HF and OpenAI tokens
- **Principle of least privilege**: Use tokens with minimal required permissions

### Best Practices

1. **Environment Separation**: Use different tokens for development/production
2. **Token Validation**: Regularly validate tokens using `python scripts/validate-token.py`
3. **Access Monitoring**: Monitor Hugging Face space access logs
4. **Secret Management**: Use secure secret management in production

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Detailed system status  
curl http://localhost:8000/health/detailed
```

### Deployment Monitoring

- **GitHub Actions**: Monitor deployment workflows in the Actions tab
- **Hugging Face Logs**: Check build and runtime logs in your Space
- **Application Metrics**: Access metrics at `/metrics` endpoint

## 🌐 WebSocket API

Real-time updates via WebSocket at `/ws`:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};

// Send ping
ws.send(JSON.stringify({type: 'ping'}));
```

### Message Types

- `status`: System status updates
- `agent_message`: Messages from AI agents
- `log`: System log entries
- `progress`: Job progress updates
- `error`: Error notifications

## 🛠️ Development

### Project Structure

```
├── app.py              # Main FastAPI application
├── config.py           # Configuration management
├── models.py           # Pydantic models
├── db.py              # Database operations
├── agents.py          # CrewAI agents
├── routes.py          # API routes
├── requirements.txt   # Python dependencies
├── .env              # Environment configuration
├── static/           # Frontend files
│   └── index.html    # Main UI
├── tests/            # Test suite
│   ├── backend.test.py
│   └── frontend.test.html
└── docs/             # Documentation
```

### Adding New Agents

1. Create agent class extending `BaseCrewAgent`
2. Implement required methods (`execute`, `validate_input`)
3. Register agent in `MultiAgentWorkflow`
4. Add agent configuration to settings

```python
class MyCustomAgent(BaseCrewAgent):
    async def execute(self, input_data):
        # Agent logic here
        return result
```

### Custom Tools

Extend `AgentTools` class to add new capabilities:

```python
@tool("my_custom_tool")
def my_tool(input: str) -> str:
    """Custom tool description."""
    # Tool implementation
    return result
```

## 🚨 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U username -d multiagent
```

**Redis Connection Errors**
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping
```

**OpenAI API Errors**
- Verify API key validity
- Check rate limits and quotas
- Ensure model availability

**WebSocket Connection Issues**
- Check firewall settings
- Verify CORS configuration
- Test with different browsers

### Debug Mode

Enable debug mode for detailed error messages:

```env
DEBUG=true
```

### Logs

Structured logging with JSON format:

```bash
# View logs
tail -f app.log

# Filter by level
grep "ERROR" app.log
```

### Getting Help

1. **Check logs**: GitHub Actions, Hugging Face Space, application logs
2. **Validate configuration**: Use provided validation scripts
3. **Test components**: Use individual test commands for each service
4. **Community support**: Open issues with detailed error information

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Component Documentation**: In `docs/` directory
- **Deployment Guide**: See `GITHUB_SETUP.md` after running setup script
- **Architecture Details**: See `docs/architecture.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **CrewAI**: For the multi-agent framework
- **OpenAI**: For the language model API
- **Hugging Face**: For hosting and deployment platform
- **FastAPI**: For the high-performance web framework
- **Community**: For contributions and feedback

---

## 🚀 Quick Start Commands

### Immediate Setup
```bash
# 1. Clone and setup
git clone <your-repo-url>
cd multi-agent-code-generator

# 2. Quick HF setup
HF_TOKEN=your_hf_token_here ./scripts/setup.sh

# 3. Configure other environment variables
nano .env

# 4. Test deployment
./deploy.sh "🧪 Initial test"
```

### Development Workflow
```bash
# Start development server
python main.py

# In another terminal, test the API
curl http://localhost:8000/health

# Deploy when ready
git add .
git commit -m "✨ New features"
git push origin main  # Auto-deploys to HF Spaces
```

**🌐 Your deployed application**: https://huggingface.co/spaces/Really-amin/ultichat-hugginigfae
