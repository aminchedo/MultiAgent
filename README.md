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
```

## 🚀 Quick Start

### Hugging Face Spaces Deployment

1. **Quick Deploy**:
```bash
chmod +x quick-deploy-test.sh
./quick-deploy-test.sh
```

2. **Manual Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your_openai_api_key"
export JWT_SECRET_KEY="your_jwt_secret_key"

# Run the application
python app.py
```

### Local Development

1. **Clone and Setup**:
```bash
git clone <repository_url>
cd multi-agent-code-generation
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp config/config.example.json config/config.json
# Edit config.json with your API keys
```

3. **Run the Application**:
```bash
# Development mode
python simple_run.py

# Production mode
python app.py
```

## 📝 Environment Variables

Required for production deployment:

- `OPENAI_API_KEY`: Your OpenAI API key
- `JWT_SECRET_KEY`: Secret key for JWT authentication
- `DATABASE_URL`: PostgreSQL connection string (optional)
- `REDIS_URL`: Redis connection string (optional)

## 🤖 Multi-Agent System

### Agents

1. **Planning Agent**: Analyzes requirements and creates project structure
2. **Code Generation Agent**: Writes high-quality, production-ready code
3. **Testing Agent**: Generates comprehensive test suites
4. **Documentation Agent**: Creates detailed documentation
5. **Review Agent**: Performs code review and quality assurance

### Workflow

```
User Request → Planning → Code Generation → Testing → Documentation → Review → Final Output
```

## 🌐 Deployment Options

### Hugging Face Spaces (Recommended)
- Automatic deployment with the provided scripts
- Gradio interface for easy interaction
- Built-in CI/CD pipeline

### Vercel
- Fast, global edge deployment
- Automatic SSL and custom domains
- Serverless functions support

### Docker
```bash
docker build -t multi-agent-code-gen .
docker run -p 8000:8000 multi-agent-code-gen
```

## 📚 API Documentation

Once deployed, visit `/docs` for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

### Key Endpoints

- `POST /api/generate`: Generate code from natural language
- `POST /api/chat`: Interactive chat with agents
- `GET /api/health`: Health check endpoint
- `WebSocket /ws`: Real-time updates and collaboration

## 🔧 Configuration

The system is highly configurable through `config/config.json`:

```json
{
  "agents": {
    "planning_agent": {
      "model": "gpt-4",
      "temperature": 0.1
    },
    "code_agent": {
      "model": "gpt-4",
      "temperature": 0.2
    }
  },
  "ui": {
    "language": "fa",
    "rtl": true
  }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/backend/
pytest tests/frontend/
pytest tests/integration/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the deployment guides

## 🎯 Roadmap

- [ ] Support for more programming languages
- [ ] Advanced code optimization features
- [ ] Integration with more AI models
- [ ] Enhanced collaboration features
- [ ] Mobile application support

---

**Happy Coding! 🚀**