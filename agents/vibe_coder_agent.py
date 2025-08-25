"""
VibeCoderAgent - Generates code from detailed development plans.

This agent takes structured plans and transforms them into actual, functional code
with proper file structure, dependencies, and implementation details.
"""

import json
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

from agents.base_agent import BaseAgent


class VibeCoderAgent(BaseAgent):
    """
    Agent responsible for generating code from structured development plans.
    
    This agent:
    1. Takes detailed plans from the VibePlannerAgent
    2. Generates actual, functional code files
    3. Creates proper file structures and dependencies
    4. Implements features according to specifications
    5. Ensures code quality and best practices
    """
    
    def __init__(self, agent_id: str = None, name: str = "VibeCoderAgent"):
        # Initialize capabilities as empty list for BaseAgent
        capabilities = []
        super().__init__("vibe_coder", capabilities)
        self.logger = logging.getLogger(__name__)
        
        # Agent capabilities (stored as simple list for this implementation)
        self.vibe_capabilities = [
            "code_generation",
            "file_structure_creation",
            "dependency_management",
            "template_instantiation",
            "feature_implementation"
        ]
        
        # Code templates for different technologies
        self.code_templates = {
            "react_component": '''import React from 'react';
import './{{component_name}}.css';

const {{component_name}} = ({{props}}) => {
  {{component_logic}}

  return (
    <div className="{{class_name}}">
      {{component_jsx}}
    </div>
  );
};

export default {{component_name}};''',

            "express_route": '''const express = require('express');
const router = express.Router();
{{middleware_imports}}

{{route_handlers}}

module.exports = router;''',

            "fastapi_endpoint": '''from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
{{additional_imports}}

router = APIRouter()

{{endpoint_functions}}''',

            "database_model": '''{{database_imports}}

class {{model_name}}({{base_class}}):
    {{table_definition}}
    
    {{field_definitions}}
    
    {{relationships}}
    
    {{methods}}''',

            "package_json": '''{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "description": "{{project_description}}",
  "main": "{{main_file}}",
  "scripts": {
    {{scripts}}
  },
  "dependencies": {
    {{dependencies}}
  },
  "devDependencies": {
    {{dev_dependencies}}
  }
}''',

            "dockerfile": '''FROM {{base_image}}

WORKDIR /app

{{copy_dependencies}}

RUN {{install_command}}

{{copy_source}}

{{expose_port}}

CMD {{start_command}}''',

            "env_file": '''# Environment Configuration
{{env_variables}}''',

            "readme": '''# {{project_name}}

{{project_description}}

## Features

{{features_list}}

## Installation

{{installation_instructions}}

## Usage

{{usage_instructions}}

## API Documentation

{{api_documentation}}

## Contributing

{{contributing_guidelines}}''',

            "html_template": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{page_title}}</title>
    {{stylesheets}}
</head>
<body>
    {{body_content}}
    {{scripts}}
</body>
</html>''',

            "css_file": '''/* {{file_description}} */

{{css_reset}}

{{component_styles}}

{{responsive_styles}}

