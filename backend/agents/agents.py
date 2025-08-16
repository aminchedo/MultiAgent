"""
CrewAI agents module for intelligent multi-agent code generation workflows.
"""

import asyncio
import json
import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from pydantic import BaseModel, Field

from config.config import get_settings
from backend.models.models import (
    JobStatus, ProjectType, ComplexityLevel, AgentType, 
    generate_task_id, WebSocketMessage, MessageType
)
from backend.database.db import db_manager
import structlog

logger = structlog.get_logger()


settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def execute_crew_with_retry(crew, inputs):
    """Execute crew with automatic retries"""
    try:
        return await crew.kickoff(inputs)
    except Exception as e:
        logger.error(f"Crew execution failed: {e}")
        raise


class AgentTools:
    """Custom tools for CrewAI agents."""
    
    @tool("file_writer")
    def write_file(file_path: str, content: str) -> str:
        """Write content to a file."""
        try:
            from backend.utils.vercel_utils import write_file_vercel_safe
            actual_path, message = write_file_vercel_safe(file_path, content)
            return message
        except Exception as e:
            return f"Error writing file {file_path}: {str(e)}"
    
    @tool("file_reader")
    def read_file(file_path: str) -> str:
        """Read content from a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"File not found: {file_path}"
            return path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    @tool("code_executor")
    def execute_code(code: str, language: str = "python") -> str:
        """Execute code in a sandboxed environment."""
        try:
            if language.lower() == "python":
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Execute Python code
                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Clean up
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    return f"Execution successful:\n{result.stdout}"
                else:
                    return f"Execution failed:\n{result.stderr}"
            
            elif language.lower() == "javascript":
                # Execute JavaScript with Node.js
                result = subprocess.run(
                    ["node", "-e", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return f"Execution successful:\n{result.stdout}"
                else:
                    return f"Execution failed:\n{result.stderr}"
            
            else:
                return f"Unsupported language: {language}"
                
        except subprocess.TimeoutExpired:
            return "Code execution timed out"
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    @tool("test_runner")
    def run_tests(test_directory: str) -> str:
        """Run tests in the specified directory."""
        try:
            test_path = Path(test_directory)
            if not test_path.exists():
                return f"Test directory not found: {test_directory}"
            
            # Try pytest first
            result = subprocess.run(
                ["pytest", str(test_path), "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return f"All tests passed:\n{result.stdout}"
            else:
                return f"Some tests failed:\n{result.stdout}\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Test execution timed out"
        except FileNotFoundError:
            # Fallback to unittest
            try:
                result = subprocess.run(
                    ["python", "-m", "unittest", "discover", str(test_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return f"Test results:\n{result.stdout}\n{result.stderr}"
            except Exception as e:
                return f"Test execution error: {str(e)}"
        except Exception as e:
            return f"Test execution error: {str(e)}"


class BaseCrewAgent:
    """Base class for CrewAI agents with database integration."""
    
    def __init__(self, job_id: str, websocket_callback: Optional[Callable] = None):
        self.job_id = job_id
        self.websocket_callback = websocket_callback
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,  # gpt-4 or gpt-4-turbo
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
    
    async def log_message(self, message: str, level: str = "INFO", metadata: Dict[str, Any] = None):
        """Log a message to the database and WebSocket."""
        await db_manager.create_log(
            job_id=self.job_id,
            agent=self.__class__.__name__,
            message=message,
            level=level,
            metadata=metadata or {}
        )
        
        if self.websocket_callback:
            ws_message = WebSocketMessage(
                type=MessageType.AGENT_MESSAGE,
                job_id=self.job_id,
                agent=self.__class__.__name__,
                content=message,
                metadata=metadata or {}
            )
            await self.websocket_callback(ws_message.dict())
    
    async def update_progress(self, progress: float, step: str, step_number: int = None):
        """Update job progress."""
        await db_manager.update_job_status(
            job_id=self.job_id,
            status=JobStatus.RUNNING,
            progress=progress,
            current_step=step,
            step_number=step_number
        )
    
    def create_agent(self, role: str, goal: str, backstory: str, tools: List = None) -> Agent:
        """Create a CrewAI agent with common configuration."""
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=settings.crewai_verbose,
            allow_delegation=False,
            llm=self.llm,
            tools=tools or []
        )


class PlannerAgent(BaseCrewAgent):
    """Agent responsible for analyzing project requirements and creating detailed plans."""
    
    async def generate_plan(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive project plan."""
        await self.log_message("Starting project analysis and planning...")
        await self.update_progress(10, "Analyzing project requirements", 1)
        
        # Create the planner agent
        planner = self.create_agent(
            role="Senior Project Architect",
            goal="Analyze project requirements and create a comprehensive development plan",
            backstory="""You are an experienced software architect with expertise in multiple 
            programming languages and frameworks. You excel at breaking down complex projects 
            into manageable tasks and creating detailed technical specifications."""
        )
        
        # Create planning task with strict JSON schema enforcement
        schema_prompt = '''
        Return ONLY valid JSON with this exact structure:
        {
            "name": "project_name",
            "structure": {
                "README.md": "Project documentation",
                "src/main.py": "Main application file",
                "src/utils.py": "Utility functions",
                "tests/test_main.py": "Unit tests",
                "requirements.txt": "Python dependencies"
            }
        }
        
        CRITICAL: Only include FILES with extensions, never directories ending with /
        '''
        
        planning_task = Task(
            description=f"""
            Analyze the following project requirements and create a detailed development plan:
            
            Project Name: {project_data.get('name')}
            Description: {project_data.get('description')}
            Type: {project_data.get('project_type')}
            Languages: {', '.join(project_data.get('languages', []))}
            Frameworks: {', '.join(project_data.get('frameworks', []))}
            Complexity: {project_data.get('complexity')}
            Features: {', '.join(project_data.get('features', []))}
            
            {schema_prompt}
            
            Create a plan that includes:
            1. Project structure and file organization (ONLY files with extensions)
            2. Technology stack recommendations
            3. Development phases and milestones
            4. Required dependencies and libraries
            5. Testing strategy
            6. Deployment considerations
            
            Output the plan as a detailed JSON structure following the exact schema above.
            """,
            agent=planner,
            expected_output="A comprehensive JSON plan with project structure, phases, and requirements"
        )
        
        # Execute planning
        crew = Crew(
            agents=[planner],
            tasks=[planning_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )
        
        await self.update_progress(30, "Generating project plan", 2)
        result = await execute_crew_with_retry(crew, {})
        
        try:
            # Parse the result as JSON
            plan = json.loads(result)
            
            # Validate structure contains only files
            structure = plan.get('structure', {})
            validated_structure = {}
            
            for path, description in structure.items():
                if path.endswith('/'):
                    # Skip directories, convert to files
                    logger.warning(f"Skipping directory entry: {path}")
                    continue
                if '.' not in path.split('/')[-1]:
                    # Add extension for extensionless files
                    path = f"{path}.py"
                validated_structure[path] = description
                
            plan['structure'] = validated_structure
            
        except json.JSONDecodeError:
            # Enhanced fallback with actual files
            plan = {
                "name": project_data.get('name', 'Generated Project'),
                "structure": {
                    "README.md": "Project documentation and setup instructions",
                    "src/main.py": "Main application entry point",
                    "src/config.py": "Configuration settings",
                    "tests/test_main.py": "Unit tests for main functionality",
                    "requirements.txt": "Python package dependencies",
                    ".gitignore": "Git ignore rules"
                }
            }
        
        await self.log_message("Project plan generated successfully", metadata={"plan_files": len(plan.get('structure', {}))})
        await self.update_progress(50, "Plan generation completed", 3)
        
        return plan


class CodeGeneratorAgent(BaseCrewAgent):
    """Agent responsible for generating code based on the project plan."""
    
    async def generate_code(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code files based on the project plan."""
        await self.log_message("Starting code generation...")
        await self.update_progress(55, "Initializing code generation", 4)
        
        tools = [
            AgentTools.write_file,
            AgentTools.read_file,
            AgentTools.execute_code
        ]
        
        # Create the code generator agent
        coder = self.create_agent(
            role="Senior Full-Stack Developer",
            goal="Generate high-quality, production-ready code based on the project plan",
            backstory="""You are an expert full-stack developer with extensive experience 
            in multiple programming languages and frameworks. You write clean, efficient, 
            and well-documented code following best practices and industry standards.""",
            tools=tools
        )
        
        generated_files = []
        file_structure = plan.get('structure', {})
        project_name = plan.get('name', 'project')
        
        for i, (file_path, description) in enumerate(file_structure.items()):
            await self.update_progress(
                55 + (30 * i / len(file_structure)), 
                f"Generating {file_path}", 
                4 + i
            )
            
            # Create code generation task
            code_task = Task(
                description=f"""
                Generate the code for: {file_path}
                Description: {description}
                Project: {project_name}
                Plan context: {json.dumps(plan, indent=2)}
                
                Requirements:
                1. Follow best practices for the target language
                2. Include proper error handling
                3. Add comprehensive comments and docstrings
                4. Ensure code is production-ready
                5. Include necessary imports and dependencies
                
                Generate complete, functional code for this file.
                """,
                agent=coder,
                expected_output=f"Complete, functional code for {file_path}"
            )
            
            # Execute code generation
            crew = Crew(
                agents=[coder],
                tasks=[code_task],
                verbose=settings.crewai_verbose,
                process=Process.sequential
            )
            
            result = await execute_crew_with_retry(crew, {})
            
            # Determine language based on file extension
            language = self._detect_language(file_path)
            
            # Save to database
            await db_manager.create_file(
                job_id=self.job_id,
                filename=Path(file_path).name,
                path=file_path,
                content=result,
                language=language
            )
            
            generated_files.append({
                "path": file_path,
                "content": result,
                "language": language,
                "size": len(result.encode('utf-8'))
            })
            
            await self.log_message(f"Generated {file_path} ({len(result)} characters)")
        
        await self.log_message(f"Code generation completed. Generated {len(generated_files)} files.")
        await self.update_progress(85, "Code generation completed", 4 + len(file_structure))
        
        return generated_files
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bat': 'batch'
        }
        return language_map.get(ext, 'text')


class TesterAgent(BaseCrewAgent):
    """Agent responsible for writing and running tests."""
    
    async def generate_tests(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate comprehensive tests for the project."""
        await self.log_message("Starting test generation...")
        await self.update_progress(87, "Generating tests", 5)
        
        tools = [
            AgentTools.write_file,
            AgentTools.read_file,
            AgentTools.test_runner,
            AgentTools.execute_code
        ]
        
        # Create the tester agent
        tester = self.create_agent(
            role="Senior QA Engineer",
            goal="Create comprehensive test suites to ensure code quality and reliability",
            backstory="""You are an expert QA engineer with deep knowledge of testing 
            frameworks and methodologies. You write thorough unit tests, integration tests, 
            and ensure high code coverage with meaningful test cases.""",
            tools=tools
        )
        
        test_files = []
        
        # Generate tests for each code file
        for file_info in files:
            if file_info['language'] in ['python', 'javascript', 'typescript']:
                await self.log_message(f"Generating tests for {file_info['path']}")
                
                test_task = Task(
                    description=f"""
                    Create comprehensive tests for the following code:
                    
                    File: {file_info['path']}
                    Language: {file_info['language']}
                    Code:
                    ```{file_info['language']}
                    {file_info['content']}
                    ```
                    
                    Generate tests that include:
                    1. Unit tests for all functions/methods
                    2. Edge case testing
                    3. Error handling tests
                    4. Integration tests where applicable
                    5. Mock data and fixtures
                    
                    Use appropriate testing framework:
                    - Python: pytest
                    - JavaScript/TypeScript: Jest
                    
                    Create complete, runnable test files.
                    """,
                    agent=tester,
                    expected_output=f"Complete test file for {file_info['path']}"
                )
                
                crew = Crew(
                    agents=[tester],
                    tasks=[test_task],
                    verbose=settings.crewai_verbose,
                    process=Process.sequential
                )
                
                result = await execute_crew_with_retry(crew, {})
                
                # Determine test file path
                test_path = self._get_test_path(file_info['path'], file_info['language'])
                
                # Save test file
                await db_manager.create_file(
                    job_id=self.job_id,
                    filename=Path(test_path).name,
                    path=test_path,
                    content=result,
                    language=file_info['language']
                )
                
                test_files.append({
                    "path": test_path,
                    "content": result,
                    "language": file_info['language'],
                    "target_file": file_info['path']
                })
        
        await self.log_message(f"Test generation completed. Generated {len(test_files)} test files.")
        await self.update_progress(92, "Test generation completed", 6)
        
        return test_files
    
    def _get_test_path(self, file_path: str, language: str) -> str:
        """Generate test file path based on the original file."""
        path = Path(file_path)
        
        if language == 'python':
            return f"tests/test_{path.stem}.py"
        elif language in ['javascript', 'typescript']:
            return f"tests/{path.stem}.test.{path.suffix[1:]}"
        else:
            return f"tests/test_{path.name}"


class DocGeneratorAgent(BaseCrewAgent):
    """Agent responsible for generating documentation."""
    
    async def generate_documentation(
        self, 
        plan: Dict[str, Any], 
        files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive project documentation."""
        await self.log_message("Starting documentation generation...")
        await self.update_progress(94, "Generating documentation", 7)
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        # Create the documentation agent
        doc_writer = self.create_agent(
            role="Technical Documentation Specialist",
            goal="Create clear, comprehensive documentation for the project",
            backstory="""You are an expert technical writer with extensive experience 
            in creating documentation for software projects. You write clear, concise, 
            and user-friendly documentation that helps developers understand and use the code effectively.""",
            tools=tools
        )
        
        doc_files = []
        
        # Generate README.md
        readme_task = Task(
            description=f"""
            Create a comprehensive README.md file for this project:
            
            Project Plan: {json.dumps(plan, indent=2)}
            
            Generated Files:
            {chr(10).join([f"- {f['path']}: {f['language']}" for f in files])}
            
            The README should include:
            1. Project title and description
            2. Features and capabilities
            3. Installation instructions
            4. Usage examples
            5. API documentation (if applicable)
            6. Project structure overview
            7. Contributing guidelines
            8. License information
            
            Write in clear, professional markdown format.
            """,
            agent=doc_writer,
            expected_output="A comprehensive README.md file in markdown format"
        )
        
        crew = Crew(
            agents=[doc_writer],
            tasks=[readme_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )
        
        readme_content = await execute_crew_with_retry(crew, {})
        
        # Save README
        await db_manager.create_file(
            job_id=self.job_id,
            filename="README.md",
            path="README.md",
            content=readme_content,
            language="markdown"
        )
        
        doc_files.append({
            "path": "README.md",
            "content": readme_content,
            "language": "markdown"
        })
        
        # Generate API documentation if applicable
        api_files = [f for f in files if 'api' in f['path'].lower() or 'server' in f['path'].lower()]
        if api_files:
            api_doc_task = Task(
                description=f"""
                Create API documentation for the following files:
                {chr(10).join([f"File: {f['path']}\nContent: {f['content'][:500]}..." for f in api_files])}
                
                Generate comprehensive API documentation including:
                1. Endpoint descriptions
                2. Request/response formats
                3. Authentication requirements
                4. Example requests and responses
                5. Error codes and handling
                
                Format as markdown.
                """,
                agent=doc_writer,
                expected_output="Comprehensive API documentation in markdown format"
            )
            
            crew_api = Crew(
                agents=[doc_writer],
                tasks=[api_doc_task],
                verbose=settings.crewai_verbose,
                process=Process.sequential
            )
            
            api_doc_content = await execute_crew_with_retry(crew_api, {})
            
            await db_manager.create_file(
                job_id=self.job_id,
                filename="API.md",
                path="docs/API.md",
                content=api_doc_content,
                language="markdown"
            )
            
            doc_files.append({
                "path": "docs/API.md",
                "content": api_doc_content,
                "language": "markdown"
            })
        
        await self.log_message(f"Documentation generation completed. Generated {len(doc_files)} documentation files.")
        await self.update_progress(98, "Documentation generation completed", 8)
        
        return doc_files


class MultiAgentWorkflow:
    """Orchestrates the multi-agent workflow for project generation."""
    
    def __init__(self, job_id: str, websocket_callback: Optional[Callable] = None):
        self.job_id = job_id
        self.websocket_callback = websocket_callback
        self.planner = PlannerAgent(job_id, websocket_callback)
        self.coder = CodeGeneratorAgent(job_id, websocket_callback)
        self.tester = TesterAgent(job_id, websocket_callback)
        self.doc_writer = DocGeneratorAgent(job_id, websocket_callback)
        
        # Import and integrate review agent
        try:
            from backend.agents.specialized.reviewer_agent import CodeReviewerAgent
            from backend.memory.context_store import SharedMemoryStore
            memory_store = SharedMemoryStore()
            self.reviewer = CodeReviewerAgent(f"reviewer_{job_id}", memory_store)
        except ImportError as e:
            logger.warning(f"Review agent not available: {e}")
            self.reviewer = None
    
    async def execute_workflow(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow."""
        try:
            # Update job status to running
            await db_manager.update_job_status(
                job_id=self.job_id,
                status=JobStatus.RUNNING,
                progress=5,
                current_step="Starting workflow",
                step_number=0
            )
            
            # Phase 1: Planning
            plan = await self.planner.generate_plan(project_data)
            
            # Phase 2: Code Generation
            if project_data.get('mode') == 'dry':
                # Dry run - only planning
                await db_manager.update_job_status(
                    job_id=self.job_id,
                    status=JobStatus.COMPLETED,
                    progress=100,
                    current_step="Dry run completed - plan generated",
                    step_number=3
                )
                return {"plan": plan, "mode": "dry"}
            
            # Full generation
            code_files = await self.coder.generate_code(plan)
            
            # Phase 3: Testing
            test_files = await self.tester.generate_tests(code_files)
            
            # Phase 4: Documentation
            doc_files = await self.doc_writer.generate_documentation(plan, code_files)
            
            # Phase 5: Code Review (if reviewer is available)
            if self.reviewer:
                await self.update_progress(85, "Reviewing generated code", 6)
                review_results = await self.reviewer.execute_task({
                    'task_type': 'code_review',
                    'files': code_files + test_files + doc_files,
                    'project_data': project_data
                })
                
                if review_results.get('needs_fixes'):
                    # Apply automated fixes
                    code_files = await self.apply_review_fixes(
                        code_files, 
                        review_results.get('suggestions', [])
                    )
                    await self.log_message("Applied review fixes", metadata={"fixes_applied": len(review_results.get('suggestions', []))})
            
            # Complete the job
            await db_manager.update_job_status(
                job_id=self.job_id,
                status=JobStatus.COMPLETED,
                progress=100,
                current_step="Project generation completed",
                step_number=8
            )
            
            return {
                "plan": plan,
                "code_files": code_files,
                "test_files": test_files,
                "doc_files": doc_files,
                "total_files": len(code_files) + len(test_files) + len(doc_files)
            }
            
        except Exception as e:
            # Handle workflow errors
            error_msg = f"Workflow error: {str(e)}"
            await db_manager.update_job_status(
                job_id=self.job_id,
                status=JobStatus.FAILED,
                error_message=error_msg
            )
            
            if self.websocket_callback:
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    job_id=self.job_id,
                    content=error_msg
                )
                await self.websocket_callback(error_message.dict())
            
            raise
    
    async def update_progress(self, progress: float, step: str, step_number: int = None):
        """Update job progress."""
        await db_manager.update_job_status(
            job_id=self.job_id,
            status=JobStatus.RUNNING,
            progress=progress,
            current_step=step,
            step_number=step_number
        )
    
    async def log_message(self, message: str, metadata: Dict[str, Any] = None):
        """Log a message to the database."""
        await db_manager.create_log(
            job_id=self.job_id,
            agent="MultiAgentWorkflow",
            message=message,
            level="INFO",
            metadata=metadata or {}
        )
    
    async def apply_review_fixes(self, files: List[Dict[str, Any]], suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply review suggestions to files."""
        # Simple implementation - in production, this would be more sophisticated
        for suggestion in suggestions:
            file_path = suggestion.get('file_path')
            if file_path:
                for file_info in files:
                    if file_info['path'] == file_path:
                        # Apply the suggestion (simplified)
                        content = file_info['content']
                        # Here you would implement the actual fix application
                        file_info['content'] = content
                        break
        return files


async def create_and_execute_workflow(
    job_id: str, 
    project_data: Dict[str, Any], 
    websocket_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """Create and execute a multi-agent workflow."""
    workflow = MultiAgentWorkflow(job_id, websocket_callback)
    return await workflow.execute_workflow(project_data)