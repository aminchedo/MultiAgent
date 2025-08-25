"""
VibePlannerAgent - Decomposes vibe prompts into detailed technical plans.

This agent takes natural language "vibe" descriptions and transforms them into
structured development plans with clear tasks, technologies, and specifications.
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging

from agents.base_agent import BaseAgent


class VibePlannerAgent(BaseAgent):
    """
    Agent responsible for decomposing vibe prompts into actionable development plans.
    
    This agent:
    1. Analyzes natural language vibe descriptions
    2. Determines appropriate technologies and frameworks
    3. Breaks down the project into structured tasks
    4. Estimates complexity and timelines
    5. Creates detailed specifications for implementation
    """
    
    def __init__(self, agent_id: str = None, name: str = "VibePlannerAgent"):
        # Initialize capabilities as empty list for BaseAgent
        capabilities = []
        super().__init__("vibe_planner", capabilities)
        self.logger = logging.getLogger(__name__)
        
        # Agent capabilities (stored as simple list for this implementation)
        self.vibe_capabilities = [
            "vibe_decomposition",
            "technology_selection", 
            "task_planning",
            "complexity_analysis",
            "specification_generation"
        ]
        
        # Planning templates for different project types
        self.project_templates = {
            "web_app": {
                "frontend": ["HTML", "CSS", "JavaScript", "React/Vue/Angular"],
                "backend": ["Node.js", "Python", "APIs", "Database"],
                "common_features": ["responsive design", "user authentication", "data management"]
            },
            "mobile_app": {
                "platforms": ["iOS", "Android", "React Native", "Flutter"],
                "features": ["navigation", "local storage", "push notifications"],
                "apis": ["RESTful services", "GraphQL"]
            },
            "api": {
                "frameworks": ["Express.js", "FastAPI", "Django", "Flask"],
                "features": ["endpoints", "authentication", "validation", "documentation"],
                "database": ["PostgreSQL", "MongoDB", "Redis"]
            },
            "dashboard": {
                "components": ["charts", "tables", "filters", "real-time updates"],
                "technologies": ["React", "Vue", "D3.js", "Chart.js"],
                "data": ["APIs", "WebSockets", "caching"]
            },
            "game": {
                "engines": ["Unity", "Unreal", "JavaScript Canvas", "Phaser"],
                "features": ["game loop", "physics", "graphics", "sound"],
                "platforms": ["web", "mobile", "desktop"]
            }
        }
        
        # Complexity indicators
        self.complexity_factors = {
            "simple": {
                "features": 1-3,
                "integrations": 0-1,
                "users": "single",
                "data": "basic"
            },
            "moderate": {
                "features": 4-8,
                "integrations": 2-4,
                "users": "multiple",
                "data": "structured"
            },
            "complex": {
                "features": 9-15,
                "integrations": 5-10,
                "users": "many",
                "data": "complex relationships"
            },
            "enterprise": {
                "features": "15+",
                "integrations": "10+",
                "users": "enterprise scale",
                "data": "big data/analytics"
            }
        }

    async def decompose_vibe_prompt(self, vibe_prompt: str, project_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method to decompose a vibe prompt into a detailed development plan.
        
        Args:
            vibe_prompt: Natural language description of desired project
            project_data: Additional context about the project
            
        Returns:
            Structured plan with tasks, technologies, and specifications
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting vibe decomposition for: {vibe_prompt[:100]}...")
            
            # Initialize project data if not provided
            if project_data is None:
                project_data = {}
            
            # Step 1: Analyze the vibe prompt
            analysis = await self._analyze_vibe_prompt(vibe_prompt)
            
            # Step 2: Determine project type and complexity
            project_type = self._determine_project_type(vibe_prompt, analysis)
            complexity = self._assess_complexity(vibe_prompt, analysis)
            
            # Step 3: Select appropriate technologies
            tech_stack = self._select_technology_stack(project_type, complexity, analysis)
            
            # Step 4: Generate task breakdown
            tasks = self._generate_task_breakdown(analysis, project_type, complexity)
            
            # Step 5: Create detailed specifications
            specifications = self._create_specifications(analysis, project_type, tech_stack, tasks)
            
            # Step 6: Estimate timeline and resources
            estimates = self._estimate_timeline_and_resources(tasks, complexity)
            
            # Compile final plan
            plan = {
                "vibe_prompt": vibe_prompt,
                "analysis": analysis,
                "project_type": project_type,
                "complexity": complexity,
                "technology_stack": tech_stack,
                "task_breakdown": tasks,
                "specifications": specifications,
                "estimates": estimates,
                "metadata": {
                    "planner_agent_id": self.agent_id,
                    "planning_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time,
                    "version": "1.0"
                }
            }
            
            self.logger.info(f"Vibe decomposition completed in {time.time() - start_time:.2f}s")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error in vibe decomposition: {str(e)}")
            return {
                "error": str(e),
                "vibe_prompt": vibe_prompt,
                "status": "failed",
                "metadata": {
                    "planner_agent_id": self.agent_id,
                    "error_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time
                }
            }

    async def _analyze_vibe_prompt(self, vibe_prompt: str) -> Dict[str, Any]:
        """Analyze the vibe prompt to extract key information."""
        
        # Extract key entities and concepts
        entities = self._extract_entities(vibe_prompt)
        
        # Identify features and requirements
        features = self._identify_features(vibe_prompt)
        
        # Detect user personas and use cases
        users = self._identify_user_personas(vibe_prompt)
        
        # Extract functional requirements
        requirements = self._extract_requirements(vibe_prompt)
        
        return {
            "entities": entities,
            "features": features,
            "user_personas": users,
            "requirements": requirements,
            "keywords": self._extract_keywords(vibe_prompt),
            "tone_indicators": self._analyze_tone(vibe_prompt)
        }

    def _extract_entities(self, prompt: str) -> List[str]:
        """Extract key entities from the prompt."""
        entities = []
        
        # Common tech entities
        tech_terms = [
            "dashboard", "app", "website", "api", "mobile", "web", "game", "tool",
            "platform", "system", "interface", "database", "analytics", "chat",
            "social", "ecommerce", "blog", "portfolio", "landing page"
        ]
        
        prompt_lower = prompt.lower()
        for term in tech_terms:
            if term in prompt_lower:
                entities.append(term)
                
        return entities

    def _identify_features(self, prompt: str) -> List[str]:
        """Identify requested features from the prompt."""
        features = []
        
        feature_keywords = {
            "authentication": ["login", "signup", "auth", "user account", "register"],
            "real_time": ["real-time", "live", "instant", "streaming"],
            "data_visualization": ["chart", "graph", "analytics", "dashboard", "visualization"],
            "file_upload": ["upload", "file", "image", "document"],
            "search": ["search", "filter", "find"],
            "notifications": ["notification", "alert", "email", "push"],
            "payment": ["payment", "checkout", "billing", "subscription"],
            "social": ["share", "comment", "like", "follow", "social"],
            "responsive": ["mobile", "responsive", "device"],
            "admin": ["admin", "management", "control panel"]
        }
        
        prompt_lower = prompt.lower()
        for feature, keywords in feature_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                features.append(feature)
                
        return features

    def _identify_user_personas(self, prompt: str) -> List[str]:
        """Identify user personas from the prompt."""
        personas = []
        
        persona_keywords = {
            "admin": ["admin", "administrator", "manager"],
            "customer": ["customer", "client", "buyer", "user"],
            "employee": ["employee", "staff", "worker", "team"],
            "student": ["student", "learner"],
            "teacher": ["teacher", "instructor", "educator"],
            "developer": ["developer", "programmer", "coder"],
            "analyst": ["analyst", "data scientist"]
        }
        
        prompt_lower = prompt.lower()
        for persona, keywords in persona_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                personas.append(persona)
                
        return personas if personas else ["general_user"]

    def _extract_requirements(self, prompt: str) -> Dict[str, List[str]]:
        """Extract functional and non-functional requirements."""
        requirements = {
            "functional": [],
            "non_functional": []
        }
        
        # Functional requirement patterns
        functional_patterns = [
            "need to", "should be able to", "must have", "requires", "allows",
            "enables", "provides", "supports", "includes", "features"
        ]
        
        # Non-functional requirement indicators
        non_functional_keywords = {
            "performance": ["fast", "quick", "responsive", "speed"],
            "security": ["secure", "safe", "protected", "encrypted"],
            "usability": ["easy", "simple", "intuitive", "user-friendly"],
            "scalability": ["scale", "grow", "expand", "many users"],
            "reliability": ["reliable", "stable", "available", "uptime"]
        }
        
        prompt_lower = prompt.lower()
        
        # Extract functional requirements (simplified)
        if "create" in prompt_lower or "build" in prompt_lower:
            requirements["functional"].append("create_application")
        if "manage" in prompt_lower or "crud" in prompt_lower:
            requirements["functional"].append("data_management")
            
        # Extract non-functional requirements
        for category, keywords in non_functional_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                requirements["non_functional"].append(category)
                
        return requirements

    def _extract_keywords(self, prompt: str) -> List[str]:
        """Extract important keywords from the prompt."""
        # Simple keyword extraction - in production, use NLP libraries
        words = prompt.lower().split()
        
        # Filter out common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should"
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:20]  # Return top 20 keywords

    def _analyze_tone(self, prompt: str) -> Dict[str, str]:
        """Analyze the tone and style indicators in the prompt."""
        tone_indicators = {
            "formality": "neutral",
            "urgency": "normal",
            "complexity_preference": "moderate"
        }
        
        prompt_lower = prompt.lower()
        
        # Formality indicators
        if any(word in prompt_lower for word in ["professional", "corporate", "business"]):
            tone_indicators["formality"] = "formal"
        elif any(word in prompt_lower for word in ["fun", "casual", "friendly"]):
            tone_indicators["formality"] = "casual"
            
        # Urgency indicators
        if any(word in prompt_lower for word in ["urgent", "quickly", "asap", "immediately"]):
            tone_indicators["urgency"] = "high"
        elif any(word in prompt_lower for word in ["eventually", "when possible"]):
            tone_indicators["urgency"] = "low"
            
        # Complexity preference
        if any(word in prompt_lower for word in ["simple", "basic", "minimal"]):
            tone_indicators["complexity_preference"] = "simple"
        elif any(word in prompt_lower for word in ["advanced", "sophisticated", "enterprise"]):
            tone_indicators["complexity_preference"] = "complex"
            
        return tone_indicators

    def _determine_project_type(self, vibe_prompt: str, analysis: Dict[str, Any]) -> str:
        """Determine the project type based on analysis."""
        entities = analysis.get("entities", [])
        
        # Project type mapping
        type_indicators = {
            "web_app": ["website", "web app", "web application"],
            "mobile_app": ["mobile app", "mobile", "ios", "android"],
            "api": ["api", "backend", "service", "microservice"],
            "dashboard": ["dashboard", "analytics", "reporting"],
            "game": ["game", "gaming"],
            "ecommerce": ["ecommerce", "shop", "store", "marketplace"],
            "blog": ["blog", "content", "cms"],
            "portfolio": ["portfolio", "showcase"],
            "landing_page": ["landing page", "landing", "marketing"]
        }
        
        prompt_lower = vibe_prompt.lower()
        
        for project_type, indicators in type_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return project_type
                
        # Default based on entities
        if "dashboard" in entities:
            return "dashboard"
        elif "app" in entities and "mobile" in entities:
            return "mobile_app"
        elif "api" in entities:
            return "api"
        else:
            return "web_app"  # Default

    def _assess_complexity(self, vibe_prompt: str, analysis: Dict[str, Any]) -> str:
        """Assess project complexity based on features and requirements."""
        features = analysis.get("features", [])
        requirements = analysis.get("requirements", {})
        
        complexity_score = 0
        
        # Feature-based scoring
        complexity_score += len(features)
        
        # Integration complexity
        integrations = ["payment", "social", "real_time", "notifications"]
        complexity_score += len([f for f in features if f in integrations]) * 2
        
        # User persona complexity
        personas = analysis.get("user_personas", [])
        if len(personas) > 1:
            complexity_score += len(personas)
            
        # Keyword-based indicators
        prompt_lower = vibe_prompt.lower()
        if any(word in prompt_lower for word in ["enterprise", "scalable", "advanced"]):
            complexity_score += 5
        elif any(word in prompt_lower for word in ["simple", "basic", "minimal"]):
            complexity_score -= 2
            
        # Determine complexity level
        if complexity_score <= 3:
            return "simple"
        elif complexity_score <= 8:
            return "moderate"
        elif complexity_score <= 15:
            return "complex"
        else:
            return "enterprise"

    def _select_technology_stack(self, project_type: str, complexity: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate technology stack based on project requirements."""
        
        base_stack = self.project_templates.get(project_type, self.project_templates["web_app"])
        features = analysis.get("features", [])
        
        tech_stack = {
            "frontend": [],
            "backend": [],
            "database": [],
            "additional_tools": [],
            "deployment": []
        }
        
        # Frontend technologies
        if project_type in ["web_app", "dashboard"]:
            if complexity in ["simple", "moderate"]:
                tech_stack["frontend"] = ["HTML", "CSS", "JavaScript", "React"]
            else:
                tech_stack["frontend"] = ["TypeScript", "React", "Tailwind CSS", "Redux"]
                
        elif project_type == "mobile_app":
            tech_stack["frontend"] = ["React Native"]
            
        # Backend technologies
        if project_type != "landing_page":
            if complexity == "simple":
                tech_stack["backend"] = ["Node.js", "Express"]
            else:
                tech_stack["backend"] = ["Python", "FastAPI", "SQLAlchemy"]
                
        # Database selection
        if "data_management" in analysis.get("requirements", {}).get("functional", []):
            if complexity in ["simple", "moderate"]:
                tech_stack["database"] = ["SQLite"]
            else:
                tech_stack["database"] = ["PostgreSQL", "Redis"]
                
        # Feature-specific additions
        if "real_time" in features:
            tech_stack["additional_tools"].append("WebSockets")
        if "payment" in features:
            tech_stack["additional_tools"].append("Stripe API")
        if "authentication" in features:
            tech_stack["additional_tools"].append("JWT")
        if "data_visualization" in features:
            tech_stack["additional_tools"].append("Chart.js")
            
        # Deployment options
        if complexity == "simple":
            tech_stack["deployment"] = ["Vercel", "Netlify"]
        else:
            tech_stack["deployment"] = ["Docker", "AWS/GCP"]
            
        return tech_stack

    def _generate_task_breakdown(self, analysis: Dict[str, Any], project_type: str, complexity: str) -> List[Dict[str, Any]]:
        """Generate detailed task breakdown for the project."""
        
        tasks = []
        task_id = 1
        
        # Phase 1: Setup and Planning
        tasks.append({
            "id": task_id,
            "phase": "setup",
            "title": "Project Setup and Environment Configuration",
            "description": "Initialize project structure, set up development environment, and configure tools",
            "estimated_hours": 2,
            "priority": "high",
            "dependencies": []
        })
        task_id += 1
        
        # Phase 2: Core Development
        if project_type in ["web_app", "dashboard"]:
            # Frontend tasks
            tasks.append({
                "id": task_id,
                "phase": "frontend",
                "title": "Create UI Components and Layout",
                "description": "Develop main UI components, layout structure, and responsive design",
                "estimated_hours": 8 if complexity == "simple" else 16,
                "priority": "high",
                "dependencies": [1]
            })
            task_id += 1
            
            # Backend tasks if needed
            if "data_management" in analysis.get("requirements", {}).get("functional", []):
                tasks.append({
                    "id": task_id,
                    "phase": "backend",
                    "title": "Implement Backend API and Database",
                    "description": "Create API endpoints, database models, and data management logic",
                    "estimated_hours": 12 if complexity == "simple" else 24,
                    "priority": "high",
                    "dependencies": [1]
                })
                task_id += 1
                
        # Feature-specific tasks
        for feature in analysis.get("features", []):
            if feature == "authentication":
                tasks.append({
                    "id": task_id,
                    "phase": "features",
                    "title": "Implement User Authentication",
                    "description": "Set up user registration, login, and session management",
                    "estimated_hours": 6,
                    "priority": "medium",
                    "dependencies": [task_id - 1] if tasks else []
                })
                task_id += 1
                
            elif feature == "data_visualization":
                tasks.append({
                    "id": task_id,
                    "phase": "features",
                    "title": "Create Data Visualization Components",
                    "description": "Implement charts, graphs, and analytics displays",
                    "estimated_hours": 8,
                    "priority": "medium",
                    "dependencies": [2] if len(tasks) >= 2 else []
                })
                task_id += 1
                
        # Phase 3: Testing and Deployment
        tasks.append({
            "id": task_id,
            "phase": "testing",
            "title": "Testing and Quality Assurance",
            "description": "Write tests, perform quality checks, and bug fixes",
            "estimated_hours": 4 if complexity == "simple" else 8,
            "priority": "medium",
            "dependencies": list(range(1, task_id))
        })
        task_id += 1
        
        tasks.append({
            "id": task_id,
            "phase": "deployment",
            "title": "Deployment and Documentation",
            "description": "Deploy application and create user documentation",
            "estimated_hours": 3,
            "priority": "medium",
            "dependencies": [task_id - 1]
        })
        
        return tasks

    def _create_specifications(self, analysis: Dict[str, Any], project_type: str, tech_stack: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create detailed technical specifications."""
        
        return {
            "architecture": {
                "pattern": "MVC" if project_type in ["web_app", "api"] else "Component-based",
                "frontend_framework": tech_stack.get("frontend", ["React"])[0] if tech_stack.get("frontend") else None,
                "backend_framework": tech_stack.get("backend", ["FastAPI"])[0] if tech_stack.get("backend") else None,
                "database": tech_stack.get("database", ["SQLite"])[0] if tech_stack.get("database") else None
            },
            "file_structure": self._generate_file_structure(project_type, tech_stack),
            "api_endpoints": self._generate_api_endpoints(analysis, project_type),
            "database_schema": self._generate_database_schema(analysis, project_type),
            "ui_components": self._generate_ui_components(analysis, project_type),
            "deployment_config": {
                "platform": tech_stack.get("deployment", ["Vercel"])[0] if tech_stack.get("deployment") else "Vercel",
                "environment_variables": self._generate_env_variables(analysis, tech_stack),
                "build_commands": self._generate_build_commands(tech_stack)
            }
        }

    def _generate_file_structure(self, project_type: str, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project file structure."""
        
        if project_type in ["web_app", "dashboard"]:
            return {
                "src/": {
                    "components/": ["Header.jsx", "Footer.jsx", "Layout.jsx"],
                    "pages/": ["Home.jsx", "About.jsx"],
                    "hooks/": ["useAuth.js", "useApi.js"],
                    "utils/": ["api.js", "helpers.js"],
                    "styles/": ["globals.css", "components.css"]
                },
                "public/": ["index.html", "favicon.ico"],
                "package.json": "dependencies and scripts",
                ".env": "environment variables"
            }
        else:
            return {
                "src/": "source code directory",
                "tests/": "test files",
                "docs/": "documentation",
                "config/": "configuration files"
            }

    def _generate_api_endpoints(self, analysis: Dict[str, Any], project_type: str) -> List[Dict[str, str]]:
        """Generate API endpoint specifications."""
        
        endpoints = []
        
        if "data_management" in analysis.get("requirements", {}).get("functional", []):
            endpoints.extend([
                {"method": "GET", "path": "/api/items", "description": "Get all items"},
                {"method": "POST", "path": "/api/items", "description": "Create new item"},
                {"method": "GET", "path": "/api/items/:id", "description": "Get item by ID"},
                {"method": "PUT", "path": "/api/items/:id", "description": "Update item"},
                {"method": "DELETE", "path": "/api/items/:id", "description": "Delete item"}
            ])
            
        if "authentication" in analysis.get("features", []):
            endpoints.extend([
                {"method": "POST", "path": "/api/auth/login", "description": "User login"},
                {"method": "POST", "path": "/api/auth/register", "description": "User registration"},
                {"method": "POST", "path": "/api/auth/logout", "description": "User logout"}
            ])
            
        return endpoints

    def _generate_database_schema(self, analysis: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """Generate database schema."""
        
        schema = {}
        
        if "data_management" in analysis.get("requirements", {}).get("functional", []):
            schema["items"] = {
                "id": "INTEGER PRIMARY KEY",
                "name": "VARCHAR(255) NOT NULL", 
                "description": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
        if "authentication" in analysis.get("features", []):
            schema["users"] = {
                "id": "INTEGER PRIMARY KEY",
                "username": "VARCHAR(255) UNIQUE NOT NULL",
                "email": "VARCHAR(255) UNIQUE NOT NULL",
                "password_hash": "VARCHAR(255) NOT NULL",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            
        return schema

    def _generate_ui_components(self, analysis: Dict[str, Any], project_type: str) -> List[str]:
        """Generate list of UI components needed."""
        
        components = ["Header", "Footer", "Layout", "Button", "Input"]
        
        if project_type == "dashboard":
            components.extend(["Chart", "Table", "Filter", "Sidebar"])
            
        if "authentication" in analysis.get("features", []):
            components.extend(["LoginForm", "RegisterForm"])
            
        if "data_visualization" in analysis.get("features", []):
            components.extend(["BarChart", "LineChart", "PieChart"])
            
        return components

    def _generate_env_variables(self, analysis: Dict[str, Any], tech_stack: Dict[str, Any]) -> List[str]:
        """Generate list of environment variables needed."""
        
        env_vars = ["NODE_ENV", "PORT"]
        
        if tech_stack.get("database"):
            env_vars.extend(["DATABASE_URL", "DB_HOST", "DB_PASSWORD"])
            
        if "authentication" in analysis.get("features", []):
            env_vars.extend(["JWT_SECRET", "SESSION_SECRET"])
            
        if "payment" in analysis.get("features", []):
            env_vars.extend(["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"])
            
        return env_vars

    def _generate_build_commands(self, tech_stack: Dict[str, Any]) -> Dict[str, str]:
        """Generate build commands for the project."""
        
        commands = {}
        
        if "React" in tech_stack.get("frontend", []):
            commands.update({
                "install": "npm install",
                "dev": "npm run dev",
                "build": "npm run build",
                "start": "npm start"
            })
            
        if "Python" in tech_stack.get("backend", []):
            commands.update({
                "install_backend": "pip install -r requirements.txt",
                "start_backend": "python main.py",
                "test": "pytest"
            })
            
        return commands

    def _estimate_timeline_and_resources(self, tasks: List[Dict[str, Any]], complexity: str) -> Dict[str, Any]:
        """Estimate timeline and resource requirements."""
        
        total_hours = sum(task.get("estimated_hours", 0) for task in tasks)
        
        # Adjust for complexity
        complexity_multiplier = {
            "simple": 1.0,
            "moderate": 1.2,
            "complex": 1.5,
            "enterprise": 2.0
        }
        
        adjusted_hours = total_hours * complexity_multiplier.get(complexity, 1.0)
        
        return {
            "total_estimated_hours": adjusted_hours,
            "estimated_days": max(1, int(adjusted_hours / 8)),
            "recommended_team_size": 1 if complexity == "simple" else 2 if complexity == "moderate" else 3,
            "critical_path": [task["id"] for task in tasks if task.get("priority") == "high"],
            "risk_factors": self._identify_risk_factors(complexity, tasks),
            "buffer_percentage": 20 if complexity == "simple" else 30 if complexity == "moderate" else 50
        }

    def _identify_risk_factors(self, complexity: str, tasks: List[Dict[str, Any]]) -> List[str]:
        """Identify potential risk factors for the project."""
        
        risks = []
        
        if complexity in ["complex", "enterprise"]:
            risks.append("High complexity may lead to scope creep")
            
        if len(tasks) > 10:
            risks.append("Large number of tasks increases coordination overhead")
            
        # Check for integration tasks
        integration_tasks = [task for task in tasks if "integration" in task.get("description", "").lower()]
        if integration_tasks:
            risks.append("Third-party integrations may cause delays")
            
        return risks

    async def process_task(self, task) -> Any:
        """Process a task (required by BaseAgent)."""
        # For vibe agents, we don't use the generic task processing
        # This is just a placeholder implementation
        return {"status": "task_not_supported", "message": "Use decompose_vibe_prompt instead"}

    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get custom metrics for the planner agent."""
        return {
            "plans_generated": 0.0,
            "average_planning_time": 0.0,
            "complexity_distribution": 0.0
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_planner():
        planner = VibePlannerAgent()
        
        # Test with a simple vibe prompt
        vibe_prompt = "Create a modern dashboard for tracking sales analytics with real-time charts and user authentication"
        
        plan = await planner.decompose_vibe_prompt(vibe_prompt)
        
        print("=== VIBE PLANNER RESULT ===")
        print(json.dumps(plan, indent=2))
        
    # Run the test
    asyncio.run(test_planner())