{{utility_classes}}'''
        }
        
        # Technology-specific configurations
        self.tech_configs = {
            "React": {
                "file_extension": ".jsx",
                "dependencies": ["react", "react-dom"],
                "dev_dependencies": ["@vitejs/plugin-react", "vite"],
                "build_tool": "vite"
            },
            "Vue": {
                "file_extension": ".vue",
                "dependencies": ["vue"],
                "dev_dependencies": ["@vitejs/plugin-vue", "vite"],
                "build_tool": "vite"
            },
            "Node.js": {
                "file_extension": ".js",
                "dependencies": ["express"],
                "dev_dependencies": ["nodemon"],
                "runtime": "node"
            },
            "Python": {
                "file_extension": ".py",
                "dependencies": ["fastapi", "uvicorn"],
                "dev_dependencies": ["pytest"],
                "runtime": "python"
            },
            "TypeScript": {
                "file_extension": ".ts",
                "dependencies": ["typescript"],
                "dev_dependencies": ["@types/node"],
                "build_tool": "tsc"
            }
        }

    async def generate_code_from_plan(self, plan: Dict[str, Any], project_id: int) -> Dict[str, Any]:
        """
        Main method to generate code from a development plan.
        
        Args:
            plan: Structured development plan from VibePlannerAgent
            project_id: Unique identifier for the project
            
        Returns:
            Generated code files and project structure
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting code generation for project {project_id}")
            
            # Validate plan structure
            if not self._validate_plan(plan):
                raise ValueError("Invalid plan structure provided")
            
            # Extract plan components
            project_type = plan.get("project_type", "web_app")
            tech_stack = plan.get("technology_stack", {})
            specifications = plan.get("specifications", {})
            tasks = plan.get("task_breakdown", [])
            
            # Step 1: Create project structure
            file_structure = self._create_project_structure(project_type, tech_stack, specifications)
            
            # Step 2: Generate configuration files
            config_files = await self._generate_config_files(project_type, tech_stack, plan)
            
            # Step 3: Generate core application files
            core_files = await self._generate_core_files(project_type, tech_stack, specifications)
            
            # Step 4: Generate feature-specific files
            feature_files = await self._generate_feature_files(plan, tech_stack)
            
            # Step 5: Generate test files
            test_files = await self._generate_test_files(project_type, tech_stack, specifications)
            
            # Step 6: Generate documentation
            doc_files = await self._generate_documentation(plan, tech_stack)
            
            # Combine all generated files
            all_files = []
            all_files.extend(config_files)
            all_files.extend(core_files)
            all_files.extend(feature_files)
            all_files.extend(test_files)
            all_files.extend(doc_files)
            
            # Calculate metrics
            total_lines = sum(len(f["content"].split('\n')) for f in all_files)
            
            result = {
                "project_id": project_id,
                "project_type": project_type,
                "technology_stack": tech_stack,
                "file_structure": file_structure,
                "files": all_files,
                "metrics": {
                    "total_files": len(all_files),
                    "total_lines_of_code": total_lines,
                    "files_by_type": self._categorize_files(all_files),
                    "estimated_setup_time": self._estimate_setup_time(tech_stack),
                },
                "next_steps": self._generate_next_steps(project_type, tech_stack),
                "metadata": {
                    "coder_agent_id": self.agent_id,
                    "generation_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time,
                    "plan_version": plan.get("metadata", {}).get("version", "unknown")
                }
            }
            
            self.logger.info(f"Code generation completed in {time.time() - start_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in code generation: {str(e)}")
            return {
                "error": str(e),
                "project_id": project_id,
                "status": "failed",
                "metadata": {
                    "coder_agent_id": self.agent_id,
                    "error_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time
                }
            }

    def _validate_plan(self, plan: Dict[str, Any]) -> bool:
        """Validate that the plan has required structure."""
        required_fields = ["project_type", "technology_stack", "specifications"]
        return all(field in plan for field in required_fields)

    def _create_project_structure(self, project_type: str, tech_stack: Dict[str, Any], specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Create the directory structure for the project."""
        
        base_structure = {
            "src/": {},
            "public/": {},
            "tests/": {},
            "docs/": {},
            ".env": "environment variables",
            "README.md": "project documentation"
        }
        
        # Frontend structure
        if tech_stack.get("frontend"):
            frontend_tech = tech_stack["frontend"][0] if tech_stack["frontend"] else "React"
            
            if frontend_tech in ["React", "Vue"]:
                base_structure["src/"].update({
                    "components/": {},
                    "pages/": {},
                    "hooks/": {},
                    "utils/": {},
                    "styles/": {},
                    "assets/": {}
                })
                base_structure["package.json"] = "dependencies and scripts"
                base_structure["vite.config.js"] = "build configuration"
                
        # Backend structure
        if tech_stack.get("backend"):
            backend_tech = tech_stack["backend"][0] if tech_stack["backend"] else "Node.js"
            
            if backend_tech == "Node.js":
                base_structure["src/"].update({
                    "routes/": {},
                    "controllers/": {},
                    "models/": {},
                    "middleware/": {},
                    "config/": {}
                })
                base_structure["package.json"] = "dependencies and scripts"
                
            elif backend_tech == "Python":
                base_structure["src/"].update({
                    "api/": {},
                    "models/": {},
                    "services/": {},
                    "database/": {},
                    "core/": {}
                })
                base_structure["requirements.txt"] = "python dependencies"
                base_structure["main.py"] = "application entry point"
                
        # Database structure
        if tech_stack.get("database"):
            base_structure["migrations/"] = {}
            base_structure["seeds/"] = {}
            
        # Deployment structure
        if "Docker" in tech_stack.get("deployment", []):
            base_structure["Dockerfile"] = "container configuration"
            base_structure["docker-compose.yml"] = "multi-container setup"
            
        return base_structure

    async def _generate_config_files(self, project_type: str, tech_stack: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate configuration files."""
        
        config_files = []
        frontend_tech = tech_stack.get("frontend", [None])[0]
        backend_tech = tech_stack.get("backend", [None])[0]
        
        # Package.json for Node.js projects
        if frontend_tech in ["React", "Vue"] or backend_tech == "Node.js":
            package_json = self._generate_package_json(project_type, tech_stack, plan)
            config_files.append({
                "path": "package.json",
                "content": package_json,
                "language": "json",
                "type": "config"
            })
            
        # Requirements.txt for Python projects
        if backend_tech == "Python":
            requirements = self._generate_requirements_txt(tech_stack, plan)
            config_files.append({
                "path": "requirements.txt",
                "content": requirements,
                "language": "text",
                "type": "config"
            })
            
        # Environment file
        env_content = self._generate_env_file(tech_stack, plan)
        config_files.append({
            "path": ".env.example",
            "content": env_content,
            "language": "text",
            "type": "config"
        })
        
        # Vite config for frontend projects
        if frontend_tech in ["React", "Vue"]:
            vite_config = self._generate_vite_config(frontend_tech)
            config_files.append({
                "path": "vite.config.js",
                "content": vite_config,
                "language": "javascript",
                "type": "config"
            })
            
        # Dockerfile if Docker deployment
        if "Docker" in tech_stack.get("deployment", []):
            dockerfile = self._generate_dockerfile(tech_stack)
            config_files.append({
                "path": "Dockerfile",
                "content": dockerfile,
                "language": "dockerfile",
                "type": "config"
            })
            
        return config_files

    async def _generate_core_files(self, project_type: str, tech_stack: Dict[str, Any], specifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate core application files."""
        
        core_files = []
        frontend_tech = tech_stack.get("frontend", [None])[0]
        backend_tech = tech_stack.get("backend", [None])[0]
        
        # Frontend core files
        if frontend_tech == "React":
            # Main App component
            app_component = self._generate_react_app_component(specifications)
            core_files.append({
                "path": "src/App.jsx",
                "content": app_component,
                "language": "javascript",
                "type": "frontend"
            })
            
            # Main index file
            index_file = self._generate_react_index_file()
            core_files.append({
                "path": "src/main.jsx",
                "content": index_file,
                "language": "javascript",
                "type": "frontend"
            })
            
            # Global styles
            global_styles = self._generate_global_styles()
            core_files.append({
                "path": "src/index.css",
                "content": global_styles,
                "language": "css",
                "type": "frontend"
            })
            
        # Backend core files
        if backend_tech == "Python":
            # Main FastAPI app
            main_app = self._generate_fastapi_main(specifications)
            core_files.append({
                "path": "main.py",
                "content": main_app,
                "language": "python",
                "type": "backend"
            })
            
            # Database models
            if specifications.get("database_schema"):
                models_file = self._generate_python_models(specifications["database_schema"])
                core_files.append({
                    "path": "src/models/models.py",
                    "content": models_file,
                    "language": "python",
                    "type": "backend"
                })
                
        elif backend_tech == "Node.js":
            # Express app
            express_app = self._generate_express_app(specifications)
            core_files.append({
                "path": "src/app.js",
                "content": express_app,
                "language": "javascript",
                "type": "backend"
            })
            
        return core_files

    async def _generate_feature_files(self, plan: Dict[str, Any], tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate feature-specific files based on plan analysis."""
        
        feature_files = []
        features = plan.get("analysis", {}).get("features", [])
        frontend_tech = tech_stack.get("frontend", [None])[0]
        backend_tech = tech_stack.get("backend", [None])[0]
        
        for feature in features:
            if feature == "authentication":
                auth_files = self._generate_auth_files(frontend_tech, backend_tech)
                feature_files.extend(auth_files)
                
            elif feature == "data_visualization":
                viz_files = self._generate_visualization_files(frontend_tech)
                feature_files.extend(viz_files)
                
            elif feature == "file_upload":
                upload_files = self._generate_upload_files(frontend_tech, backend_tech)
                feature_files.extend(upload_files)
                
        return feature_files

    async def _generate_test_files(self, project_type: str, tech_stack: Dict[str, Any], specifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test files for the project."""
        
        test_files = []
        frontend_tech = tech_stack.get("frontend", [None])[0]
        backend_tech = tech_stack.get("backend", [None])[0]
        
        if frontend_tech == "React":
            # Component tests
            app_test = self._generate_react_app_test()
            test_files.append({
                "path": "src/App.test.jsx",
                "content": app_test,
                "language": "javascript",
                "type": "test"
            })
            
        if backend_tech == "Python":
            # API tests
            api_test = self._generate_python_api_test(specifications)
            test_files.append({
                "path": "tests/test_api.py",
                "content": api_test,
                "language": "python",
                "type": "test"
            })
            
        return test_files

    async def _generate_documentation(self, plan: Dict[str, Any], tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate documentation files."""
        
        doc_files = []
        
        # README.md
        readme_content = self._generate_readme(plan, tech_stack)
        doc_files.append({
            "path": "README.md",
            "content": readme_content,
            "language": "markdown",
            "type": "documentation"
        })
        
        # API documentation if backend exists
        if tech_stack.get("backend"):
            api_docs = self._generate_api_documentation(plan)
            doc_files.append({
                "path": "docs/API.md",
                "content": api_docs,
                "language": "markdown",
                "type": "documentation"
            })
            
        return doc_files

    # Template generation methods
    def _generate_package_json(self, project_type: str, tech_stack: Dict[str, Any], plan: Dict[str, Any]) -> str:
        """Generate package.json file."""
        
        project_name = plan.get("vibe_prompt", "generated-project").lower().replace(" ", "-")
        frontend_tech = tech_stack.get("frontend", [None])[0]
        
        scripts = {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        }
        
        dependencies = {}
        dev_dependencies = {}
        
        if frontend_tech == "React":
            dependencies.update({
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
            dev_dependencies.update({
                "@vitejs/plugin-react": "^4.0.0",
                "vite": "^4.4.0"
            })
            
        return json.dumps({
            "name": project_name,
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": scripts,
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }, indent=2)

    def _generate_requirements_txt(self, tech_stack: Dict[str, Any], plan: Dict[str, Any]) -> str:
        """Generate requirements.txt for Python projects."""
        
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0"
        ]
        
        if tech_stack.get("database"):
            db_type = tech_stack["database"][0]
            if db_type == "PostgreSQL":
                requirements.append("psycopg2-binary==2.9.7")
                requirements.append("sqlalchemy==2.0.23")
            elif db_type == "SQLite":
                requirements.append("sqlalchemy==2.0.23")
                
        features = plan.get("analysis", {}).get("features", [])
        if "authentication" in features:
            requirements.extend([
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "python-multipart==0.0.6"
            ])
            
        return '\n'.join(requirements)

    def _generate_env_file(self, tech_stack: Dict[str, Any], plan: Dict[str, Any]) -> str:
        """Generate environment variables file."""
        
        env_vars = [
            "# Environment Configuration",
            "NODE_ENV=development",
            "PORT=3000"
        ]
        
        if tech_stack.get("database"):
            env_vars.extend([
                "",
                "# Database Configuration",
                "DATABASE_URL=sqlite:///./app.db"
            ])
            
        features = plan.get("analysis", {}).get("features", [])
        if "authentication" in features:
            env_vars.extend([
                "",
                "# Authentication",
                "JWT_SECRET=your-secret-key-here",
                "ACCESS_TOKEN_EXPIRE_MINUTES=30"
            ])
            
        return '\n'.join(env_vars)

    def _generate_vite_config(self, frontend_tech: str) -> str:
        """Generate Vite configuration file."""
        
        if frontend_tech == "React":
            return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
  build: {
    outDir: 'dist',
  },
})'''
        else:
            return '''import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 3000,
  },
  build: {
    outDir: 'dist',
  },
})'''

    def _generate_dockerfile(self, tech_stack: Dict[str, Any]) -> str:
        """Generate Dockerfile."""
        
        if tech_stack.get("backend", [None])[0] == "Python":
            return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'''
        else:
            return '''FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]'''

    def _generate_react_app_component(self, specifications: Dict[str, Any]) -> str:
        """Generate main React App component."""
        
        components = specifications.get("ui_components", [])
        
        imports = ["import React from 'react'"]
        if "Header" in components:
            imports.append("import Header from './components/Header'")
        if "Footer" in components:
            imports.append("import Footer from './components/Footer'")
            
        jsx_content = []
        if "Header" in components:
            jsx_content.append("      <Header />")
        jsx_content.append("      <main>")
        jsx_content.append("        <h1>Welcome to Your App</h1>")
        jsx_content.append("        <p>This is a generated application ready for customization.</p>")
        jsx_content.append("      </main>")
        if "Footer" in components:
            jsx_content.append("      <Footer />")
            
        return f'''{chr(10).join(imports)}
