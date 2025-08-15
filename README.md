---
title: Multi-Agent Code Generator
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🤖 Multi-Agent Code Generator

An intelligent code generation platform powered by **CrewAI** and **OpenAI** that automatically creates complete software projects from natural language descriptions using collaborative AI agents.

## ✨ Features

- 🧠 **4 Specialized AI Agents**: Planner, Code Generator, Tester, and Documentation Generator
- 🌐 **Persian/Farsi UI**: Full RTL-supported interface with Persian localization
- ⚡ **Real-time Collaboration**: Live WebSocket updates and interactive chat
- 🎨 **Advanced Code Editor**: Sandpack integration for live code preview and editing
- 🔒 **Production Ready**: JWT authentication, rate limiting, comprehensive testing
- 📦 **Complete Projects**: Download full projects as ZIP files with all dependencies
- 🔄 **Multi-Language Support**: Python, JavaScript, HTML/CSS, and more
- 📊 **Project Templates**: Pre-built templates for web apps, APIs, and data science projects

## 🚀 Quick Start

### 1. **Enter Project Requirements**
Describe your project in natural language - be as detailed or as simple as you want!

### 2. **Watch AI Agents Work**
See real-time progress as our specialized agents collaborate:
- **Planner Agent** analyzes your requirements
- **Code Generator** creates production-ready code
- **Tester Agent** writes comprehensive test suites
- **Documentation Generator** creates docs and README files

### 3. **Download Complete Project**
Get a fully functional project with:
- ✅ Clean, documented code
- ✅ Comprehensive test suite
- ✅ Complete documentation
- ✅ All dependencies and configuration files

## 🏗️ Architecture

```
Frontend (HTML/JS/CSS) ↔ FastAPI Backend ↔ SQLite Database
                              ↕
                        CrewAI Agents
                              ↕
                        OpenAI GPT-4 API
```

## 🤖 AI Agents

### **PlannerAgent** 📋
- Analyzes user requirements and technical specifications
- Creates detailed project structure and development roadmap
- Identifies optimal technologies and frameworks
- Plans file organization and dependency management

### **CodeGeneratorAgent** 💻
- Generates production-ready, clean, and efficient code
- Implements best practices and design patterns
- Creates modular and maintainable code structure
- Handles error handling and edge cases

### **TesterAgent** 🧪
- Creates comprehensive test suites with high coverage
- Generates unit tests, integration tests, and end-to-end tests
- Implements test automation and CI/CD configurations
- Ensures code quality and reliability

### **DocGeneratorAgent** 📚
- Generates comprehensive documentation and README files
- Creates API documentation and code comments
- Produces user guides and developer documentation
- Ensures project maintainability and knowledge transfer

## 💻 Usage Examples

### Web Interface
1. Open the application in your browser
2. Fill out the project form with your requirements:
   - **Project Name**: "My Blog Platform"
   - **Description**: "A modern blog platform with user authentication"
   - **Type**: Web Application
   - **Languages**: Python, JavaScript
   - **Frameworks**: FastAPI, React
3. Watch the AI agents collaborate in real-time
4. Download your complete, production-ready project

### API Usage
```bash
curl -X POST "https://huggingface.co/spaces/Really-amin/ultichat-hugginigfae/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce API",
    "description": "REST API for e-commerce platform with payment integration",
    "project_type": "api",
    "languages": ["python"],
    "frameworks": ["fastapi"],
    "features": ["authentication", "payment", "inventory"]
  }'
```

### WebSocket Real-time Updates
```javascript
const ws = new WebSocket('wss://huggingface.co/spaces/Really-amin/ultichat-hugginigfae/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent Update:', data);
};
```

## 🔧 Configuration

The application uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | None |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Auto-generated |
| `MAX_CONCURRENT_GENERATIONS` | Max concurrent generations | 3 |
| `DATABASE_URL` | Database connection string | SQLite |
| `PORT` | Server port (HF Spaces uses 7860) | 7860 |

## 🌟 Project Types Supported

- **Web Applications**: Full-stack web apps with frontend and backend
- **REST APIs**: Complete API services with documentation
- **Data Science**: ML/AI projects with Jupyter notebooks
- **CLI Tools**: Command-line applications and utilities
- **Microservices**: Scalable microservice architectures
- **Mobile Apps**: React Native and Flutter applications

## 🎯 Use Cases

- **Rapid Prototyping**: Quickly create MVP versions of your ideas
- **Learning Projects**: Generate educational code examples and tutorials
- **Boilerplate Generation**: Create project templates and starter code
- **Code Architecture**: Get suggestions for optimal project structure
- **Documentation**: Auto-generate comprehensive project documentation

## 🔒 Security & Privacy

- **No Code Storage**: Generated code is not stored on our servers
- **Secure API Keys**: Your OpenAI API key is handled securely
- **Rate Limiting**: Built-in protection against abuse
- **Input Validation**: All inputs are validated and sanitized

## 📈 Performance

- **Fast Generation**: Average project generation in 2-5 minutes
- **High Quality**: Code follows industry best practices
- **Scalable**: Supports projects from simple scripts to complex applications
- **Reliable**: Built-in error handling and recovery mechanisms

## 🤝 Contributing

This project is automatically deployed from GitHub. To contribute:

1. Fork the [GitHub repository](https://github.com/YOUR_USERNAME/multi-agent-code-generator)
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with descriptive messages: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Submit a pull request

## 🐛 Issues & Support

- **Bug Reports**: [GitHub Issues](https://github.com/YOUR_USERNAME/multi-agent-code-generator/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/YOUR_USERNAME/multi-agent-code-generator/discussions)
- **Documentation**: [Full Documentation](https://github.com/YOUR_USERNAME/multi-agent-code-generator/docs)

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub Repository**: [Source Code](https://github.com/YOUR_USERNAME/multi-agent-code-generator)
- **Live Demo**: [Hugging Face Spaces](https://huggingface.co/spaces/Really-amin/ultichat-hugginigfae)
- **API Documentation**: [Interactive API Docs](https://huggingface.co/spaces/Really-amin/ultichat-hugginigfae/docs)

## 🏆 Technologies Used

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **AI Framework**: CrewAI, OpenAI GPT-4
- **Database**: SQLite (production), PostgreSQL (scalable option)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **WebSockets**: Real-time communication
- **Authentication**: JWT tokens
- **Testing**: Pytest, AsyncIO testing
- **Deployment**: Docker, Hugging Face Spaces

---

<div align="center">

**Built with ❤️ using CrewAI, OpenAI, and FastAPI**

*Transform your ideas into production-ready code with AI-powered multi-agent collaboration*

</div>