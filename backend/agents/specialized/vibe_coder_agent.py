"""
Enhanced Coder Agent specialized for Vibe Coding - generating complete, production-ready code from plans.
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from backend.agents.base.base_agent import BaseCrewAgent
from backend.agents.agents import AgentTools
from backend.models.models import generate_task_id
from config.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class VibeCoderAgent(BaseCrewAgent):
    """
    Specialized Coder Agent for generating complete, production-ready code from technical plans.
    This agent focuses on creating maintainable, modern code that matches the user's vibe.
    """

    def __init__(self, job_id: str, websocket_callback: Optional[callable] = None):
        super().__init__(job_id, websocket_callback)
        self.code_templates = self._load_code_templates()
        self.style_patterns = self._load_style_patterns()

    def _load_code_templates(self) -> Dict[str, Any]:
        """Load code templates for different project types."""
        return {
            "react_component": '''import React from 'react';
import './{{component_name}}.css';

const {{component_name}} = () => {
  return (
    <div className="{{css_class}}">
      {{component_content}}
    </div>
  );
};

export default {{component_name}};''',

            "react_app": '''import React from 'react';
import './App.css';
{{imports}}

function App() {
  return (
    <div className="App">
      {{app_content}}
    </div>
  );
}

export default App;''',

            "package_json": '''{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    {{dependencies}}
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}''',

            "tailwind_css": '''@tailwind base;
@tailwind components;
@tailwind utilities;

{{custom_styles}}''',

            "fastapi_main": '''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
{{imports}}

app = FastAPI(title="{{project_name}}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

{{models}}

{{endpoints}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)''',

            "html_template": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    {{css_links}}
    <style>{{custom_css}}</style>
</head>
<body>
    {{body_content}}
    {{js_scripts}}
</body>
</html>'''
        }

    def _load_style_patterns(self) -> Dict[str, Any]:
        """Load style patterns for different vibes."""
        return {
            "modern": {
                "colors": ["bg-white", "text-gray-800", "border-gray-200"],
                "spacing": ["p-6", "m-4", "space-y-4"],
                "typography": ["font-sans", "text-lg", "font-medium"],
                "effects": ["shadow-lg", "rounded-lg", "hover:shadow-xl"]
            },
            "dark": {
                "colors": ["bg-gray-900", "text-white", "border-gray-700"],
                "spacing": ["p-6", "m-4", "space-y-4"],
                "typography": ["font-sans", "text-lg", "font-medium"],
                "effects": ["shadow-xl", "rounded-lg", "hover:bg-gray-800"]
            },
            "colorful": {
                "colors": ["bg-gradient-to-r", "from-purple-400", "to-pink-400", "text-white"],
                "spacing": ["p-8", "m-6", "space-y-6"],
                "typography": ["font-bold", "text-xl"],
                "effects": ["shadow-2xl", "rounded-2xl", "hover:scale-105", "transition-transform"]
            },
            "minimal": {
                "colors": ["bg-gray-50", "text-gray-600", "border-gray-100"],
                "spacing": ["p-4", "m-2", "space-y-2"],
                "typography": ["font-light", "text-base"],
                "effects": ["shadow-sm", "rounded", "hover:shadow-md"]
            },
            "professional": {
                "colors": ["bg-blue-50", "text-blue-900", "border-blue-200"],
                "spacing": ["p-6", "m-4", "space-y-4"],
                "typography": ["font-medium", "text-lg"],
                "effects": ["shadow-md", "rounded-lg", "hover:bg-blue-100"]
            }
        }

    async def generate_code(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main method to generate complete code from a technical plan.
        
        Args:
            plan: Structured technical plan from the Planner Agent
            
        Returns:
            List of generated code files with content, language, and metadata
        """
        await self.log_message("Starting code generation from technical plan")
        await self.update_progress(20, "Initializing code generation", 2)

        # Extract key information from plan
        vibe_analysis = plan.get("vibe_analysis", {})
        project_spec = plan.get("project_specification", {})
        technical_plan = plan.get("technical_plan", {})
        file_structure = plan.get("file_structure", {})
        task_breakdown = plan.get("task_breakdown", [])

        # Determine coding style based on vibe
        coding_style = await self._determine_coding_style(vibe_analysis)
        
        # Generate files in dependency order
        generated_files = []
        
        # Phase 1: Configuration files
        config_files = await self._generate_configuration_files(plan, coding_style)
        generated_files.extend(config_files)
        await self.update_progress(30, "Generated configuration files", 2)

        # Phase 2: Core application files
        core_files = await self._generate_core_files(plan, coding_style)
        generated_files.extend(core_files)
        await self.update_progress(50, "Generated core application files", 2)

        # Phase 3: Components and features
        component_files = await self._generate_component_files(plan, coding_style)
        generated_files.extend(component_files)
        await self.update_progress(70, "Generated component files", 2)

        # Phase 4: Styling and assets
        style_files = await self._generate_style_files(plan, coding_style)
        generated_files.extend(style_files)
        await self.update_progress(80, "Generated styling files", 2)

        # Phase 5: Backend files (if needed)
        if project_spec.get("backend_needed", False):
            backend_files = await self._generate_backend_files(plan, coding_style)
            generated_files.extend(backend_files)
            await self.update_progress(90, "Generated backend files", 2)

        await self.log_message(
            f"Code generation completed: {len(generated_files)} files generated",
            metadata={
                "total_files": len(generated_files),
                "coding_style": coding_style["name"],
                "project_type": project_spec.get("type")
            }
        )

        return generated_files

    async def _determine_coding_style(self, vibe_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine coding style and patterns based on vibe analysis."""
        
        ui_requirements = vibe_analysis.get("ui_requirements", [])
        key_emotions = vibe_analysis.get("key_emotions", [])
        
        # Determine primary style theme
        style_theme = "modern"  # default
        
        if any(mood in ui_requirements + key_emotions for mood in ["dark", "night", "black"]):
            style_theme = "dark"
        elif any(mood in ui_requirements + key_emotions for mood in ["colorful", "vibrant", "bright", "gradient"]):
            style_theme = "colorful"
        elif any(mood in ui_requirements + key_emotions for mood in ["minimal", "clean", "simple"]):
            style_theme = "minimal"
        elif any(mood in ui_requirements + key_emotions for mood in ["professional", "business", "corporate"]):
            style_theme = "professional"

        style_config = self.style_patterns.get(style_theme, self.style_patterns["modern"])
        
        return {
            "name": style_theme,
            "config": style_config,
            "naming_convention": "camelCase",
            "component_style": "functional",
            "code_style": "modern_es6",
            "formatting": {
                "indent": 2,
                "quotes": "single",
                "semicolons": True
            }
        }

    async def _generate_configuration_files(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate configuration files (package.json, README.md, etc.)."""
        
        project_spec = plan.get("project_specification", {})
        vibe_analysis = plan.get("vibe_analysis", {})
        tech_stack = project_spec.get("technology_stack", {})
        
        files = []
        
        # Generate package.json for React projects
        if tech_stack.get("frontend") in ["react", "next.js"]:
            package_json = await self._generate_package_json(plan, coding_style)
            files.append(package_json)
        
        # Generate README.md
        readme = await self._generate_readme(plan, coding_style)
        files.append(readme)
        
        # Generate requirements.txt for Python backend
        if project_spec.get("backend_needed", False):
            requirements = await self._generate_requirements_txt(plan, coding_style)
            files.append(requirements)
        
        # Generate .gitignore
        gitignore = await self._generate_gitignore(plan, coding_style)
        files.append(gitignore)
        
        return files

    async def _generate_package_json(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate package.json file."""
        
        project_spec = plan.get("project_specification", {})
        vibe_analysis = plan.get("vibe_analysis", {})
        tech_stack = project_spec.get("technology_stack", {})
        
        # Determine dependencies based on requirements
        dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1"
        }
        
        # Add styling dependencies
        if tech_stack.get("styling") == "tailwindcss":
            dependencies.update({
                "tailwindcss": "^3.3.0",
                "autoprefixer": "^10.4.14",
                "postcss": "^8.4.24"
            })
        
        # Add feature-specific dependencies
        features = str(vibe_analysis.get("core_features", [])).lower()
        if "chart" in features:
            dependencies["recharts"] = "^2.7.2"
        if "animation" in features or coding_style["name"] == "colorful":
            dependencies["framer-motion"] = "^10.12.16"
        if "icon" in features:
            dependencies["lucide-react"] = "^0.263.1"
        if "form" in features:
            dependencies["react-hook-form"] = "^7.45.1"
        if "router" in features or "page" in features:
            dependencies["react-router-dom"] = "^6.14.1"
        
        project_name = self._generate_project_name(vibe_analysis)
        
        deps_string = ",\n    ".join([f'"{k}": "{v}"' for k, v in dependencies.items()])
        
        content = self.code_templates["package_json"].replace("{{project_name}}", project_name).replace("{{dependencies}}", deps_string)
        
        return {
            "path": "package.json",
            "filename": "package.json",
            "content": content,
            "language": "json",
            "metadata": {
                "file_type": "configuration",
                "dependencies_count": len(dependencies)
            }
        }

    async def _generate_readme(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive README.md file."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        project_spec = plan.get("project_specification", {})
        original_vibe = plan.get("original_vibe", "")
        
        project_name = self._generate_project_name(vibe_analysis)
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        readme_writer = self.create_agent(
            role="Technical Documentation Specialist",
            goal="Create comprehensive, user-friendly README files",
            backstory="""You are an expert technical writer who creates clear, 
            engaging documentation. You excel at explaining complex projects in 
            simple terms and providing practical setup instructions.""",
            tools=tools
        )

        readme_task = Task(
            description=f"""
            Create a comprehensive README.md file for this project:
            
            Original User Vibe: "{original_vibe}"
            Project Name: {project_name}
            Project Type: {project_spec.get("type", "web application")}
            Technology Stack: {project_spec.get("technology_stack", {})}
            Complexity: {project_spec.get("complexity", "moderate")}
            
            The README should include:
            1. **Project Title** - Clear, descriptive title
            2. **Description** - What the project does and why it's useful
            3. **Features** - Key features and capabilities
            4. **Installation** - Step-by-step setup instructions
            5. **Usage** - How to use the application
            6. **Project Structure** - Overview of key files and folders
            7. **Technologies Used** - List of frameworks and libraries
            8. **Contributing** - How others can contribute
            9. **License** - MIT License information
            
            Make it engaging and professional. Include emojis and clear formatting.
            Focus on the user's original vibe and make it sound exciting!
            """,
            agent=readme_writer,
            expected_output="Complete README.md file in markdown format"
        )

        crew = Crew(
            agents=[readme_writer],
            tasks=[readme_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        content = await self.execute_crew_with_retry(crew, {})
        
        return {
            "path": "README.md",
            "filename": "README.md",
            "content": str(content),
            "language": "markdown",
            "metadata": {
                "file_type": "documentation",
                "generated_from_vibe": original_vibe
            }
        }

    async def _generate_core_files(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate core application files."""
        
        project_spec = plan.get("project_specification", {})
        tech_stack = project_spec.get("technology_stack", {})
        
        files = []
        
        if tech_stack.get("frontend") == "react":
            # Generate App.jsx
            app_file = await self._generate_react_app(plan, coding_style)
            files.append(app_file)
            
            # Generate index.js
            index_file = await self._generate_react_index(plan, coding_style)
            files.append(index_file)
            
            # Generate public/index.html
            html_file = await self._generate_html_template(plan, coding_style)
            files.append(html_file)
            
        elif tech_stack.get("frontend") == "html":
            # Generate standalone HTML file
            html_file = await self._generate_standalone_html(plan, coding_style)
            files.append(html_file)
            
            # Generate CSS file
            css_file = await self._generate_standalone_css(plan, coding_style)
            files.append(css_file)
            
            # Generate JavaScript file
            js_file = await self._generate_standalone_js(plan, coding_style)
            files.append(js_file)
        
        return files

    async def _generate_react_app(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the main React App component."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        project_spec = plan.get("project_specification", {})
        technical_plan = plan.get("technical_plan", {})
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        react_developer = self.create_agent(
            role="Senior React Developer",
            goal="Create modern, functional React components with best practices",
            backstory="""You are a senior React developer with expertise in modern 
            React patterns, hooks, and component architecture. You write clean, 
            maintainable code that follows React best practices.""",
            tools=tools
        )

        app_task = Task(
            description=f"""
            Create the main React App component for this project:
            
            Original Vibe: {plan.get("original_vibe", "")}
            Project Features: {vibe_analysis.get("core_features", [])}
            UI Requirements: {vibe_analysis.get("ui_requirements", [])}
            Coding Style: {coding_style["name"]}
            Style Config: {coding_style["config"]}
            
            Requirements:
            1. Use functional components with hooks
            2. Include proper component structure and organization
            3. Apply the determined style theme: {coding_style["name"]}
            4. Include main features identified in the vibe analysis
            5. Use modern React patterns (useState, useEffect as needed)
            6. Include proper imports and exports
            7. Make it responsive and accessible
            8. Include comments explaining key functionality
            
            The component should reflect the user's original vibe and be production-ready.
            Use Tailwind CSS classes if styling framework is tailwindcss.
            """,
            agent=react_developer,
            expected_output="Complete React App.jsx component code"
        )

        crew = Crew(
            agents=[react_developer],
            tasks=[app_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        content = await self.execute_crew_with_retry(crew, {})
        
        return {
            "path": "src/App.jsx",
            "filename": "App.jsx",
            "content": str(content),
            "language": "javascript",
            "metadata": {
                "file_type": "component",
                "framework": "react",
                "style_theme": coding_style["name"]
            }
        }

    async def _generate_react_index(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate React index.js entry point."""
        
        content = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''

        return {
            "path": "src/index.js",
            "filename": "index.js",
            "content": content,
            "language": "javascript",
            "metadata": {
                "file_type": "entry_point",
                "framework": "react"
            }
        }

    async def _generate_html_template(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HTML template for React app."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        project_name = self._generate_project_name(vibe_analysis)
        
        content = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="{project_name} - Created with Vibe Coding Platform"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>'''

        return {
            "path": "public/index.html",
            "filename": "index.html",
            "content": content,
            "language": "html",
            "metadata": {
                "file_type": "template",
                "framework": "react"
            }
        }

    async def _generate_component_files(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate individual component files based on features."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        features = vibe_analysis.get("core_features", [])
        
        files = []
        
        # Generate components based on identified features
        for feature in features:
            if isinstance(feature, str):
                component_file = await self._generate_feature_component(feature, plan, coding_style)
                if component_file:
                    files.append(component_file)
        
        # Generate common utility components
        if len(features) > 0:
            # Generate a common Header component
            header_component = await self._generate_header_component(plan, coding_style)
            files.append(header_component)
            
            # Generate a common Footer component if appropriate
            if any(term in str(features).lower() for term in ["landing", "page", "website"]):
                footer_component = await self._generate_footer_component(plan, coding_style)
                files.append(footer_component)
        
        return files

    async def _generate_feature_component(self, feature: str, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a component for a specific feature."""
        
        # Map features to component names
        feature_components = {
            "dashboard": "Dashboard",
            "chat": "Chat",
            "blog": "Blog",
            "task": "TaskManager",
            "calendar": "Calendar",
            "analytics": "Analytics",
            "form": "ContactForm",
            "gallery": "Gallery",
            "profile": "UserProfile",
            "navigation": "Navigation"
        }
        
        component_name = None
        for key, comp_name in feature_components.items():
            if key in feature.lower():
                component_name = comp_name
                break
        
        if not component_name:
            # Generate a generic component name
            component_name = feature.title().replace(" ", "").replace("-", "")
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        component_developer = self.create_agent(
            role="React Component Specialist",
            goal=f"Create a specialized {component_name} component",
            backstory=f"""You are a React component specialist with expertise in creating 
            {feature} functionality. You build reusable, well-structured components 
            that are both functional and visually appealing.""",
            tools=tools
        )

        component_task = Task(
            description=f"""
            Create a React component for {feature} functionality:
            
            Component Name: {component_name}
            Feature: {feature}
            Style Theme: {coding_style["name"]}
            Style Config: {coding_style["config"]}
            
            Requirements:
            1. Create a functional React component
            2. Include relevant props and state management
            3. Apply consistent styling using the style theme
            4. Add proper JSX structure for the {feature} feature
            5. Include interactive elements where appropriate
            6. Add comments explaining the component's purpose
            7. Export the component properly
            8. Use modern React patterns and hooks
            
            Make the component production-ready and visually appealing.
            """,
            agent=component_developer,
            expected_output=f"Complete {component_name}.jsx component code"
        )

        crew = Crew(
            agents=[component_developer],
            tasks=[component_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        content = await self.execute_crew_with_retry(crew, {})
        
        return {
            "path": f"src/components/{component_name}.jsx",
            "filename": f"{component_name}.jsx",
            "content": str(content),
            "language": "javascript",
            "metadata": {
                "file_type": "component",
                "feature": feature,
                "component_name": component_name
            }
        }

    async def _generate_header_component(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a common Header component."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        project_name = self._generate_project_name(vibe_analysis)
        
        content = f'''import React from 'react';

const Header = () => {{
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">
              {project_name}
            </h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="#" className="text-gray-500 hover:text-gray-900">Home</a>
            <a href="#" className="text-gray-500 hover:text-gray-900">About</a>
            <a href="#" className="text-gray-500 hover:text-gray-900">Contact</a>
          </nav>
        </div>
      </div>
    </header>
  );
}};

export default Header;'''

        return {
            "path": "src/components/Header.jsx",
            "filename": "Header.jsx",
            "content": content,
            "language": "javascript",
            "metadata": {
                "file_type": "component",
                "component_type": "layout"
            }
        }

    async def _generate_footer_component(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a common Footer component."""
        
        content = '''import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-gray-500">
            © 2024 Built with Vibe Coding Platform. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;'''

        return {
            "path": "src/components/Footer.jsx",
            "filename": "Footer.jsx",
            "content": content,
            "language": "javascript",
            "metadata": {
                "file_type": "component",
                "component_type": "layout"
            }
        }

    async def _generate_style_files(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate styling files."""
        
        project_spec = plan.get("project_specification", {})
        tech_stack = project_spec.get("technology_stack", {})
        
        files = []
        
        if tech_stack.get("styling") == "tailwindcss":
            # Generate Tailwind CSS files
            index_css = await self._generate_tailwind_index_css(plan, coding_style)
            files.append(index_css)
            
            tailwind_config = await self._generate_tailwind_config(plan, coding_style)
            files.append(tailwind_config)
            
        else:
            # Generate regular CSS
            index_css = await self._generate_regular_css(plan, coding_style)
            files.append(index_css)
        
        return files

    async def _generate_tailwind_index_css(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Tailwind CSS index.css file."""
        
        style_config = coding_style.get("config", {})
        
        custom_styles = f'''
/* Custom styles for {coding_style["name"]} theme */
.app-container {{
  /* Add any custom styles here */
}}

/* Animation utilities */
.fade-in {{
  animation: fadeIn 0.5s ease-in-out;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Custom component styles */
.btn-primary {{
  @apply bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors;
}}

.card {{
  @apply bg-white rounded-lg shadow-md p-6 border border-gray-200;
}}'''
        
        content = self.code_templates["tailwind_css"].replace("{{custom_styles}}", custom_styles)
        
        return {
            "path": "src/index.css",
            "filename": "index.css",
            "content": content,
            "language": "css",
            "metadata": {
                "file_type": "styling",
                "framework": "tailwindcss",
                "theme": coding_style["name"]
            }
        }

    async def _generate_backend_files(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate backend API files if needed."""
        
        project_spec = plan.get("project_specification", {})
        if not project_spec.get("backend_needed", False):
            return []
        
        files = []
        
        # Generate main API file
        main_api = await self._generate_fastapi_main(plan, coding_style)
        files.append(main_api)
        
        # Generate models file
        models_file = await self._generate_api_models(plan, coding_style)
        files.append(models_file)
        
        return files

    async def _generate_fastapi_main(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FastAPI main.py file."""
        
        vibe_analysis = plan.get("vibe_analysis", {})
        features = vibe_analysis.get("core_features", [])
        
        # Generate basic API endpoints based on features
        endpoints = []
        
        if any("user" in str(f).lower() for f in features):
            endpoints.append('''
@app.get("/api/users")
async def get_users():
    return {"users": []}

@app.post("/api/users")
async def create_user(user_data: dict):
    return {"message": "User created", "user": user_data}''')
        
        if any("post" in str(f).lower() or "blog" in str(f).lower() for f in features):
            endpoints.append('''
@app.get("/api/posts")
async def get_posts():
    return {"posts": []}

@app.post("/api/posts")
async def create_post(post_data: dict):
    return {"message": "Post created", "post": post_data}''')
        
        # Default health check
        endpoints.append('''
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}''')
        
        project_name = self._generate_project_name(vibe_analysis)
        
        content = self.code_templates["fastapi_main"].replace(
            "{{project_name}}", project_name
        ).replace(
            "{{imports}}", ""
        ).replace(
            "{{models}}", "# Add your Pydantic models here"
        ).replace(
            "{{endpoints}}", "\n".join(endpoints)
        )
        
        return {
            "path": "api/main.py",
            "filename": "main.py",
            "content": content,
            "language": "python",
            "metadata": {
                "file_type": "api",
                "framework": "fastapi",
                "endpoints_count": len(endpoints)
            }
        }

    def _generate_project_name(self, vibe_analysis: Dict[str, Any]) -> str:
        """Generate a project name from vibe analysis."""
        
        project_type = vibe_analysis.get("project_type", "app")
        
        # Simple name generation
        if "blog" in project_type:
            return "My Blog"
        elif "dashboard" in project_type:
            return "Dashboard App"
        elif "task" in project_type:
            return "Task Manager"
        elif "chat" in project_type:
            return "Chat App"
        elif "landing" in project_type:
            return "Landing Page"
        else:
            return f"My {project_type.title()}"

    # Utility methods
    async def _generate_requirements_txt(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requirements.txt for Python backend."""
        
        content = '''fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0'''

        return {
            "path": "requirements.txt",
            "filename": "requirements.txt",
            "content": content,
            "language": "text",
            "metadata": {
                "file_type": "configuration",
                "purpose": "python_dependencies"
            }
        }

    async def _generate_gitignore(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate .gitignore file."""
        
        content = '''# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log

# Production
build/
dist/

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Directory for instrumented libs generated by jscoverage/JSCover
lib-cov

# Coverage directory used by tools like istanbul
coverage

# nyc test coverage
.nyc_output

# Grunt intermediate storage (http://gruntjs.com/creating-plugins#storing-task-files)
.grunt

# Bower dependency directory (https://bower.io/)
bower_components

# node-waf configuration
.lock-wscript

# Compiled binary addons (http://nodejs.org/api/addons.html)
build/Release

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db'''

        return {
            "path": ".gitignore",
            "filename": ".gitignore",
            "content": content,
            "language": "text",
            "metadata": {
                "file_type": "configuration",
                "purpose": "git_ignore"
            }
        }

    async def _generate_api_models(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API models file."""
        
        content = '''from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    created_at: Optional[datetime] = None

class Post(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    author_id: int
    created_at: Optional[datetime] = None

class Response(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None'''

        return {
            "path": "api/models.py",
            "filename": "models.py",
            "content": content,
            "language": "python",
            "metadata": {
                "file_type": "models",
                "framework": "pydantic"
            }
        }

    async def _generate_tailwind_config(self, plan: Dict[str, Any], coding_style: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tailwind.config.js file."""
        
        content = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
      }
    },
  },
  plugins: [],
}'''

        return {
            "path": "tailwind.config.js",
            "filename": "tailwind.config.js",
            "content": content,
            "language": "javascript",
            "metadata": {
                "file_type": "configuration",
                "framework": "tailwindcss"
            }
        }

    async def execute_crew_with_retry(self, crew, inputs):
        """Execute crew with retry logic."""
        try:
            result = await crew.kickoff_async(inputs)
            return result
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return f"// Error generating code: {str(e)}\n// Fallback code will be provided"