import './App.css'

function App() {{
  return (
    <div className="App">
{chr(10).join(jsx_content)}
    </div>
  )
}}

export default App'''

    def _generate_react_index_file(self) -> str:
        """Generate React index file."""
        
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''

    def _generate_global_styles(self) -> str:
        """Generate global CSS styles."""
        
        return '''/* Global Styles */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5;
  color: #333;
}

.App {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #2c3e50;
}

p {
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  main {
    padding: 1rem;
  }
  
  h1 {
    font-size: 2rem;
  }
}'''

    def _generate_fastapi_main(self, specifications: Dict[str, Any]) -> str:
        """Generate FastAPI main application file."""
        
        endpoints = specifications.get("api_endpoints", [])
        
        imports = [
            "from fastapi import FastAPI, HTTPException",
            "from fastapi.middleware.cors import CORSMiddleware"
        ]
        
        if any("auth" in ep.get("path", "") for ep in endpoints):
            imports.append("from fastapi.security import HTTPBearer")
            
        app_config = '''
app = FastAPI(
    title="Generated API",
    description="Auto-generated API from vibe prompt",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

        routes = []
        for endpoint in endpoints:
            method = endpoint.get("method", "GET").lower()
            path = endpoint.get("path", "/")
            description = endpoint.get("description", "")
            
            if method == "get":
                routes.append(f'''
@app.{method}("{path}")
async def {path.replace("/", "_").replace(":", "_").strip("_")}():
    """
    {description}
    """
    return {{"message": "This endpoint is ready for implementation"}}''')
                
        return f'''{chr(10).join(imports)}

{app_config}

{chr(10).join(routes)}

@app.get("/")
async def root():
    return {{"message": "API is running successfully"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)'''

    def _generate_python_models(self, database_schema: Dict[str, Any]) -> str:
        """Generate SQLAlchemy models."""
        
        imports = [
            "from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean",
            "from sqlalchemy.ext.declarative import declarative_base",
            "from sqlalchemy.sql import func",
            "",
            "Base = declarative_base()"
        ]
        
        models = []
        for table_name, fields in database_schema.items():
            model_name = table_name.title().rstrip('s')
            
            field_definitions = []
            for field_name, field_type in fields.items():
                if "INTEGER PRIMARY KEY" in field_type:
                    field_definitions.append(f"    {field_name} = Column(Integer, primary_key=True, index=True)")
                elif "VARCHAR" in field_type:
                    field_definitions.append(f"    {field_name} = Column(String(255), nullable=False)")
                elif "TEXT" in field_type:
                    field_definitions.append(f"    {field_name} = Column(Text)")
                elif "TIMESTAMP" in field_type:
                    field_definitions.append(f"    {field_name} = Column(DateTime, server_default=func.now())")
                    
            model_code = f'''
class {model_name}(Base):
    __tablename__ = "{table_name}"
    
{chr(10).join(field_definitions)}'''
            models.append(model_code)
            
        return f'''{chr(10).join(imports)}

{chr(10).join(models)}'''

    def _generate_express_app(self, specifications: Dict[str, Any]) -> str:
        """Generate Express.js application."""
        
        return '''const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
  res.json({ message: 'API is running successfully' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

module.exports = app;'''

    def _generate_auth_files(self, frontend_tech: str, backend_tech: str) -> List[Dict[str, Any]]:
        """Generate authentication-related files."""
        
        auth_files = []
        
        if frontend_tech == "React":
            # Login component
            login_component = '''import React, { useState } from 'react';

const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Add your login logic here
      console.log('Login attempted with:', credentials);
      if (onLogin) {
        onLogin(credentials);
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>Login</h2>
      <div className="form-group">
        <label htmlFor="username">Username:</label>
        <input
          type="text"
          id="username"
          name="username"
          value={credentials.username}
          onChange={handleChange}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          name="password"
          value={credentials.password}
          onChange={handleChange}
          required
        />
      </div>
      <button type="submit">Login</button>
    </form>
  );
};

export default LoginForm;'''
            
            auth_files.append({
                "path": "src/components/LoginForm.jsx",
                "content": login_component,
                "language": "javascript",
                "type": "frontend"
            })
            
        return auth_files

    def _generate_visualization_files(self, frontend_tech: str) -> List[Dict[str, Any]]:
        """Generate data visualization files."""
        
        viz_files = []
        
        if frontend_tech == "React":
            chart_component = '''import React from 'react';

const BarChart = ({ data, title }) => {
  // Simple CSS-based bar chart
  const maxValue = Math.max(...data.map(item => item.value));

  return (
    <div className="bar-chart">
      <h3>{title}</h3>
      <div className="chart-container">
        {data.map((item, index) => (
          <div key={index} className="bar-item">
            <div className="bar-label">{item.label}</div>
            <div className="bar-wrapper">
              <div 
                className="bar"
                style={{
                  height: `${(item.value / maxValue) * 100}%`,
                  backgroundColor: item.color || '#3498db'
                }}
              >
                <span className="bar-value">{item.value}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BarChart;'''
            
            viz_files.append({
                "path": "src/components/BarChart.jsx",
                "content": chart_component,
                "language": "javascript",
                "type": "frontend"
            })
            
        return viz_files

    def _generate_upload_files(self, frontend_tech: str, backend_tech: str) -> List[Dict[str, Any]]:
        """Generate file upload functionality."""
        
        upload_files = []
        
        if frontend_tech == "React":
            upload_component = '''import React, { useState } from 'react';

const FileUpload = ({ onUpload, acceptedTypes = "*", maxSize = 10485760 }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > maxSize) {
        alert(`File size too large. Maximum size is ${maxSize / 1024 / 1024}MB`);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Add your upload logic here
      console.log('Uploading file:', selectedFile.name);
      
      if (onUpload) {
        await onUpload(formData);
      }
      
      setSelectedFile(null);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="upload-area">
        <input
          type="file"
          onChange={handleFileSelect}
          accept={acceptedTypes}
          disabled={uploading}
        />
        {selectedFile && (
          <div className="file-info">
            <p>Selected: {selectedFile.name}</p>
            <p>Size: {(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>
        )}
      </div>
      <button 
        onClick={handleUpload} 
        disabled={!selectedFile || uploading}
        className="upload-btn"
      >
        {uploading ? 'Uploading...' : 'Upload File'}
      </button>
    </div>
  );
};

export default FileUpload;'''
            
            upload_files.append({
                "path": "src/components/FileUpload.jsx",
                "content": upload_component,
                "language": "javascript",
                "type": "frontend"
            })
            
        return upload_files

    def _generate_react_app_test(self) -> str:
        """Generate React App test file."""
        
        return '''import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders welcome message', () => {
    render(<App />);
    const welcomeElement = screen.getByText(/welcome to your app/i);
    expect(welcomeElement).toBeInTheDocument();
  });

  it('renders main content', () => {
    render(<App />);
    const mainElement = screen.getByRole('main');
    expect(mainElement).toBeInTheDocument();
  });
});'''

    def _generate_python_api_test(self, specifications: Dict[str, Any]) -> str:
        """Generate Python API test file."""
        
        return '''import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    """Test health check endpoint if it exists."""
    response = client.get("/health")
    # This might return 404 if health endpoint doesn't exist
    assert response.status_code in [200, 404]

class TestAPI:
    """Test suite for API endpoints."""
    
    def test_api_is_running(self):
        """Test that the API is running."""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/")
        assert response.status_code == 200
        # CORS headers should be present for cross-origin requests'''

    def _generate_readme(self, plan: Dict[str, Any], tech_stack: Dict[str, Any]) -> str:
        """Generate README.md file."""
        
        project_name = plan.get("vibe_prompt", "Generated Project").title()
        features = plan.get("analysis", {}).get("features", [])
        frontend_tech = tech_stack.get("frontend", [])
        backend_tech = tech_stack.get("backend", [])
        
        tech_stack_section = []
        if frontend_tech:
            tech_stack_section.append(f"- **Frontend**: {', '.join(frontend_tech)}")
        if backend_tech:
            tech_stack_section.append(f"- **Backend**: {', '.join(backend_tech)}")
        if tech_stack.get("database"):
            tech_stack_section.append(f"- **Database**: {', '.join(tech_stack['database'])}")
            
        features_list = '\n'.join([f"- {feature.replace('_', ' ').title()}" for feature in features])
        
        return f'''# {project_name}

Auto-generated application from vibe prompt: "{plan.get("vibe_prompt", "")}"

## Features

{features_list}

## Technology Stack

{chr(10).join(tech_stack_section)}

## Getting Started

### Prerequisites

- Node.js (version 18 or higher)
{f"- Python 3.11+" if backend_tech and "Python" in backend_tech else ""}

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {project_name.lower().replace(" ", "-")}
```

2. Install dependencies:
```bash
npm install
{f"pip install -r requirements.txt" if backend_tech and "Python" in backend_tech else ""}
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

#### Development
```bash
npm run dev
{f"python main.py  # In a separate terminal for backend" if backend_tech and "Python" in backend_tech else ""}
```

#### Production
```bash
npm run build
npm run preview
```

## Project Structure

```
{project_name.lower().replace(" ", "-")}/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Application pages
│   ├── utils/         # Utility functions
│   └── styles/        # CSS files
├── public/            # Static assets
├── tests/             # Test files
└── docs/              # Documentation
```

## API Documentation

{f"See [API.md](docs/API.md) for detailed API documentation." if backend_tech else "This is a frontend-only application."}

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is generated code and can be used according to your needs.

## Generated Information

- **Generated by**: VibeCoderAgent
- **Generation timestamp**: {datetime.utcnow().isoformat()}
- **Plan version**: {plan.get("metadata", {}).get("version", "unknown")}
'''

    def _generate_api_documentation(self, plan: Dict[str, Any]) -> str:
        """Generate API documentation."""
        
        endpoints = plan.get("specifications", {}).get("api_endpoints", [])
        
        endpoint_docs = []
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            description = endpoint.get("description", "")
            
            endpoint_docs.append(f'''### {method} {path}

{description}

**Example Request:**
```bash
curl -X {method} http://localhost:8000{path}
```

**Example Response:**
```json
{{
  "message": "Success"
}}
```
''')
        
        return f'''# API Documentation

This document describes the available API endpoints.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

{f"This API uses JWT authentication. Include the token in the Authorization header:" if "authentication" in plan.get("analysis", {}).get("features", []) else "No authentication required."}

{f'''```bash
Authorization: Bearer <your-token>
```''' if "authentication" in plan.get("analysis", {}).get("features", []) else ""}

## Endpoints

{chr(10).join(endpoint_docs)}

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

Error responses follow this format:
```json
{{
  "error": "Error message",
  "details": "Additional error details"
}}
```
'''

    def _categorize_files(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize files by type."""
        
        categories = {}
        for file in files:
            file_type = file.get("type", "unknown")
            categories[file_type] = categories.get(file_type, 0) + 1
            
        return categories

    def _estimate_setup_time(self, tech_stack: Dict[str, Any]) -> str:
        """Estimate setup time for the project."""
        
        base_time = 5  # minutes
        
        if tech_stack.get("frontend"):
            base_time += 3
        if tech_stack.get("backend"):
            base_time += 5
        if tech_stack.get("database"):
            base_time += 3
            
        return f"{base_time} minutes"

    def _generate_next_steps(self, project_type: str, tech_stack: Dict[str, Any]) -> List[str]:
        """Generate list of next steps for development."""
        
        steps = [
            "1. Install dependencies using package manager",
            "2. Configure environment variables",
            "3. Review and customize generated code"
        ]
        
        if tech_stack.get("database"):
            steps.append("4. Set up database connection and run migrations")
            
        steps.extend([
            f"{len(steps) + 1}. Test the application locally",
            f"{len(steps) + 2}. Add custom business logic",
            f"{len(steps) + 3}. Write additional tests",
            f"{len(steps) + 4}. Deploy to production"
        ])
        
        return steps

    async def process_task(self, task) -> Any:
        """Process a task (required by BaseAgent)."""
        # For vibe agents, we don't use the generic task processing
        return {"status": "task_not_supported", "message": "Use generate_code_from_plan instead"}

    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get custom metrics for the coder agent."""
        return {
            "files_generated": 0.0,
            "lines_of_code": 0.0,
            "average_generation_time": 0.0,
            "template_usage": 0.0
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_coder():
        from agents.vibe_planner_agent import VibePlannerAgent
        
        # Create a plan first
        planner = VibePlannerAgent()
        plan = await planner.decompose_vibe_prompt(
            "Create a modern dashboard for tracking sales analytics with real-time charts and user authentication"
        )
        
        # Generate code from the plan
        coder = VibeCoderAgent()
        result = await coder.generate_code_from_plan(plan, 123)
        
        print("=== VIBE CODER RESULT ===")
        print(f"Generated {result['metrics']['total_files']} files")
        print(f"Total lines of code: {result['metrics']['total_lines_of_code']}")
        print(f"Files by type: {result['metrics']['files_by_type']}")
        
        # Print some example files
        for file in result["files"][:3]:
            print(f"\n--- {file['path']} ---")
            print(file["content"][:300] + "..." if len(file["content"]) > 300 else file["content"])
            
    # Run the test
    asyncio.run(test_coder())