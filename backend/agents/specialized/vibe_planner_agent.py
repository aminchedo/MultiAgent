"""
Enhanced Planner Agent specialized for Vibe Coding - decomposing user vibes into actionable technical plans.
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from backend.agents.base.base_agent import BaseCrewAgent
from backend.agents.agents import AgentTools
from backend.models.models import ProjectType, ComplexityLevel
from config.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class VibePlannerAgent(BaseCrewAgent):
    """
    Specialized Planner Agent for decomposing user 'vibes' into structured technical plans.
    This agent understands natural language descriptions and converts them into executable tasks.
    """

    def __init__(self, job_id: str, websocket_callback: Optional[callable] = None):
        super().__init__(job_id, websocket_callback)
        self.vibe_patterns = self._load_vibe_patterns()
        self.project_templates = self._load_project_templates()

    def _load_vibe_patterns(self) -> Dict[str, Any]:
        """Load common vibe patterns for better understanding."""
        return {
            "ui_keywords": [
                "modern", "clean", "minimal", "dark mode", "responsive", "mobile-friendly",
                "beautiful", "elegant", "sleek", "professional", "colorful", "gradient"
            ],
            "functionality_keywords": [
                "dashboard", "chat", "blog", "e-commerce", "social", "portfolio", 
                "landing page", "admin panel", "task manager", "calendar", "analytics"
            ],
            "technology_keywords": [
                "react", "next.js", "vue", "angular", "node.js", "express", "fastapi",
                "tailwind", "bootstrap", "typescript", "javascript", "python"
            ],
            "features_keywords": [
                "authentication", "real-time", "database", "api", "search", "filtering",
                "notifications", "drag-and-drop", "charts", "forms", "validation"
            ]
        }

    def _load_project_templates(self) -> Dict[str, Any]:
        """Load project templates for common vibe types."""
        return {
            "landing_page": {
                "files": ["index.html", "styles.css", "script.js"],
                "sections": ["hero", "features", "testimonials", "pricing", "contact"],
                "complexity": "simple"
            },
            "dashboard": {
                "files": ["dashboard.jsx", "components/", "utils/", "styles/"],
                "features": ["charts", "tables", "filters", "sidebar", "header"],
                "complexity": "moderate"
            },
            "blog": {
                "files": ["pages/", "components/", "api/", "styles/"],
                "features": ["posts", "comments", "categories", "search", "pagination"],
                "complexity": "moderate"
            },
            "task_manager": {
                "files": ["components/", "hooks/", "api/", "utils/", "styles/"],
                "features": ["tasks", "projects", "users", "notifications", "drag-drop"],
                "complexity": "complex"
            },
            "e_commerce": {
                "files": ["products/", "cart/", "checkout/", "api/", "components/"],
                "features": ["catalog", "cart", "payment", "orders", "admin"],
                "complexity": "complex"
            }
        }

    async def decompose_vibe_prompt(self, user_prompt: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to decompose a user's vibe prompt into a structured technical plan.
        
        Args:
            user_prompt: The user's natural language description of what they want
            project_data: Additional project context and preferences
            
        Returns:
            Structured plan with tasks, file structure, and technical specifications
        """
        await self.log_message(f"Starting vibe decomposition for: '{user_prompt[:100]}...'")
        await self.update_progress(5, "Analyzing vibe prompt", 1)

        # Analyze the vibe prompt
        vibe_analysis = await self._analyze_vibe(user_prompt)
        
        # Determine project type and complexity
        project_spec = await self._determine_project_specifications(vibe_analysis, project_data)
        
        # Generate detailed technical plan
        technical_plan = await self._generate_technical_plan(vibe_analysis, project_spec)
        
        # Create file structure
        file_structure = await self._plan_file_structure(technical_plan, project_spec)
        
        # Generate task breakdown
        task_breakdown = await self._create_task_breakdown(technical_plan, file_structure)

        await self.update_progress(15, "Vibe decomposition completed", 1)
        
        complete_plan = {
            "original_vibe": user_prompt,
            "vibe_analysis": vibe_analysis,
            "project_specification": project_spec,
            "technical_plan": technical_plan,
            "file_structure": file_structure,
            "task_breakdown": task_breakdown,
            "estimated_complexity": project_spec.get("complexity", "moderate"),
            "estimated_files": len(file_structure.get("files", [])),
            "metadata": {
                "created_at": project_data.get("created_at"),
                "planner_version": "2.0-vibe-optimized"
            }
        }

        await self.log_message(
            f"Plan generated: {len(task_breakdown)} tasks, {len(file_structure.get('files', []))} files",
            metadata={
                "complexity": project_spec.get("complexity"),
                "project_type": project_spec.get("type"),
                "estimated_duration": project_spec.get("estimated_duration")
            }
        )

        return complete_plan

    async def _analyze_vibe(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze the user's vibe to extract key information."""
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        analyzer_agent = self.create_agent(
            role="Vibe Analysis Specialist",
            goal="Extract technical requirements from natural language descriptions",
            backstory="""You are an expert at understanding user intentions from casual, 
            creative descriptions. You can translate 'vibes' into concrete technical requirements. 
            You understand modern web development trends and can infer technical needs from 
            creative language.""",
            tools=tools
        )

        analysis_task = Task(
            description=f"""
            Analyze this user vibe prompt and extract structured information:
            
            User Vibe: "{user_prompt}"
            
            Extract and categorize:
            1. **Project Type**: What kind of application/website is this?
            2. **Core Features**: What functionality is needed?
            3. **UI/UX Requirements**: Visual style, design preferences
            4. **Technical Preferences**: Any mentioned technologies or frameworks
            5. **Target Audience**: Who will use this?
            6. **Complexity Indicators**: Simple, moderate, or complex project?
            7. **Key Emotions/Feelings**: What mood should the final product convey?
            
            Known patterns to look for:
            - UI Keywords: {', '.join(self.vibe_patterns['ui_keywords'][:10])}
            - Functionality: {', '.join(self.vibe_patterns['functionality_keywords'][:10])}
            - Technologies: {', '.join(self.vibe_patterns['technology_keywords'][:10])}
            
            Return analysis as a structured JSON object.
            """,
            agent=analyzer_agent,
            expected_output="JSON object with categorized vibe analysis"
        )

        crew = Crew(
            agents=[analyzer_agent],
            tasks=[analysis_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        result = await self.execute_crew_with_retry(crew, {})
        
        try:
            # Try to parse as JSON
            if isinstance(result, str):
                # Extract JSON from the result if it's wrapped in text
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback parsing
                    return self._parse_analysis_fallback(result, user_prompt)
            return result
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse vibe analysis as JSON: {e}")
            return self._parse_analysis_fallback(str(result), user_prompt)

    def _parse_analysis_fallback(self, analysis_text: str, user_prompt: str) -> Dict[str, Any]:
        """Fallback method to parse analysis when JSON parsing fails."""
        
        # Basic keyword detection
        prompt_lower = user_prompt.lower()
        
        # Detect project type
        project_type = "website"
        for keyword in self.vibe_patterns["functionality_keywords"]:
            if keyword in prompt_lower:
                project_type = keyword
                break
        
        # Detect UI preferences
        ui_preferences = []
        for keyword in self.vibe_patterns["ui_keywords"]:
            if keyword in prompt_lower:
                ui_preferences.append(keyword)
        
        # Detect technology preferences
        tech_preferences = []
        for keyword in self.vibe_patterns["technology_keywords"]:
            if keyword in prompt_lower:
                tech_preferences.append(keyword)
        
        # Estimate complexity
        complexity_indicators = ["admin", "dashboard", "real-time", "authentication", "database"]
        complexity = "simple"
        if any(indicator in prompt_lower for indicator in complexity_indicators):
            complexity = "moderate"
        if len([ind for ind in complexity_indicators if ind in prompt_lower]) > 2:
            complexity = "complex"

        return {
            "project_type": project_type,
            "core_features": [f for f in self.vibe_patterns["functionality_keywords"] if f in prompt_lower],
            "ui_requirements": ui_preferences,
            "technical_preferences": tech_preferences,
            "target_audience": "general users",
            "complexity_indicators": complexity,
            "key_emotions": ui_preferences,
            "extracted_from": "fallback_parsing"
        }

    async def _determine_project_specifications(self, vibe_analysis: Dict[str, Any], project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine detailed project specifications based on vibe analysis."""
        
        project_type = vibe_analysis.get("project_type", "website")
        complexity = vibe_analysis.get("complexity_indicators", "simple")
        
        # Map to template if available
        template = None
        for template_name, template_data in self.project_templates.items():
            if template_name in project_type or project_type in template_name:
                template = template_data
                break
        
        # Determine technology stack
        tech_stack = self._determine_tech_stack(vibe_analysis, project_data)
        
        return {
            "type": project_type,
            "complexity": complexity,
            "template": template,
            "technology_stack": tech_stack,
            "estimated_duration": self._estimate_duration(complexity),
            "target_framework": tech_stack.get("frontend", "react"),
            "styling_framework": tech_stack.get("styling", "tailwind"),
            "backend_needed": self._needs_backend(vibe_analysis),
            "database_needed": self._needs_database(vibe_analysis)
        }

    def _determine_tech_stack(self, vibe_analysis: Dict[str, Any], project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best technology stack based on requirements."""
        
        # Default modern stack
        stack = {
            "frontend": "react",
            "styling": "tailwindcss",
            "backend": "fastapi",
            "database": "sqlite",
            "deployment": "vercel"
        }
        
        # Override based on user preferences
        tech_prefs = vibe_analysis.get("technical_preferences", [])
        
        for pref in tech_prefs:
            if pref in ["react", "vue", "angular", "next.js"]:
                stack["frontend"] = pref
            elif pref in ["tailwind", "bootstrap", "css"]:
                stack["styling"] = pref
            elif pref in ["node.js", "express", "fastapi", "django"]:
                stack["backend"] = pref
            elif pref in ["mongodb", "postgresql", "mysql", "sqlite"]:
                stack["database"] = pref
        
        # Project type specific overrides
        project_type = project_data.get("project_type", ProjectType.WEB)
        if project_type == ProjectType.API:
            stack["frontend"] = "none"
            stack["focus"] = "api"
        elif project_type == ProjectType.MOBILE:
            stack["frontend"] = "react-native"
        
        return stack

    def _needs_backend(self, vibe_analysis: Dict[str, Any]) -> bool:
        """Determine if the project needs a backend."""
        backend_indicators = [
            "authentication", "login", "database", "api", "real-time", 
            "chat", "user", "admin", "dashboard", "dynamic"
        ]
        
        features = str(vibe_analysis.get("core_features", [])).lower()
        return any(indicator in features for indicator in backend_indicators)

    def _needs_database(self, vibe_analysis: Dict[str, Any]) -> bool:
        """Determine if the project needs a database."""
        db_indicators = [
            "user", "save", "store", "data", "profile", "post", "comment",
            "order", "product", "inventory", "history", "favorite"
        ]
        
        features = str(vibe_analysis.get("core_features", [])).lower()
        return any(indicator in features for indicator in db_indicators)

    def _estimate_duration(self, complexity: str) -> str:
        """Estimate project duration based on complexity."""
        duration_map = {
            "simple": "1-2 hours",
            "moderate": "3-6 hours", 
            "complex": "1-2 days"
        }
        return duration_map.get(complexity, "2-4 hours")

    async def _generate_technical_plan(self, vibe_analysis: Dict[str, Any], project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed technical implementation plan."""
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        technical_planner = self.create_agent(
            role="Senior Technical Architect",
            goal="Create detailed technical implementation plans from requirements",
            backstory="""You are a senior technical architect with expertise in modern 
            web development. You excel at creating comprehensive technical plans that 
            consider scalability, maintainability, and best practices.""",
            tools=tools
        )

        planning_task = Task(
            description=f"""
            Create a detailed technical implementation plan:
            
            Vibe Analysis: {json.dumps(vibe_analysis, indent=2)}
            Project Specifications: {json.dumps(project_spec, indent=2)}
            
            Generate a comprehensive plan including:
            1. **Architecture Overview**: High-level system design
            2. **Component Breakdown**: Main components and their responsibilities
            3. **Data Models**: Required data structures and relationships
            4. **API Endpoints**: If backend is needed
            5. **UI Components**: Main interface components
            6. **Styling Strategy**: CSS/styling approach
            7. **State Management**: How application state will be handled
            8. **Integration Points**: How components will work together
            9. **Performance Considerations**: Optimization strategies
            10. **Security Measures**: Security best practices to implement
            
            Focus on modern, production-ready practices and maintainable code structure.
            """,
            agent=technical_planner,
            expected_output="Comprehensive technical implementation plan"
        )

        crew = Crew(
            agents=[technical_planner],
            tasks=[planning_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        return await self.execute_crew_with_retry(crew, {})

    async def _plan_file_structure(self, technical_plan: Any, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Plan the complete file structure for the project."""
        
        tech_stack = project_spec.get("technology_stack", {})
        frontend = tech_stack.get("frontend", "react")
        needs_backend = project_spec.get("backend_needed", False)
        
        # Base structure based on frontend framework
        if frontend == "react" or frontend == "next.js":
            structure = {
                "files": [
                    "package.json",
                    "README.md",
                    "src/App.jsx",
                    "src/index.js",
                    "src/components/",
                    "src/hooks/",
                    "src/utils/",
                    "src/styles/",
                    "public/index.html"
                ],
                "directories": [
                    "src/components",
                    "src/hooks", 
                    "src/utils",
                    "src/styles",
                    "public"
                ]
            }
        else:
            # Default HTML/CSS/JS structure
            structure = {
                "files": [
                    "index.html",
                    "styles.css", 
                    "script.js",
                    "README.md"
                ],
                "directories": []
            }
        
        # Add backend structure if needed
        if needs_backend:
            structure["files"].extend([
                "api/main.py",
                "api/models.py",
                "api/routes.py",
                "requirements.txt"
            ])
            structure["directories"].extend([
                "api"
            ])
        
        # Add specific files based on project features
        features = str(technical_plan).lower()
        
        if "authentication" in features:
            structure["files"].append("src/components/Auth.jsx")
        if "dashboard" in features:
            structure["files"].append("src/components/Dashboard.jsx")
        if "chart" in features:
            structure["files"].append("src/components/Charts.jsx")
        
        return structure

    async def _create_task_breakdown(self, technical_plan: Any, file_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a breakdown of tasks for the Coder Agent."""
        
        tasks = []
        files = file_structure.get("files", [])
        
        # Group files by type/category
        file_groups = {
            "configuration": [f for f in files if f.endswith(('.json', '.txt', '.md'))],
            "frontend_core": [f for f in files if 'App.' in f or 'index.' in f],
            "components": [f for f in files if '/components/' in f],
            "styles": [f for f in files if f.endswith('.css') or '/styles/' in f],
            "backend": [f for f in files if f.startswith('api/')],
            "utilities": [f for f in files if '/utils/' in f or '/hooks/' in f]
        }
        
        # Create tasks for each group
        priority = 1
        for group_name, group_files in file_groups.items():
            if group_files:
                tasks.append({
                    "id": f"task_{priority}",
                    "name": f"Create {group_name.replace('_', ' ').title()}",
                    "description": f"Implement {group_name} files: {', '.join(group_files)}",
                    "files": group_files,
                    "priority": priority,
                    "estimated_time": self._estimate_task_time(group_name, len(group_files)),
                    "dependencies": self._get_task_dependencies(group_name),
                    "complexity": self._assess_task_complexity(group_name, group_files)
                })
                priority += 1
        
        return tasks

    def _estimate_task_time(self, group_name: str, file_count: int) -> str:
        """Estimate time for a task group."""
        base_times = {
            "configuration": "5 minutes",
            "frontend_core": "15 minutes",
            "components": "10 minutes per component",
            "styles": "8 minutes",
            "backend": "20 minutes",
            "utilities": "5 minutes per utility"
        }
        
        base_time = base_times.get(group_name, "10 minutes")
        if "per" in base_time and file_count > 1:
            return f"{base_time} (total: ~{file_count * 10} minutes)"
        return base_time

    def _get_task_dependencies(self, group_name: str) -> List[str]:
        """Get dependencies for a task group."""
        dependencies = {
            "configuration": [],
            "frontend_core": ["configuration"],
            "components": ["frontend_core"],
            "styles": ["frontend_core"],
            "backend": ["configuration"],
            "utilities": ["frontend_core"]
        }
        return dependencies.get(group_name, [])

    def _assess_task_complexity(self, group_name: str, files: List[str]) -> str:
        """Assess complexity of a task group."""
        complexity_map = {
            "configuration": "low",
            "frontend_core": "medium",
            "components": "medium" if len(files) <= 3 else "high",
            "styles": "low",
            "backend": "high",
            "utilities": "medium"
        }
        return complexity_map.get(group_name, "medium")

    async def execute_crew_with_retry(self, crew, inputs):
        """Execute crew with retry logic."""
        try:
            result = await crew.kickoff_async(inputs)
            return result
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            # Return a structured fallback
            return {
                "status": "error",
                "message": str(e),
                "fallback": True
            }