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
```

### 5. Initialize Database

```bash
# Start PostgreSQL and Redis services
sudo systemctl start postgresql redis

# Create database
createdb multiagent

# Run database migrations (if using Alembic)
alembic upgrade head
```

### 6. Run the Application

```bash
# Development mode
python app.py

# Or with uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at `http://localhost:8000`

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

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `WORKERS` | Number of worker processes | `4` |
| `MAX_FILE_SIZE` | Maximum upload size (bytes) | `10485760` |

### Project Types

- `web_app`: Modern web applications
- `api`: RESTful API services
- `mobile_app`: Cross-platform mobile apps
- `desktop_app`: Desktop applications
- `cli_tool`: Command-line utilities
- `library`: Reusable libraries
- `microservice`: Microservice architectures
- `fullstack`: Complete full-stack applications

### Complexity Levels

- `simple`: Basic MVP functionality (1-2 hours)
- `moderate`: Standard features (3-5 hours)
- `complex`: Advanced functionality (6-12 hours)
- `enterprise`: Production-scale systems (12+ hours)

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

## 📊 Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Readiness (includes DB check)
curl http://localhost:8000/health/ready

# Liveness
curl http://localhost:8000/health/live
```

### System Statistics

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/stats
```

### Prometheus Metrics

Metrics are available at `/metrics` when `ENABLE_PROMETHEUS=true`.

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black .
isort .

# Run linting
flake8
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) for multi-agent framework
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [OpenAI](https://openai.com/) for AI capabilities
- [Sandpack](https://sandpack.codesandbox.io/) for code editing
- [PostgreSQL](https://postgresql.org/) for reliable data storage

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/multi-agent-code-generator/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/multi-agent-code-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/multi-agent-code-generator/discussions)
- **Email**: support@your-domain.com

## 🗺️ Roadmap

- [ ] Plugin system for custom agents
- [ ] Advanced code analysis and optimization
- [ ] Multi-language support for UI
- [ ] Integration with more AI providers
- [ ] Kubernetes deployment configurations
- [ ] Advanced monitoring and analytics
- [ ] Code review and suggestion system
- [ ] Team collaboration features

---

**Made with ❤️ for developers who want to code at the speed of thought**
