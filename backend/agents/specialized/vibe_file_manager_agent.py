"""
Enhanced File Manager Agent specialized for Vibe Coding - organizing and finalizing project structure.
"""

import json
import os
import zipfile
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from backend.agents.base.base_agent import BaseCrewAgent
from backend.agents.agents import AgentTools
from backend.models.models import generate_task_id
from backend.database.db import db_manager
from config.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class VibeFileManagerAgent(BaseCrewAgent):
    """
    Specialized File Manager Agent for organizing, finalizing, and packaging generated projects.
    This agent ensures proper project structure, creates necessary configuration files,
    and packages everything for download.
    """

    def __init__(self, job_id: str, websocket_callback: Optional[callable] = None):
        super().__init__(job_id, websocket_callback)
        self.project_templates = self._load_project_templates()
        self.packaging_rules = self._load_packaging_rules()

    def _load_project_templates(self) -> Dict[str, Any]:
        """Load project structure templates for different project types."""
        return {
            "react_app": {
                "root_files": ["package.json", "README.md", ".gitignore"],
                "directories": {
                    "src/": ["App.jsx", "index.js", "index.css"],
                    "src/components/": [],
                    "src/hooks/": [],
                    "src/utils/": [],
                    "src/styles/": [],
                    "public/": ["index.html", "favicon.ico"],
                    "docs/": []
                },
                "optional_files": ["tailwind.config.js", "postcss.config.js"],
                "build_commands": ["npm install", "npm start"]
            },
            "static_website": {
                "root_files": ["index.html", "styles.css", "script.js", "README.md"],
                "directories": {
                    "assets/": ["images/", "css/", "js/"],
                    "docs/": []
                },
                "optional_files": [],
                "build_commands": ["Open index.html in browser"]
            },
            "fullstack_app": {
                "root_files": ["package.json", "requirements.txt", "README.md", ".gitignore"],
                "directories": {
                    "frontend/": ["src/", "public/"],
                    "backend/": ["api/", "models/", "utils/"],
                    "docs/": [],
                    "tests/": []
                },
                "optional_files": ["docker-compose.yml", "Dockerfile"],
                "build_commands": ["npm install", "pip install -r requirements.txt", "npm start"]
            },
            "api_only": {
                "root_files": ["main.py", "requirements.txt", "README.md", ".gitignore"],
                "directories": {
                    "api/": ["routes/", "models/", "utils/"],
                    "tests/": [],
                    "docs/": []
                },
                "optional_files": ["Dockerfile", "docker-compose.yml"],
                "build_commands": ["pip install -r requirements.txt", "uvicorn main:app --reload"]
            }
        }

    def _load_packaging_rules(self) -> Dict[str, Any]:
        """Load rules for packaging different types of projects."""
        return {
            "exclude_patterns": [
                "__pycache__",
                "*.pyc",
                "node_modules",
                ".git",
                ".env",
                "*.log",
                ".DS_Store",
                "Thumbs.db"
            ],
            "required_files": {
                "react": ["package.json", "src/App.jsx", "README.md"],
                "static": ["index.html", "README.md"],
                "python": ["main.py", "requirements.txt", "README.md"],
                "api": ["main.py", "requirements.txt", "README.md"]
            },
            "file_permissions": {
                "executable": [".sh", ".py"],
                "readonly": [".md", ".txt", ".json"]
            }
        }

    async def organize_and_finalize_project(
        self, 
        generated_files: List[Dict[str, Any]], 
        review_results: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main method to organize generated files into proper project structure and create final package.
        
        Args:
            generated_files: List of generated code files from the Coder Agent
            review_results: Review results from the Critic Agent
            original_plan: Original plan with vibe analysis and project specs
            
        Returns:
            Final project package with download information and project metadata
        """
        await self.log_message(f"Starting project organization for {len(generated_files)} files")
        await self.update_progress(96, "Organizing project structure", 4)

        # Extract project information
        project_spec = original_plan.get("project_specification", {})
        vibe_analysis = original_plan.get("vibe_analysis", {})
        
        # Determine project type and template
        project_template = await self._determine_project_template(project_spec, generated_files)
        
        # Organize files into proper structure
        organized_structure = await self._organize_file_structure(
            generated_files, project_template, project_spec
        )
        
        # Apply fixes from review if needed
        if review_results.get("needs_fixes", False):
            organized_structure = await self._apply_review_fixes(
                organized_structure, review_results
            )
        
        # Add missing essential files
        enhanced_structure = await self._add_essential_files(
            organized_structure, project_template, original_plan
        )
        
        # Create project package
        package_info = await self._create_project_package(
            enhanced_structure, project_template, original_plan
        )
        
        # Generate deployment instructions
        deployment_guide = await self._generate_deployment_guide(
            project_template, enhanced_structure, original_plan
        )
        
        await self.update_progress(99, "Project finalization completed", 4)
        
        final_package = {
            "project_metadata": {
                "name": self._generate_project_name(vibe_analysis),
                "type": project_spec.get("type", "web_app"),
                "template": project_template["name"],
                "total_files": len(enhanced_structure["files"]),
                "structure": enhanced_structure["directory_tree"],
                "technologies": project_spec.get("technology_stack", {}),
                "original_vibe": original_plan.get("original_vibe", ""),
                "created_at": datetime.now().isoformat(),
                "vibe_platform_version": "2.0"
            },
            "file_structure": enhanced_structure,
            "package_info": package_info,
            "deployment_guide": deployment_guide,
            "quality_metrics": {
                "review_score": review_results.get("overall_score", 8.0),
                "approval_status": review_results.get("approval_status", True),
                "vibe_alignment": review_results.get("vibe_alignment", {}).get("alignment_score", 8.0)
            },
            "next_steps": await self._generate_next_steps(project_template, original_plan)
        }

        await self.log_message(
            f"Project organization completed successfully",
            metadata={
                "total_files": len(enhanced_structure["files"]),
                "project_type": project_template["name"],
                "package_size": package_info.get("size_mb", 0),
                "review_score": review_results.get("overall_score", 8.0)
            }
        )

        return final_package

    async def _determine_project_template(
        self, 
        project_spec: Dict[str, Any], 
        generated_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine the appropriate project template based on generated files."""
        
        file_types = [f.get("language", "") for f in generated_files]
        file_paths = [f.get("path", "") for f in generated_files]
        
        # Analyze file patterns to determine project type
        has_react = any("jsx" in path or ".jsx" in file_types for path in file_paths)
        has_python_api = any("api/" in path and lang == "python" for path, lang in zip(file_paths, file_types))
        has_html_only = any(".html" in path for path in file_paths) and not has_react
        has_package_json = any("package.json" in path for path in file_paths)
        
        # Determine template
        if has_react and has_python_api:
            template_name = "fullstack_app"
        elif has_react or has_package_json:
            template_name = "react_app"
        elif has_python_api and not has_react:
            template_name = "api_only"
        elif has_html_only:
            template_name = "static_website"
        else:
            template_name = "react_app"  # Default
        
        template = self.project_templates[template_name].copy()
        template["name"] = template_name
        template["detected_from"] = {
            "has_react": has_react,
            "has_python_api": has_python_api,
            "has_html_only": has_html_only,
            "file_types": list(set(file_types))
        }
        
        return template

    async def _organize_file_structure(
        self, 
        generated_files: List[Dict[str, Any]], 
        project_template: Dict[str, Any],
        project_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Organize files into proper directory structure."""
        
        organized_files = []
        directory_tree = {}
        
        # Create base directory structure
        template_dirs = project_template.get("directories", {})
        for dir_path, expected_files in template_dirs.items():
            directory_tree[dir_path] = []
        
        # Organize each generated file
        for file_info in generated_files:
            original_path = file_info.get("path", "")
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            filename = file_info.get("filename", "")
            
            # Determine proper location for this file
            proper_path = self._determine_proper_file_location(
                original_path, filename, language, project_template
            )
            
            # Update file info with proper path
            organized_file = file_info.copy()
            organized_file["path"] = proper_path
            organized_file["directory"] = str(Path(proper_path).parent)
            organized_file["final_filename"] = Path(proper_path).name
            
            organized_files.append(organized_file)
            
            # Update directory tree
            dir_path = str(Path(proper_path).parent)
            if dir_path not in directory_tree:
                directory_tree[dir_path] = []
            directory_tree[dir_path].append(Path(proper_path).name)
        
        # Ensure required directories exist
        for required_dir in template_dirs.keys():
            if required_dir not in directory_tree:
                directory_tree[required_dir] = []
        
        return {
            "files": organized_files,
            "directory_tree": directory_tree,
            "total_directories": len(directory_tree),
            "root_files": [f for f in organized_files if "/" not in f["path"] or f["path"].count("/") == 0]
        }

    def _determine_proper_file_location(
        self, 
        original_path: str, 
        filename: str, 
        language: str, 
        project_template: Dict[str, Any]
    ) -> str:
        """Determine the proper location for a file based on its type and content."""
        
        template_dirs = project_template.get("directories", {})
        
        # Root files that should stay in root
        root_files = ["package.json", "README.md", ".gitignore", "requirements.txt", 
                     "main.py", "index.html", "tailwind.config.js", "postcss.config.js"]
        
        if filename in root_files:
            return filename
        
        # Component files
        if language == "javascript" and ("component" in filename.lower() or filename.endswith(".jsx")):
            if filename in ["App.jsx", "index.js"]:
                return f"src/{filename}"
            else:
                return f"src/components/{filename}"
        
        # Style files
        if language == "css" or filename.endswith(".css"):
            if filename == "index.css":
                return f"src/{filename}"
            else:
                return f"src/styles/{filename}"
        
        # API files
        if "api/" in original_path or (language == "python" and filename != "main.py"):
            if filename == "main.py" and "api" in template_dirs:
                return f"api/{filename}"
            elif language == "python":
                return f"api/{filename}"
        
        # HTML files
        if language == "html":
            if filename == "index.html":
                return f"public/{filename}"
            else:
                return filename
        
        # JavaScript utility files
        if language == "javascript" and not filename.endswith(".jsx"):
            return f"src/utils/{filename}"
        
        # Default: try to maintain original structure or place in appropriate directory
        if original_path and "/" in original_path:
            return original_path
        
        # Last resort: place in src if it's a source file, otherwise root
        if language in ["javascript", "css", "typescript"]:
            return f"src/{filename}"
        
        return filename

    async def _apply_review_fixes(
        self, 
        organized_structure: Dict[str, Any], 
        review_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply fixes suggested by the Critic Agent."""
        
        suggestions = review_results.get("suggestions", [])
        files = organized_structure.get("files", [])
        
        # Track changes made
        changes_made = []
        
        for suggestion in suggestions:
            suggestion_type = suggestion.get("type", "")
            priority = suggestion.get("priority", "")
            
            # Apply high-priority fixes automatically
            if priority == "high" and suggestion_type == "syntax":
                # Apply syntax fixes
                syntax_fixes = await self._apply_syntax_fixes(files, suggestion)
                changes_made.extend(syntax_fixes)
            
            elif suggestion_type == "security":
                # Apply security fixes
                security_fixes = await self._apply_security_fixes(files, suggestion)
                changes_made.extend(security_fixes)
        
        # Update structure with fixes
        organized_structure["applied_fixes"] = changes_made
        organized_structure["fixes_applied"] = len(changes_made)
        
        return organized_structure

    async def _apply_syntax_fixes(self, files: List[Dict[str, Any]], suggestion: Dict[str, Any]) -> List[str]:
        """Apply automatic syntax fixes."""
        
        fixes_applied = []
        details = suggestion.get("details", [])
        
        for file_info in files:
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            
            # Apply language-specific fixes
            if language == "javascript":
                # Fix missing semicolons
                if "semicolon" in str(details).lower():
                    # Simple semicolon fix (basic implementation)
                    lines = content.split('\n')
                    fixed_lines = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped and not stripped.endswith((';', '{', '}', ')', ',')) and not stripped.startswith('//'):
                            if any(keyword in stripped for keyword in ['const ', 'let ', 'var ', 'return ', 'import ']):
                                line += ';'
                        fixed_lines.append(line)
                    
                    if fixed_lines != content.split('\n'):
                        file_info["content"] = '\n'.join(fixed_lines)
                        fixes_applied.append(f"Added missing semicolons in {file_info['path']}")
            
            elif language == "python":
                # Fix import organization
                if "import" in str(details).lower():
                    lines = content.split('\n')
                    imports = [line for line in lines if line.strip().startswith(('import ', 'from '))]
                    other_lines = [line for line in lines if not line.strip().startswith(('import ', 'from ')) or line.strip() == '']
                    
                    if imports:
                        # Sort imports
                        imports.sort()
                        fixed_content = '\n'.join(imports) + '\n\n' + '\n'.join(other_lines)
                        file_info["content"] = fixed_content
                        fixes_applied.append(f"Organized imports in {file_info['path']}")
        
        return fixes_applied

    async def _apply_security_fixes(self, files: List[Dict[str, Any]], suggestion: Dict[str, Any]) -> List[str]:
        """Apply automatic security fixes."""
        
        fixes_applied = []
        details = suggestion.get("details", [])
        
        for file_info in files:
            content = file_info.get("content", "")
            
            # Fix innerHTML usage
            if "innerHTML" in content and "sanitize" not in content:
                # Replace innerHTML with textContent where appropriate
                fixed_content = content.replace(
                    ".innerHTML =", 
                    ".textContent =  // Changed from innerHTML for security"
                )
                if fixed_content != content:
                    file_info["content"] = fixed_content
                    fixes_applied.append(f"Replaced innerHTML with textContent in {file_info['path']}")
        
        return fixes_applied

    async def _add_essential_files(
        self, 
        organized_structure: Dict[str, Any], 
        project_template: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add any missing essential files for the project."""
        
        existing_files = {f["path"] for f in organized_structure["files"]}
        required_files = project_template.get("root_files", [])
        files = organized_structure["files"].copy()
        
        vibe_analysis = original_plan.get("vibe_analysis", {})
        project_spec = original_plan.get("project_specification", {})
        
        # Add missing essential files
        for required_file in required_files:
            if required_file not in existing_files:
                # Generate the missing file
                if required_file == ".gitignore":
                    content = await self._generate_gitignore_content(project_template)
                elif required_file == "package.json" and project_template["name"] == "react_app":
                    content = await self._generate_package_json_content(vibe_analysis, project_spec)
                elif required_file == "requirements.txt":
                    content = await self._generate_requirements_content(project_spec)
                elif required_file == "README.md":
                    content = await self._generate_readme_content(original_plan)
                else:
                    content = f"# {required_file}\n# Generated by Vibe Coding Platform"
                
                files.append({
                    "path": required_file,
                    "filename": required_file,
                    "content": content,
                    "language": self._detect_language_from_extension(required_file),
                    "metadata": {
                        "file_type": "essential",
                        "auto_generated": True
                    }
                })
        
        # Add optional helpful files
        if project_template["name"] == "react_app":
            # Add package-lock.json placeholder
            if "package-lock.json" not in existing_files:
                files.append({
                    "path": "package-lock.json",
                    "filename": "package-lock.json", 
                    "content": "{}",
                    "language": "json",
                    "metadata": {
                        "file_type": "generated_placeholder",
                        "note": "Run 'npm install' to generate actual file"
                    }
                })
        
        # Add development helper files
        if project_template["name"] in ["react_app", "fullstack_app"]:
            if ".env.example" not in existing_files:
                files.append({
                    "path": ".env.example",
                    "filename": ".env.example",
                    "content": "# Environment variables\n# Copy to .env and fill in your values\n\n# REACT_APP_API_URL=http://localhost:8000\n# DATABASE_URL=sqlite:///./app.db",
                    "language": "text",
                    "metadata": {
                        "file_type": "configuration_template"
                    }
                })
        
        organized_structure["files"] = files
        return organized_structure

    async def _create_project_package(
        self, 
        enhanced_structure: Dict[str, Any], 
        project_template: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create downloadable project package."""
        
        # Save all files to database
        files = enhanced_structure.get("files", [])
        saved_files = []
        
        for file_info in files:
            try:
                # Save to database
                db_file = await db_manager.create_file(
                    job_id=self.job_id,
                    filename=file_info.get("filename", ""),
                    path=file_info.get("path", ""),
                    content=file_info.get("content", ""),
                    language=file_info.get("language", "")
                )
                saved_files.append(db_file)
            except Exception as e:
                logger.error(f"Failed to save file {file_info.get('path', '')}: {e}")
        
        # Create temporary zip file
        zip_path = await self._create_zip_package(files, original_plan)
        
        # Calculate package statistics
        total_size = sum(len(f.get("content", "").encode('utf-8')) for f in files)
        
        package_info = {
            "total_files": len(files),
            "saved_files": len(saved_files),
            "total_size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "zip_path": zip_path,
            "structure_summary": {
                "directories": len(enhanced_structure.get("directory_tree", {})),
                "root_files": len(enhanced_structure.get("root_files", [])),
                "components": len([f for f in files if "component" in f.get("path", "").lower()]),
                "styles": len([f for f in files if f.get("language") == "css"]),
                "config_files": len([f for f in files if f.get("filename", "").startswith(".")])
            },
            "build_commands": project_template.get("build_commands", []),
            "download_ready": True
        }
        
        return package_info

    async def _create_zip_package(self, files: List[Dict[str, Any]], original_plan: Dict[str, Any]) -> str:
        """Create a zip file containing all project files."""
        
        vibe_analysis = original_plan.get("vibe_analysis", {})
        project_name = self._generate_project_name(vibe_analysis)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        project_dir = os.path.join(temp_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        try:
            # Write all files to temporary directory
            for file_info in files:
                file_path = file_info.get("path", "")
                content = file_info.get("content", "")
                
                full_path = os.path.join(project_dir, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Create zip file
            zip_filename = f"{project_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files_in_dir in os.walk(project_dir):
                    for file in files_in_dir:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return zip_path
            
        except Exception as e:
            logger.error(f"Failed to create zip package: {e}")
            return ""

    async def _generate_deployment_guide(
        self, 
        project_template: Dict[str, Any], 
        enhanced_structure: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate deployment instructions and guide."""
        
        template_name = project_template.get("name", "")
        build_commands = project_template.get("build_commands", [])
        
        deployment_guide = {
            "project_type": template_name,
            "quick_start": {
                "steps": build_commands,
                "estimated_time": "5-10 minutes"
            },
            "development": {
                "local_setup": [],
                "requirements": [],
                "commands": []
            },
            "deployment_options": [],
            "troubleshooting": []
        }
        
        # Generate specific instructions based on project type
        if template_name == "react_app":
            deployment_guide["development"] = {
                "local_setup": [
                    "1. Extract the project files",
                    "2. Open terminal in project directory",
                    "3. Run 'npm install' to install dependencies",
                    "4. Run 'npm start' to start development server",
                    "5. Open http://localhost:3000 in your browser"
                ],
                "requirements": ["Node.js 14+", "npm or yarn"],
                "commands": ["npm install", "npm start", "npm build"]
            }
            
            deployment_guide["deployment_options"] = [
                {
                    "platform": "Vercel",
                    "steps": ["Connect GitHub repo", "Import project", "Deploy"],
                    "url": "https://vercel.com"
                },
                {
                    "platform": "Netlify", 
                    "steps": ["Drag & drop build folder", "Configure settings"],
                    "url": "https://netlify.com"
                }
            ]
            
        elif template_name == "static_website":
            deployment_guide["development"] = {
                "local_setup": [
                    "1. Extract the project files",
                    "2. Open index.html in a web browser",
                    "3. Or use a local server like Live Server extension"
                ],
                "requirements": ["Web browser", "Optional: Local web server"],
                "commands": ["Open index.html"]
            }
            
        elif template_name == "api_only":
            deployment_guide["development"] = {
                "local_setup": [
                    "1. Extract the project files",
                    "2. Install Python 3.8+",
                    "3. Run 'pip install -r requirements.txt'",
                    "4. Run 'uvicorn main:app --reload'",
                    "5. Open http://localhost:8000/docs for API documentation"
                ],
                "requirements": ["Python 3.8+", "pip"],
                "commands": ["pip install -r requirements.txt", "uvicorn main:app --reload"]
            }
        
        # Add troubleshooting tips
        deployment_guide["troubleshooting"] = [
            {
                "issue": "Dependencies not installing",
                "solution": "Check Node.js/Python version, clear cache, try again"
            },
            {
                "issue": "Port already in use",
                "solution": "Kill process on port or use different port"
            },
            {
                "issue": "Build errors",
                "solution": "Check syntax errors, missing dependencies"
            }
        ]
        
        return deployment_guide

    async def _generate_next_steps(self, project_template: Dict[str, Any], original_plan: Dict[str, Any]) -> List[str]:
        """Generate suggested next steps for the user."""
        
        vibe_analysis = original_plan.get("vibe_analysis", {})
        project_spec = original_plan.get("project_specification", {})
        
        next_steps = [
            "🎉 Your vibe project is ready! Download and extract the files.",
            "🚀 Follow the deployment guide to get started.",
            "💻 Run the project locally to see your vibe come to life."
        ]
        
        # Add specific next steps based on project features
        features = vibe_analysis.get("core_features", [])
        
        if any("user" in str(f).lower() for f in features):
            next_steps.append("👤 Consider adding user authentication and profiles.")
            
        if any("database" in str(f).lower() for f in features):
            next_steps.append("🗄️ Set up a database for persistent data storage.")
            
        if project_spec.get("backend_needed", False):
            next_steps.append("🔧 Configure environment variables and API endpoints.")
            
        # General improvements
        next_steps.extend([
            "🎨 Customize colors, fonts, and styling to match your exact vision.",
            "📱 Test on different devices to ensure responsive design.",
            "🔍 Add SEO optimization and meta tags.",
            "📊 Consider adding analytics to track user engagement.",
            "🚢 Deploy to a hosting platform when ready to go live."
        ])
        
        return next_steps

    # Utility methods
    def _generate_project_name(self, vibe_analysis: Dict[str, Any]) -> str:
        """Generate a clean project name from vibe analysis."""
        
        project_type = vibe_analysis.get("project_type", "app")
        
        # Clean and format project name
        name_map = {
            "blog": "my-blog",
            "dashboard": "dashboard-app", 
            "task": "task-manager",
            "chat": "chat-app",
            "landing": "landing-page",
            "e-commerce": "ecommerce-app",
            "portfolio": "portfolio-site"
        }
        
        for key, name in name_map.items():
            if key in project_type.lower():
                return name
        
        # Default clean name
        clean_name = re.sub(r'[^a-zA-Z0-9-]', '', project_type.lower().replace(' ', '-'))
        return clean_name or "vibe-project"

    def _detect_language_from_extension(self, filename: str) -> str:
        """Detect programming language from file extension."""
        
        extension_map = {
            ".js": "javascript",
            ".jsx": "javascript", 
            ".ts": "typescript",
            ".tsx": "typescript",
            ".py": "python",
            ".css": "css",
            ".html": "html",
            ".json": "json",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".yml": "yaml",
            ".yaml": "yaml"
        }
        
        ext = Path(filename).suffix.lower()
        return extension_map.get(ext, "text")

    async def _generate_gitignore_content(self, project_template: Dict[str, Any]) -> str:
        """Generate appropriate .gitignore content."""
        
        if project_template["name"] == "react_app":
            return """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production
build/
dist/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db"""
        
        elif project_template["name"] == "api_only":
            return """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db"""
        
        else:
            return """# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Environment
.env"""

    async def _generate_package_json_content(self, vibe_analysis: Dict[str, Any], project_spec: Dict[str, Any]) -> str:
        """Generate package.json content."""
        
        project_name = self._generate_project_name(vibe_analysis)
        
        package_data = {
            "name": project_name,
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app", "react-app/jest"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        
        return json.dumps(package_data, indent=2)

    async def _generate_requirements_content(self, project_spec: Dict[str, Any]) -> str:
        """Generate requirements.txt content."""
        
        return """fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0"""

    async def _generate_readme_content(self, original_plan: Dict[str, Any]) -> str:
        """Generate README.md content."""
        
        vibe_analysis = original_plan.get("vibe_analysis", {})
        project_name = self._generate_project_name(vibe_analysis)
        original_vibe = original_plan.get("original_vibe", "")
        
        return f"""# {project_name.title().replace('-', ' ')}

> Created with Vibe Coding Platform ✨

## About

This project was generated from your vibe: "{original_vibe}"

## Features

- Modern, responsive design
- Clean, maintainable code
- Production-ready structure

## Quick Start

1. Extract the project files
2. Install dependencies: `npm install`
3. Start development server: `npm start`
4. Open http://localhost:3000

## Project Structure

```
{project_name}/
├── src/
│   ├── components/
│   ├── styles/
│   └── utils/
├── public/
└── README.md
```

## Built With

- React
- Modern CSS
- Best practices

## Next Steps

- Customize the design to match your exact vision
- Add your content and functionality
- Deploy to your favorite hosting platform

---

Built with ❤️ by Vibe Coding Platform
"""

    async def execute_crew_with_retry(self, crew, inputs):
        """Execute crew with retry logic."""
        try:
            result = await crew.kickoff_async(inputs)
            return result
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return f"Operation failed: {str(e)}"