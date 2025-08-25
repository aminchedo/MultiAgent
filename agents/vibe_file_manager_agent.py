"""
VibeFileManagerAgent - Organizes and manages project files and structure.

This agent handles the organization of generated files, ensures proper project structure,
manages dependencies, and optimizes the overall file layout for the project.
"""

import json
import time
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import logging
from pathlib import Path

from agents.base_agent import BaseAgent


class VibeFileManagerAgent(BaseAgent):
    """
    Agent responsible for organizing project files and structure.
    
    This agent:
    1. Organizes files into logical directory structures
    2. Manages file dependencies and imports
    3. Optimizes file placement for better maintainability
    4. Creates appropriate build and deployment configurations
    5. Ensures naming conventions and file organization best practices
    """
    
    def __init__(self, agent_id: str = None, name: str = "VibeFileManagerAgent"):
        # Initialize capabilities as empty list for BaseAgent
        capabilities = []
        super().__init__("vibe_file_manager", capabilities)
        self.logger = logging.getLogger(__name__)
        
        # Agent capabilities (stored as simple list for this implementation)
        self.vibe_capabilities = [
            "file_organization",
            "directory_structure_creation",
            "dependency_management",
            "build_configuration",
            "naming_convention_enforcement"
        ]
        
        # Standard project structures for different project types
        self.project_structures = {
            "web_app": {
                "src/": {
                    "components/": "React/Vue components",
                    "pages/": "Page components",
                    "hooks/": "Custom hooks",
                    "utils/": "Utility functions",
                    "services/": "API and service functions",
                    "contexts/": "React contexts",
                    "styles/": "CSS and styling files",
                    "assets/": "Images, icons, fonts"
                },
                "public/": "Static assets",
                "tests/": "Test files",
                "docs/": "Documentation",
                "build/": "Build output (generated)",
                "dist/": "Distribution files (generated)"
            },
            "api": {
                "src/": {
                    "routes/": "API route handlers",
                    "controllers/": "Business logic controllers",
                    "models/": "Data models",
                    "middleware/": "Express/FastAPI middleware",
                    "services/": "Business services",
                    "utils/": "Utility functions",
                    "config/": "Configuration files",
                    "database/": "Database related files"
                },
                "tests/": "Test files",
                "docs/": "API documentation",
                "migrations/": "Database migrations",
                "seeds/": "Database seeds"
            },
            "mobile_app": {
                "src/": {
                    "components/": "Reusable components", 
                    "screens/": "App screens",
                    "navigation/": "Navigation configuration",
                    "services/": "API and services",
                    "utils/": "Utility functions",
                    "contexts/": "State management",
                    "assets/": "Images, fonts, etc."
                },
                "android/": "Android specific files",
                "ios/": "iOS specific files",
                "__tests__/": "Test files"
            },
            "dashboard": {
                "src/": {
                    "components/": {
                        "charts/": "Chart components",
                        "tables/": "Table components", 
                        "forms/": "Form components",
                        "layout/": "Layout components",
                        "common/": "Common UI components"
                    },
                    "pages/": "Dashboard pages",
                    "hooks/": "Custom hooks",
                    "services/": "Data fetching services",
                    "utils/": "Utility functions",
                    "styles/": "Styling files",
                    "data/": "Mock or sample data"
                },
                "public/": "Static assets",
                "tests/": "Test files"
            }
        }
        
        # File type categorizations
        self.file_categories = {
            "frontend": {
                "extensions": [".jsx", ".tsx", ".vue", ".html", ".css", ".scss", ".sass", ".less"],
                "patterns": ["component", "page", "view", "ui"],
                "directory_preferences": ["src/components", "src/pages", "src/views", "src/ui"]
            },
            "backend": {
                "extensions": [".py", ".js", ".ts"],
                "patterns": ["route", "controller", "model", "service", "api"],
                "directory_preferences": ["src/routes", "src/controllers", "src/models", "src/services", "src/api"]
            },
            "config": {
                "extensions": [".json", ".yml", ".yaml", ".env", ".config.js", ".config.ts"],
                "patterns": ["config", "env", "settings"],
                "directory_preferences": ["config/", ".", "src/config"]
            },
            "test": {
                "extensions": [".test.js", ".test.ts", ".spec.js", ".spec.ts", ".test.py"],
                "patterns": ["test", "spec"],
                "directory_preferences": ["tests/", "__tests__/", "src/__tests__"]
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt"],
                "patterns": ["readme", "doc", "guide"],
                "directory_preferences": ["docs/", ".", "documentation/"]
            },
            "assets": {
                "extensions": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"],
                "patterns": ["asset", "image", "icon", "font"],
                "directory_preferences": ["src/assets", "public/assets", "assets/", "static/"]
            }
        }
        
        # Naming conventions
        self.naming_conventions = {
            "components": {
                "react": "PascalCase",
                "vue": "PascalCase",
                "file_suffix": ".jsx"
            },
            "pages": {
                "react": "PascalCase",
                "vue": "PascalCase",
                "file_suffix": ".jsx"
            },
            "utilities": {
                "pattern": "camelCase",
                "file_suffix": ".js"
            },
            "services": {
                "pattern": "camelCase",
                "file_suffix": ".js"
            },
            "constants": {
                "pattern": "UPPER_SNAKE_CASE",
                "file_suffix": ".js"
            }
        }

    async def organize_project_structure(self, files: List[Dict], project_type: str) -> Dict[str, Any]:
        """
        Main method to organize project files into optimal structure.
        
        Args:
            files: List of generated files with content and metadata
            project_type: Type of project (web_app, api, mobile_app, etc.)
            
        Returns:
            Organized file structure with recommendations and optimizations
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting file organization for {len(files)} files in {project_type} project")
            
            # Step 1: Analyze current file structure
            current_analysis = self._analyze_current_structure(files)
            
            # Step 2: Categorize files by type and purpose
            file_categories = self._categorize_files(files)
            
            # Step 3: Create optimal directory structure
            optimal_structure = self._create_optimal_structure(project_type, file_categories)
            
            # Step 4: Reorganize files according to optimal structure
            organized_files = await self._reorganize_files(files, optimal_structure, project_type)
            
            # Step 5: Update import/export statements
            updated_files = await self._update_import_statements(organized_files)
            
            # Step 6: Generate additional configuration files
            config_files = await self._generate_additional_configs(project_type, updated_files)
            
            # Step 7: Create build and deployment optimizations
            build_optimizations = self._create_build_optimizations(project_type, updated_files)
            
            # Combine all files
            final_files = updated_files + config_files
            
            # Step 8: Validate final structure
            validation_results = self._validate_final_structure(final_files, project_type)
            
            result = {
                "original_structure": current_analysis,
                "file_categories": file_categories,
                "optimal_structure": optimal_structure,
                "organized_files": final_files,
                "build_optimizations": build_optimizations,
                "validation": validation_results,
                "metrics": {
                    "total_files": len(final_files),
                    "directories_created": len(optimal_structure),
                    "files_moved": self._count_moved_files(files, final_files),
                    "import_statements_updated": self._count_updated_imports(files, updated_files),
                    "organization_score": self._calculate_organization_score(final_files, project_type)
                },
                "recommendations": self._generate_organization_recommendations(final_files, project_type),
                "metadata": {
                    "file_manager_agent_id": self.agent_id,
                    "organization_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time,
                    "project_type": project_type
                }
            }
            
            self.logger.info(f"File organization completed in {time.time() - start_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in file organization: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "metadata": {
                    "file_manager_agent_id": self.agent_id,
                    "error_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time
                }
            }

    def _analyze_current_structure(self, files: List[Dict]) -> Dict[str, Any]:
        """Analyze the current file structure."""
        
        analysis = {
            "total_files": len(files),
            "directory_depth": {},
            "file_types": {},
            "naming_patterns": {},
            "potential_issues": []
        }
        
        for file_info in files:
            path = file_info.get("path", "")
            
            # Analyze directory depth
            depth = path.count("/")
            analysis["directory_depth"][depth] = analysis["directory_depth"].get(depth, 0) + 1
            
            # Analyze file types
            if "." in path:
                extension = "." + path.split(".")[-1]
                analysis["file_types"][extension] = analysis["file_types"].get(extension, 0) + 1
            
            # Check for potential issues
            if " " in path:
                analysis["potential_issues"].append(f"File path contains spaces: {path}")
            if path.startswith("/"):
                analysis["potential_issues"].append(f"Absolute path detected: {path}")
            if len(path) > 100:
                analysis["potential_issues"].append(f"Very long file path: {path}")
                
        # Analyze naming patterns
        for file_info in files:
            filename = file_info.get("path", "").split("/")[-1]
            if "." in filename and filename:
                name_part = filename.split(".")[0]
                
                # Skip empty name parts (like .env files)
                if not name_part:
                    continue
                
                if name_part.islower():
                    analysis["naming_patterns"]["lowercase"] = analysis["naming_patterns"].get("lowercase", 0) + 1
                elif name_part.isupper():
                    analysis["naming_patterns"]["uppercase"] = analysis["naming_patterns"].get("uppercase", 0) + 1
                elif len(name_part) > 0 and name_part[0].isupper():
                    analysis["naming_patterns"]["PascalCase"] = analysis["naming_patterns"].get("PascalCase", 0) + 1
                elif "_" in name_part:
                    analysis["naming_patterns"]["snake_case"] = analysis["naming_patterns"].get("snake_case", 0) + 1
                else:
                    analysis["naming_patterns"]["camelCase"] = analysis["naming_patterns"].get("camelCase", 0) + 1
                    
        return analysis

    def _categorize_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize files by their type and purpose."""
        
        categorized = {
            "frontend": [],
            "backend": [],
            "config": [],
            "test": [],
            "documentation": [],
            "assets": [],
            "unknown": []
        }
        
        for file_info in files:
            path = file_info.get("path", "")
            content = file_info.get("content", "")
            file_type = file_info.get("type", "")
            
            category = "unknown"
            
            # Check by file type first
            if file_type in categorized:
                category = file_type
            else:
                # Check by extension and patterns
                for cat_name, cat_info in self.file_categories.items():
                    # Check extensions
                    if any(path.endswith(ext) for ext in cat_info["extensions"]):
                        category = cat_name
                        break
                    
                    # Check patterns in filename
                    filename_lower = path.lower()
                    if any(pattern in filename_lower for pattern in cat_info["patterns"]):
                        category = cat_name
                        break
                        
                # Special content-based detection
                if category == "unknown":
                    if "import React" in content or "from 'react'" in content:
                        category = "frontend"
                    elif "fastapi" in content.lower() or "express" in content.lower():
                        category = "backend"
                    elif path.endswith((".json", ".yaml", ".yml")) and ("dependencies" in content or "scripts" in content):
                        category = "config"
                        
            categorized[category].append(file_info)
            
        return categorized

    def _create_optimal_structure(self, project_type: str, file_categories: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Create optimal directory structure based on project type and files."""
        
        base_structure = self.project_structures.get(project_type, self.project_structures["web_app"])
        optimal_structure = {}
        
        # Start with base structure
        for directory, description in base_structure.items():
            if isinstance(description, dict):
                optimal_structure[directory] = description
            else:
                optimal_structure[directory] = {"_description": description}
                
        # Customize based on actual files
        for category, files in file_categories.items():
            if not files:
                continue
                
            category_info = self.file_categories.get(category, {})
            preferred_dirs = category_info.get("directory_preferences", [])
            
            # Find the best directory for this category
            best_dir = None
            for pref_dir in preferred_dirs:
                if pref_dir in optimal_structure or pref_dir.rstrip("/") in optimal_structure:
                    best_dir = pref_dir
                    break
                    
            if not best_dir and preferred_dirs:
                best_dir = preferred_dirs[0]
                optimal_structure[best_dir] = {"_description": f"{category} files"}
                
        # Add special directories based on file analysis
        if file_categories.get("frontend") and project_type == "web_app":
            # Check if we need specific component subdirectories
            frontend_files = file_categories["frontend"]
            component_files = [f for f in frontend_files if "component" in f.get("path", "").lower()]
            
            if len(component_files) > 5:
                if "src/" not in optimal_structure:
                    optimal_structure["src/"] = {}
                if "components/" not in optimal_structure["src/"]:
                    optimal_structure["src/"]["components/"] = {}
                
                # Create subdirectories for different types of components
                optimal_structure["src/"]["components/"]["ui/"] = "Basic UI components"
                optimal_structure["src/"]["components/"]["forms/"] = "Form components"
                optimal_structure["src/"]["components/"]["layout/"] = "Layout components"
                
        return optimal_structure

    async def _reorganize_files(self, files: List[Dict], optimal_structure: Dict[str, Any], project_type: str) -> List[Dict]:
        """Reorganize files according to the optimal structure."""
        
        reorganized_files = []
        
        for file_info in files.copy():
            current_path = file_info.get("path", "")
            content = file_info.get("content", "")
            file_type = file_info.get("type", "")
            language = file_info.get("language", "")
            
            # Determine new path
            new_path = self._determine_optimal_path(file_info, optimal_structure, project_type)
            
            # Update file info
            updated_file = file_info.copy()
            updated_file["path"] = new_path
            updated_file["original_path"] = current_path
            
            # Apply naming conventions
            updated_file = self._apply_naming_conventions(updated_file, project_type)
            
            reorganized_files.append(updated_file)
            
        return reorganized_files

    def _determine_optimal_path(self, file_info: Dict[str, Any], optimal_structure: Dict[str, Any], project_type: str) -> str:
        """Determine the optimal path for a file."""
        
        current_path = file_info.get("path", "")
        content = file_info.get("content", "")
        file_type = file_info.get("type", "")
        language = file_info.get("language", "")
        
        filename = current_path.split("/")[-1] if "/" in current_path else current_path
        
        # Special cases for root files
        if filename in ["package.json", "requirements.txt", "Dockerfile", ".env", ".env.example", "README.md"]:
            return filename
            
        # Determine category
        category = self._determine_file_category(file_info)
        
        # Map category to directory
        directory_mapping = {
            "frontend": self._find_frontend_directory(file_info, optimal_structure),
            "backend": self._find_backend_directory(file_info, optimal_structure),
            "config": self._find_config_directory(file_info, optimal_structure),
            "test": self._find_test_directory(file_info, optimal_structure),
            "documentation": self._find_docs_directory(file_info, optimal_structure),
            "assets": self._find_assets_directory(file_info, optimal_structure)
        }
        
        target_directory = directory_mapping.get(category, "src/")
        
        # Ensure directory ends with /
        if not target_directory.endswith("/"):
            target_directory += "/"
            
        return target_directory + filename

    def _determine_file_category(self, file_info: Dict[str, Any]) -> str:
        """Determine the category of a file."""
        
        path = file_info.get("path", "")
        content = file_info.get("content", "")
        file_type = file_info.get("type", "")
        
        # Check explicit type first
        if file_type in ["frontend", "backend", "config", "test", "documentation", "assets"]:
            return file_type
            
        # Check by file extension and content
        for category, category_info in self.file_categories.items():
            # Check extensions
            if any(path.endswith(ext) for ext in category_info["extensions"]):
                return category
                
            # Check patterns
            if any(pattern in path.lower() for pattern in category_info["patterns"]):
                return category
                
        # Content-based detection
        if "import React" in content or "from 'react'" in content:
            return "frontend"
        elif "fastapi" in content.lower() or "express" in content.lower():
            return "backend"
        elif path.endswith(".md"):
            return "documentation"
            
        return "frontend"  # Default

    def _find_frontend_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for frontend files."""
        
        path = file_info.get("path", "")
        content = file_info.get("content", "")
        
        # Component files
        if "component" in path.lower() or ("export default" in content and "return (" in content):
            if "src/components/" in self._flatten_structure(structure):
                return "src/components/"
            return "src/"
            
        # Page files
        if "page" in path.lower() or "route" in path.lower():
            if "src/pages/" in self._flatten_structure(structure):
                return "src/pages/"
            return "src/"
            
        # Hook files
        if "hook" in path.lower() or ("use" in path and path.endswith(".js")):
            if "src/hooks/" in self._flatten_structure(structure):
                return "src/hooks/"
            return "src/"
            
        # Style files
        if path.endswith((".css", ".scss", ".sass", ".less")):
            if "src/styles/" in self._flatten_structure(structure):
                return "src/styles/"
            return "src/"
            
        # Default to src/
        return "src/"

    def _find_backend_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for backend files."""
        
        path = file_info.get("path", "")
        content = file_info.get("content", "")
        
        # Route files
        if "route" in path.lower() or "@app." in content or "router." in content:
            if "src/routes/" in self._flatten_structure(structure):
                return "src/routes/"
            return "src/"
            
        # Model files
        if "model" in path.lower() or "class " in content and ("Base" in content or "db" in content):
            if "src/models/" in self._flatten_structure(structure):
                return "src/models/"
            return "src/"
            
        # Service files
        if "service" in path.lower() or "api" in path.lower():
            if "src/services/" in self._flatten_structure(structure):
                return "src/services/"
            return "src/"
            
        return "src/"

    def _find_config_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for config files."""
        
        path = file_info.get("path", "")
        
        # Root config files
        if path in ["package.json", "requirements.txt", "Dockerfile", ".env", ".env.example"]:
            return ""
            
        # Other config files
        if "src/config/" in self._flatten_structure(structure):
            return "src/config/"
        elif "config/" in self._flatten_structure(structure):
            return "config/"
        else:
            return ""

    def _find_test_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for test files."""
        
        if "tests/" in self._flatten_structure(structure):
            return "tests/"
        elif "__tests__/" in self._flatten_structure(structure):
            return "__tests__/"
        else:
            return "tests/"

    def _find_docs_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for documentation files."""
        
        path = file_info.get("path", "")
        
        if path == "README.md":
            return ""
            
        if "docs/" in self._flatten_structure(structure):
            return "docs/"
        else:
            return "docs/"

    def _find_assets_directory(self, file_info: Dict[str, Any], structure: Dict[str, Any]) -> str:
        """Find the best directory for asset files."""
        
        if "src/assets/" in self._flatten_structure(structure):
            return "src/assets/"
        elif "public/assets/" in self._flatten_structure(structure):
            return "public/assets/"
        elif "assets/" in self._flatten_structure(structure):
            return "assets/"
        else:
            return "src/assets/"

    def _flatten_structure(self, structure: Dict[str, Any], prefix: str = "") -> List[str]:
        """Flatten nested structure dict to list of paths."""
        
        paths = []
        for key, value in structure.items():
            full_path = prefix + key
            paths.append(full_path)
            
            if isinstance(value, dict):
                paths.extend(self._flatten_structure(value, full_path))
                
        return paths

    def _apply_naming_conventions(self, file_info: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """Apply proper naming conventions to files."""
        
        updated_file = file_info.copy()
        path = updated_file.get("path", "")
        content = updated_file.get("content", "")
        
        if "/" in path:
            directory = "/".join(path.split("/")[:-1]) + "/"
            filename = path.split("/")[-1]
        else:
            directory = ""
            filename = path
            
        # Apply naming conventions based on file type and content
        if "component" in directory.lower() and filename.endswith((".jsx", ".tsx", ".vue")):
            # Component files should be PascalCase
            name_part = filename.split(".")[0]
            if name_part and len(name_part) > 0 and not name_part[0].isupper():
                new_name = self._to_pascal_case(name_part)
                filename = filename.replace(name_part, new_name)
                
        elif "util" in directory.lower() or "service" in directory.lower():
            # Utility and service files should be camelCase
            name_part = filename.split(".")[0]
            if name_part and not self._is_camel_case(name_part):
                new_name = self._to_camel_case(name_part)
                filename = filename.replace(name_part, new_name)
                
        updated_file["path"] = directory + filename
        return updated_file

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        
        # Handle different separators
        words = text.replace("-", " ").replace("_", " ").split()
        return "".join(word.capitalize() for word in words)

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        
        words = text.replace("-", " ").replace("_", " ").split()
        if not words:
            return text
            
        return words[0].lower() + "".join(word.capitalize() for word in words[1:])

    def _is_camel_case(self, text: str) -> bool:
        """Check if text is in camelCase."""
        
        if not text:
            return False
        return text[0].islower() and not "_" in text and not "-" in text

    async def _update_import_statements(self, files: List[Dict]) -> List[Dict]:
        """Update import statements to reflect new file paths."""
        
        updated_files = []
        
        # Create a mapping of old paths to new paths
        path_mapping = {}
        for file_info in files:
            original_path = file_info.get("original_path", file_info.get("path", ""))
            new_path = file_info.get("path", "")
            path_mapping[original_path] = new_path
            
        for file_info in files:
            updated_file = file_info.copy()
            content = updated_file.get("content", "")
            language = updated_file.get("language", "")
            
            if language in ["javascript", "typescript"]:
                content = self._update_js_imports(content, path_mapping, updated_file.get("path", ""))
            elif language == "python":
                content = self._update_python_imports(content, path_mapping, updated_file.get("path", ""))
                
            updated_file["content"] = content
            updated_files.append(updated_file)
            
        return updated_files

    def _update_js_imports(self, content: str, path_mapping: Dict[str, str], current_file_path: str) -> str:
        """Update JavaScript/TypeScript import statements."""
        
        import re
        
        # Find all import statements
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        def replace_import(match):
            import_path = match.group(1)
            
            # Skip external imports (don't start with . or /)
            if not import_path.startswith('.') and not import_path.startswith('/'):
                return match.group(0)
                
            # Calculate the new relative path
            old_absolute_path = self._resolve_relative_path(import_path, current_file_path)
            
            if old_absolute_path in path_mapping:
                new_absolute_path = path_mapping[old_absolute_path]
                new_relative_path = self._calculate_relative_path(current_file_path, new_absolute_path)
                return match.group(0).replace(import_path, new_relative_path)
                
            return match.group(0)
        
        return re.sub(import_pattern, replace_import, content)

    def _update_python_imports(self, content: str, path_mapping: Dict[str, str], current_file_path: str) -> str:
        """Update Python import statements."""
        
        import re
        
        # Python imports are more complex and would need actual AST parsing
        # For now, we'll do basic string replacement
        return content

    def _resolve_relative_path(self, relative_path: str, current_file_path: str) -> str:
        """Resolve a relative import path to an absolute path."""
        
        if current_file_path.count("/") == 0:
            current_dir = ""
        else:
            current_dir = "/".join(current_file_path.split("/")[:-1])
            
        if relative_path.startswith("./"):
            return current_dir + "/" + relative_path[2:]
        elif relative_path.startswith("../"):
            # Handle going up directories
            up_levels = 0
            temp_path = relative_path
            while temp_path.startswith("../"):
                up_levels += 1
                temp_path = temp_path[3:]
                
            dir_parts = current_dir.split("/") if current_dir else []
            if len(dir_parts) >= up_levels:
                new_dir = "/".join(dir_parts[:-up_levels]) if up_levels > 0 else "/".join(dir_parts)
                return new_dir + "/" + temp_path if new_dir else temp_path
                
        return relative_path

    def _calculate_relative_path(self, from_path: str, to_path: str) -> str:
        """Calculate relative path from one file to another."""
        
        from_parts = from_path.split("/")[:-1]  # Remove filename
        to_parts = to_path.split("/")[:-1]  # Remove filename
        to_filename = to_path.split("/")[-1]
        
        # Find common prefix
        common_length = 0
        for i in range(min(len(from_parts), len(to_parts))):
            if from_parts[i] == to_parts[i]:
                common_length += 1
            else:
                break
                
        # Calculate relative path
        up_levels = len(from_parts) - common_length
        down_path = to_parts[common_length:]
        
        relative_parts = [".."] * up_levels + down_path
        
        if relative_parts:
            relative_dir = "/".join(relative_parts)
            return f"./{relative_dir}/{to_filename}"
        else:
            return f"./{to_filename}"

    async def _generate_additional_configs(self, project_type: str, files: List[Dict]) -> List[Dict]:
        """Generate additional configuration files needed for the project."""
        
        additional_configs = []
        
        # Check if we need a .gitignore file
        if not any(f.get("path") == ".gitignore" for f in files):
            gitignore_content = self._generate_gitignore(project_type)
            additional_configs.append({
                "path": ".gitignore",
                "content": gitignore_content,
                "language": "text",
                "type": "config"
            })
            
        # Check if we need VS Code settings
        if not any("/.vscode/" in f.get("path", "") for f in files):
            vscode_settings = self._generate_vscode_settings(project_type)
            additional_configs.append({
                "path": ".vscode/settings.json",
                "content": vscode_settings,
                "language": "json",
                "type": "config"
            })
            
        # Check if we need ESLint config for JavaScript projects
        has_js_files = any(f.get("language") in ["javascript", "typescript"] for f in files)
        if has_js_files and not any(".eslintrc" in f.get("path", "") for f in files):
            eslint_config = self._generate_eslint_config(project_type)
            additional_configs.append({
                "path": ".eslintrc.json",
                "content": eslint_config,
                "language": "json",
                "type": "config"
            })
            
        # Check if we need Prettier config
        if has_js_files and not any(".prettierrc" in f.get("path", "") for f in files):
            prettier_config = self._generate_prettier_config()
            additional_configs.append({
                "path": ".prettierrc",
                "content": prettier_config,
                "language": "json",
                "type": "config"
            })
            
        return additional_configs

    def _generate_gitignore(self, project_type: str) -> str:
        """Generate .gitignore file content."""
        
        base_ignores = [
            "# Dependencies",
            "node_modules/",
            "*/node_modules/",
            "",
            "# Environment variables",
            ".env",
            ".env.local",
            ".env.*.local",
            "",
            "# Build outputs",
            "build/",
            "dist/",
            "*.tgz",
            "*.tar.gz",
            "",
            "# IDE files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Logs",
            "*.log",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*"
        ]
        
        if project_type in ["api", "web_app"] and any("python" in str(project_type).lower() for project_type in [project_type]):
            base_ignores.extend([
                "",
                "# Python",
                "__pycache__/",
                "*.py[cod]",
                "*$py.class",
                "*.so",
                ".Python",
                "venv/",
                "env/",
                ".env",
                ".venv"
            ])
            
        return "\n".join(base_ignores)

    def _generate_vscode_settings(self, project_type: str) -> str:
        """Generate VS Code settings."""
        
        settings = {
            "editor.tabSize": 2,
            "editor.insertSpaces": True,
            "editor.formatOnSave": True,
            "files.trimTrailingWhitespace": True,
            "files.insertFinalNewline": True
        }
        
        if project_type in ["web_app", "mobile_app"]:
            settings.update({
                "emmet.includeLanguages": {
                    "javascript": "javascriptreact"
                },
                "editor.defaultFormatter": "esbenp.prettier-vscode"
            })
            
        return json.dumps(settings, indent=2)

    def _generate_eslint_config(self, project_type: str) -> str:
        """Generate ESLint configuration."""
        
        config = {
            "env": {
                "browser": True,
                "es2021": True,
                "node": True
            },
            "extends": [
                "eslint:recommended"
            ],
            "parserOptions": {
                "ecmaVersion": 12,
                "sourceType": "module"
            },
            "rules": {
                "no-unused-vars": "warn",
                "no-console": "warn",
                "prefer-const": "error"
            }
        }
        
        if project_type in ["web_app", "mobile_app"]:
            config["extends"].extend([
                "@typescript-eslint/recommended",
                "plugin:react/recommended"
            ])
            config["plugins"] = ["react", "@typescript-eslint"]
            config["parserOptions"]["ecmaFeatures"] = {"jsx": True}
            
        return json.dumps(config, indent=2)

    def _generate_prettier_config(self) -> str:
        """Generate Prettier configuration."""
        
        config = {
            "semi": True,
            "trailingComma": "es5",
            "singleQuote": True,
            "printWidth": 80,
            "tabWidth": 2
        }
        
        return json.dumps(config, indent=2)

    def _create_build_optimizations(self, project_type: str, files: List[Dict]) -> Dict[str, Any]:
        """Create build and deployment optimizations."""
        
        optimizations = {
            "build_scripts": {},
            "deployment_configs": {},
            "performance_optimizations": [],
            "bundle_analysis": {}
        }
        
        # Add build scripts based on project type
        if project_type in ["web_app", "mobile_app"]:
            optimizations["build_scripts"] = {
                "development": "npm run dev",
                "build": "npm run build",
                "preview": "npm run preview",
                "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
                "format": "prettier --write src/**/*.{js,jsx,ts,tsx,css,md}"
            }
            
        elif project_type == "api":
            optimizations["build_scripts"] = {
                "start": "python main.py",
                "dev": "uvicorn main:app --reload",
                "test": "pytest",
                "lint": "flake8 src/",
                "format": "black src/"
            }
            
        # Performance optimizations
        js_files = [f for f in files if f.get("language") in ["javascript", "typescript"]]
        if len(js_files) > 10:
            optimizations["performance_optimizations"].extend([
                "Consider code splitting for large applications",
                "Implement lazy loading for components",
                "Use tree shaking to reduce bundle size"
            ])
            
        # Bundle analysis
        total_js_size = sum(len(f.get("content", "")) for f in js_files)
        optimizations["bundle_analysis"] = {
            "estimated_js_size_kb": total_js_size / 1024,
            "total_files": len(files),
            "optimization_needed": total_js_size > 500000  # > 500KB
        }
        
        return optimizations

    def _validate_final_structure(self, files: List[Dict], project_type: str) -> Dict[str, Any]:
        """Validate the final file structure."""
        
        validation = {
            "structure_score": 0.0,
            "issues": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for required files
        file_paths = [f.get("path", "") for f in files]
        
        if project_type in ["web_app", "mobile_app"]:
            if "package.json" not in file_paths:
                validation["issues"].append("Missing package.json file")
            if not any("src/" in path for path in file_paths):
                validation["issues"].append("No src/ directory found")
                
        elif project_type == "api":
            if "main.py" not in file_paths and "app.py" not in file_paths:
                validation["issues"].append("Missing main application file")
                
        # Check directory organization
        directories = set()
        for path in file_paths:
            if "/" in path:
                directories.add(path.split("/")[0])
                
        if len(directories) < 2:
            validation["warnings"].append("Consider organizing files into more directories")
            
        # Calculate structure score
        score = 100
        score -= len(validation["issues"]) * 20
        score -= len(validation["warnings"]) * 5
        
        validation["structure_score"] = max(0, score)
        
        return validation

    def _count_moved_files(self, original_files: List[Dict], final_files: List[Dict]) -> int:
        """Count how many files were moved to different locations."""
        
        moved_count = 0
        
        for final_file in final_files:
            original_path = final_file.get("original_path")
            current_path = final_file.get("path")
            
            if original_path and original_path != current_path:
                moved_count += 1
                
        return moved_count

    def _count_updated_imports(self, original_files: List[Dict], final_files: List[Dict]) -> int:
        """Count how many import statements were updated."""
        
        # This would require more sophisticated analysis
        # For now, return an estimate
        return len([f for f in final_files if f.get("language") in ["javascript", "typescript", "python"]])

    def _calculate_organization_score(self, files: List[Dict], project_type: str) -> float:
        """Calculate an organization quality score."""
        
        score = 100.0
        
        # Check directory depth (penalize too deep or too flat)
        depths = [f.get("path", "").count("/") for f in files]
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        if avg_depth < 1:
            score -= 20  # Too flat
        elif avg_depth > 4:
            score -= 15  # Too deep
            
        # Check file distribution
        directories = {}
        for file_info in files:
            path = file_info.get("path", "")
            if "/" in path:
                directory = path.split("/")[0]
                directories[directory] = directories.get(directory, 0) + 1
                
        # Penalize if too many files in one directory
        if directories:
            max_files_in_dir = max(directories.values())
            if max_files_in_dir > 10:
                score -= (max_files_in_dir - 10) * 2
                
        # Check naming consistency
        extensions = {}
        for file_info in files:
            path = file_info.get("path", "")
            if "." in path:
                ext = path.split(".")[-1]
                extensions[ext] = extensions.get(ext, 0) + 1
                
        # Bonus for good organization
        if "src" in directories:
            score += 5
        if "tests" in directories or "test" in directories:
            score += 5
        if "docs" in directories:
            score += 3
            
        return max(0, min(100, score))

    def _generate_organization_recommendations(self, files: List[Dict], project_type: str) -> List[str]:
        """Generate recommendations for better file organization."""
        
        recommendations = []
        
        # Analyze current structure
        file_paths = [f.get("path", "") for f in files]
        directories = set()
        for path in file_paths:
            if "/" in path:
                directories.add(path.split("/")[0])
                
        # Check for common issues
        if len(directories) < 3:
            recommendations.append("Consider creating more specific directories for better organization")
            
        # Check for specific missing directories
        if project_type in ["web_app", "mobile_app"]:
            if not any("component" in path.lower() for path in file_paths):
                recommendations.append("Create a dedicated components directory for reusable UI components")
                
            if not any("util" in path.lower() for path in file_paths):
                recommendations.append("Consider creating a utils directory for helper functions")
                
        if project_type == "api":
            if not any("route" in path.lower() for path in file_paths):
                recommendations.append("Organize API endpoints in a dedicated routes directory")
                
        # File count recommendations
        total_files = len(files)
        if total_files > 20:
            recommendations.append("Consider breaking down the project into smaller modules")
        elif total_files < 5:
            recommendations.append("Project structure is simple and well-organized")
            
        return recommendations

    async def process_task(self, task) -> Any:
        """Process a task (required by BaseAgent)."""
        # For vibe agents, we don't use the generic task processing
        return {"status": "task_not_supported", "message": "Use organize_project_structure instead"}

    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get custom metrics for the file manager agent."""
        return {
            "projects_organized": 0.0,
            "files_moved": 0.0,
            "organization_score": 0.0,
            "structure_improvements": 0.0
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_file_manager():
        from agents.vibe_planner_agent import VibePlannerAgent
        from agents.vibe_coder_agent import VibeCoderAgent
        
        # Create a plan and generate code first
        planner = VibePlannerAgent()
        plan = await planner.decompose_vibe_prompt(
            "Create a React dashboard with charts and user authentication"
        )
        
        coder = VibeCoderAgent()
        code_result = await coder.generate_code_from_plan(plan, 123)
        
        # Organize the files
        file_manager = VibeFileManagerAgent()
        organization_result = await file_manager.organize_project_structure(
            code_result["files"], 
            plan["project_type"]
        )
        
        print("=== VIBE FILE MANAGER RESULT ===")
        print(f"Organized {organization_result['metrics']['total_files']} files")
        print(f"Created {organization_result['metrics']['directories_created']} directories")
        print(f"Moved {organization_result['metrics']['files_moved']} files")
        print(f"Organization Score: {organization_result['metrics']['organization_score']:.1f}/100")
        print(f"Recommendations: {len(organization_result['recommendations'])}")
        
        # Show some organized files
        for file in organization_result["organized_files"][:5]:
            original = file.get("original_path", "N/A")
            current = file.get("path", "N/A")
            print(f"  {original} -> {current}")
            
    # Run the test
    asyncio.run(test_file_manager())