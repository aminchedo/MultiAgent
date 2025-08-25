"""
VibeCriticAgent - Reviews and validates generated code for quality, security, and best practices.

This agent analyzes generated code files and provides comprehensive feedback on:
- Code quality and adherence to best practices
- Security vulnerabilities and concerns
- Performance optimization opportunities
- Architecture and design patterns
- Documentation completeness
"""

import json
import time
import re
import ast
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
import logging

from agents.base_agent import BaseAgent


class VibeCriticAgent(BaseAgent):
    """
    Agent responsible for reviewing and validating generated code.
    
    This agent:
    1. Analyzes code quality and best practices
    2. Identifies security vulnerabilities
    3. Suggests performance improvements
    4. Validates architecture patterns
    5. Checks documentation completeness
    6. Provides actionable feedback and recommendations
    """
    
    def __init__(self, agent_id: str = None, name: str = "VibeCriticAgent"):
        # Initialize capabilities as empty list for BaseAgent
        capabilities = []
        super().__init__("vibe_critic", capabilities)
        self.logger = logging.getLogger(__name__)
        
        # Agent capabilities (stored as simple list for this implementation)
        self.vibe_capabilities = [
            "code_quality_analysis",
            "security_scanning",
            "performance_analysis",
            "architecture_review",
            "documentation_review",
            "best_practices_validation"
        ]
        
        # Quality criteria weights
        self.quality_weights = {
            "code_style": 0.15,
            "security": 0.25,
            "performance": 0.20,
            "maintainability": 0.20,
            "documentation": 0.10,
            "architecture": 0.10
        }
        
        # Language-specific analyzers
        self.language_analyzers = {
            "python": self._analyze_python_code,
            "javascript": self._analyze_javascript_code,
            "typescript": self._analyze_typescript_code,
            "css": self._analyze_css_code,
            "html": self._analyze_html_code,
            "json": self._analyze_json_code,
            "markdown": self._analyze_markdown_code
        }
        
        # Security vulnerability patterns
        self.security_patterns = {
            "python": [
                (r'eval\s*\(', "Dangerous use of eval() function", "high"),
                (r'exec\s*\(', "Dangerous use of exec() function", "high"),
                (r'pickle\.loads?\s*\(', "Unsafe pickle usage", "high"),
                (r'subprocess\.(call|run|Popen).*shell\s*=\s*True', "Shell injection risk", "high"),
                (r'open\s*\([^)]*[\'"]r[\'"]', "File access without proper validation", "medium"),
                (r'random\.random\(\)', "Weak random number generation", "low"),
            ],
            "javascript": [
                (r'eval\s*\(', "Dangerous use of eval()", "high"),
                (r'innerHTML\s*=', "Potential XSS vulnerability", "medium"),
                (r'document\.write\s*\(', "Deprecated and unsafe document.write", "medium"),
                (r'console\.log\s*\(.*password', "Password in console output", "high"),
                (r'\$\{[^}]*\}', "Template literal - check for injection", "low"),
            ],
            "general": [
                (r'password\s*=\s*[\'"][^\'"]{1,}[\'"]', "Hardcoded password", "high"),
                (r'api[_-]?key\s*=\s*[\'"][^\'"]{10,}[\'"]', "Hardcoded API key", "high"),
                (r'secret\s*=\s*[\'"][^\'"]{8,}[\'"]', "Hardcoded secret", "high"),
                (r'TODO|FIXME|HACK', "Code contains TODO/FIXME comments", "low"),
            ]
        }
        
        # Performance anti-patterns
        self.performance_patterns = {
            "python": [
                (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\([^)]+\)\s*\)', "Use enumerate() instead of range(len())", "medium"),
                (r'\+\s*=.*[\'"][^\'"]*[\'"]', "String concatenation in loop", "medium"),
                (r'\.keys\(\)\s*\)', "Unnecessary .keys() call", "low"),
            ],
            "javascript": [
                (r'for\s*\(\s*var\s+\w+\s*=\s*0.*\.length', "Consider using forEach() or for...of", "low"),
                (r'document\.getElementById.*document\.getElementById', "Multiple DOM queries", "medium"),
                (r'\.innerHTML\s*\+=', "Inefficient DOM manipulation", "medium"),
            ]
        }
        
        # Best practices patterns
        self.best_practices = {
            "python": [
                ("import statements", r'^import\s+\w+$|^from\s+\w+\s+import', "✓"),
                ("function docstrings", r'def\s+\w+.*:\s*"""', "✓"),
                ("class docstrings", r'class\s+\w+.*:\s*"""', "✓"),
                ("type hints", r'def\s+\w+\([^)]*:\s*\w+', "✓"),
            ],
            "javascript": [
                ("const/let usage", r'\b(const|let)\s+\w+', "✓"),
                ("arrow functions", r'\w+\s*=\s*\([^)]*\)\s*=>', "✓"),
                ("template literals", r'`[^`]*\$\{[^}]+\}[^`]*`', "✓"),
            ]
        }

    async def review_generated_code(self, files: List[Dict], plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to review generated code files.
        
        Args:
            files: List of generated code files with content
            plan: Original development plan for context
            
        Returns:
            Comprehensive review report with scores and recommendations
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting code review for {len(files)} files")
            
            # Initialize review results
            review_results = {
                "overall_score": 0.0,
                "category_scores": {},
                "file_reviews": [],
                "recommendations": [],
                "security_issues": [],
                "performance_issues": [],
                "architecture_feedback": {},
                "summary": {}
            }
            
            # Step 1: Analyze individual files
            file_scores = []
            for file_info in files:
                file_review = await self._analyze_file(file_info, plan)
                review_results["file_reviews"].append(file_review)
                
                if file_review.get("score") is not None:
                    file_scores.append(file_review["score"])
                    
                # Collect issues
                review_results["security_issues"].extend(file_review.get("security_issues", []))
                review_results["performance_issues"].extend(file_review.get("performance_issues", []))
            
            # Step 2: Analyze overall architecture
            architecture_review = await self._analyze_architecture(files, plan)
            review_results["architecture_feedback"] = architecture_review
            
            # Step 3: Calculate category scores
            category_scores = self._calculate_category_scores(review_results["file_reviews"])
            review_results["category_scores"] = category_scores
            
            # Step 4: Calculate overall score
            overall_score = self._calculate_overall_score(category_scores)
            review_results["overall_score"] = overall_score
            
            # Step 5: Generate recommendations
            recommendations = self._generate_recommendations(review_results, plan)
            review_results["recommendations"] = recommendations
            
            # Step 6: Create summary
            summary = self._create_review_summary(review_results, files)
            review_results["summary"] = summary
            
            # Add metadata
            review_results["metadata"] = {
                "critic_agent_id": self.agent_id,
                "review_timestamp": datetime.utcnow().isoformat(),
                "processing_time": time.time() - start_time,
                "files_reviewed": len(files),
                "plan_reference": plan.get("metadata", {}).get("planner_agent_id", "unknown")
            }
            
            self.logger.info(f"Code review completed in {time.time() - start_time:.2f}s with score {overall_score:.1f}/100")
            return review_results
            
        except Exception as e:
            self.logger.error(f"Error in code review: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "metadata": {
                    "critic_agent_id": self.agent_id,
                    "error_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time
                }
            }

    async def _analyze_file(self, file_info: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single file for quality, security, and best practices."""
        
        file_path = file_info.get("path", "unknown")
        content = file_info.get("content", "")
        language = file_info.get("language", "").lower()
        
        self.logger.debug(f"Analyzing file: {file_path} ({language})")
        
        file_review = {
            "path": file_path,
            "language": language,
            "size_bytes": len(content),
            "lines_of_code": len(content.split('\n')),
            "quality_checks": {},
            "security_issues": [],
            "performance_issues": [],
            "best_practices": {},
            "suggestions": [],
            "score": 0.0
        }
        
        if not content.strip():
            file_review["score"] = 0.0
            file_review["suggestions"].append("File is empty")
            return file_review
        
        # Language-specific analysis
        if language in self.language_analyzers:
            lang_analysis = await self.language_analyzers[language](content, file_path)
            file_review.update(lang_analysis)
        
        # Security analysis
        security_issues = self._analyze_security(content, language)
        file_review["security_issues"] = security_issues
        
        # Performance analysis
        performance_issues = self._analyze_performance(content, language)
        file_review["performance_issues"] = performance_issues
        
        # Best practices check
        best_practices = self._check_best_practices(content, language)
        file_review["best_practices"] = best_practices
        
        # Calculate file score
        file_score = self._calculate_file_score(file_review)
        file_review["score"] = file_score
        
        return file_review

    async def _analyze_python_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Python code specifically."""
        
        analysis = {
            "syntax_valid": True,
            "complexity_score": 0,
            "import_analysis": {},
            "function_analysis": {},
            "class_analysis": {}
        }
        
        try:
            # Parse AST to validate syntax
            tree = ast.parse(content)
            analysis["syntax_valid"] = True
            
            # Analyze imports
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            analysis["import_analysis"] = {
                "total_imports": len(imports),
                "has_unused_imports": False,  # Simplified
                "has_wildcard_imports": any("*" in ast.unparse(imp) for imp in imports if hasattr(ast, 'unparse'))
            }
            
            # Analyze functions
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            analysis["function_analysis"] = {
                "total_functions": len(functions),
                "functions_with_docstrings": sum(1 for f in functions if ast.get_docstring(f)),
                "average_function_length": sum(len(ast.unparse(f).split('\n')) for f in functions) / max(len(functions), 1) if hasattr(ast, 'unparse') else 0
            }
            
            # Analyze classes
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            analysis["class_analysis"] = {
                "total_classes": len(classes),
                "classes_with_docstrings": sum(1 for c in classes if ast.get_docstring(c))
            }
            
            # Calculate complexity (simplified McCabe complexity)
            complexity = self._calculate_python_complexity(tree)
            analysis["complexity_score"] = complexity
            
        except SyntaxError as e:
            analysis["syntax_valid"] = False
            analysis["syntax_error"] = str(e)
        except Exception as e:
            analysis["analysis_error"] = str(e)
            
        return analysis

    async def _analyze_javascript_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze JavaScript/JSX code."""
        
        analysis = {
            "has_jsx": "jsx" in file_path.lower() or "tsx" in file_path.lower(),
            "has_react_imports": "import React" in content or "from 'react'" in content,
            "has_export": "export" in content,
            "has_default_export": "export default" in content,
            "function_count": len(re.findall(r'function\s+\w+|const\s+\w+\s*=.*=>', content)),
            "arrow_function_count": len(re.findall(r'=>', content)),
            "console_statements": len(re.findall(r'console\.(log|warn|error)', content))
        }
        
        # JSX specific checks
        if analysis["has_jsx"]:
            analysis["jsx_components"] = len(re.findall(r'<[A-Z]\w*', content))
            analysis["proper_jsx_structure"] = "return (" in content
            
        return analysis

    async def _analyze_typescript_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze TypeScript code."""
        
        # Use JavaScript analyzer as base
        analysis = await self._analyze_javascript_code(content, file_path)
        
        # Add TypeScript-specific checks
        analysis.update({
            "has_type_annotations": bool(re.search(r':\s*\w+(\[\])?', content)),
            "has_interfaces": "interface " in content,
            "has_generics": bool(re.search(r'<[A-Z]\w*>', content)),
            "has_strict_types": "// @ts-strict" in content or "strict" in content
        })
        
        return analysis

    async def _analyze_css_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze CSS code."""
        
        analysis = {
            "selector_count": len(re.findall(r'\{[^}]*\}', content)),
            "has_media_queries": "@media" in content,
            "has_animations": "@keyframes" in content or "animation:" in content,
            "has_flexbox": "display: flex" in content or "display:flex" in content,
            "has_grid": "display: grid" in content or "display:grid" in content,
            "color_count": len(re.findall(r'#[0-9a-fA-F]{3,6}|rgb\(|rgba\(|hsl\(', content)),
            "uses_variables": "--" in content or "var(" in content
        }
        
        return analysis

    async def _analyze_html_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze HTML code."""
        
        analysis = {
            "has_doctype": "<!DOCTYPE" in content,
            "has_html_tag": "<html" in content,
            "has_head_tag": "<head" in content,
            "has_body_tag": "<body" in content,
            "has_meta_viewport": "viewport" in content,
            "has_title": "<title" in content,
            "semantic_tags": len(re.findall(r'<(header|nav|main|section|article|aside|footer)', content)),
            "img_with_alt": len(re.findall(r'<img[^>]*alt=', content)),
            "total_images": len(re.findall(r'<img', content))
        }
        
        return analysis

    async def _analyze_json_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze JSON files."""
        
        analysis = {
            "valid_json": True,
            "size_kb": len(content) / 1024,
            "key_count": 0
        }
        
        try:
            data = json.loads(content)
            analysis["valid_json"] = True
            if isinstance(data, dict):
                analysis["key_count"] = len(data.keys())
                analysis["nested_levels"] = self._calculate_json_depth(data)
        except json.JSONDecodeError:
            analysis["valid_json"] = False
            
        return analysis

    async def _analyze_markdown_code(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Markdown documentation."""
        
        analysis = {
            "has_title": bool(re.search(r'^#\s+', content, re.MULTILINE)),
            "header_count": len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            "has_code_blocks": "```" in content,
            "has_links": "[" in content and "](" in content,
            "has_lists": bool(re.search(r'^[-*+]\s+', content, re.MULTILINE)),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n'))
        }
        
        return analysis

    def _analyze_security(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code for security vulnerabilities."""
        
        security_issues = []
        
        # Check language-specific patterns
        patterns = self.security_patterns.get(language, [])
        patterns.extend(self.security_patterns.get("general", []))
        
        for pattern, description, severity in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                security_issues.append({
                    "type": "security",
                    "severity": severity,
                    "description": description,
                    "line": line_number,
                    "pattern": pattern,
                    "matched_text": match.group()
                })
                
        return security_issues

    def _analyze_performance(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze code for performance issues."""
        
        performance_issues = []
        
        patterns = self.performance_patterns.get(language, [])
        
        for pattern, description, severity in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                performance_issues.append({
                    "type": "performance",
                    "severity": severity,
                    "description": description,
                    "line": line_number,
                    "suggestion": description,
                    "matched_text": match.group()
                })
                
        return performance_issues

    def _check_best_practices(self, content: str, language: str) -> Dict[str, Any]:
        """Check adherence to best practices."""
        
        best_practices = {
            "followed": [],
            "missing": [],
            "score": 0.0
        }
        
        practices = self.best_practices.get(language, [])
        
        for practice_name, pattern, indicator in practices:
            if re.search(pattern, content):
                best_practices["followed"].append(practice_name)
            else:
                best_practices["missing"].append(practice_name)
                
        # Calculate score
        total_practices = len(practices)
        if total_practices > 0:
            best_practices["score"] = len(best_practices["followed"]) / total_practices * 100
            
        return best_practices

    async def _analyze_architecture(self, files: List[Dict], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall project architecture."""
        
        architecture_analysis = {
            "file_organization": {},
            "dependency_structure": {},
            "design_patterns": [],
            "modularity_score": 0.0,
            "separation_of_concerns": {},
            "recommendations": []
        }
        
        # Analyze file organization
        file_paths = [f.get("path", "") for f in files]
        architecture_analysis["file_organization"] = self._analyze_file_organization(file_paths)
        
        # Analyze dependency structure
        architecture_analysis["dependency_structure"] = self._analyze_dependencies(files)
        
        # Check design patterns
        architecture_analysis["design_patterns"] = self._identify_design_patterns(files)
        
        # Calculate modularity score
        architecture_analysis["modularity_score"] = self._calculate_modularity_score(files)
        
        # Analyze separation of concerns
        architecture_analysis["separation_of_concerns"] = self._analyze_separation_of_concerns(files, plan)
        
        # Generate architecture recommendations
        architecture_analysis["recommendations"] = self._generate_architecture_recommendations(
            architecture_analysis, plan
        )
        
        return architecture_analysis

    def _analyze_file_organization(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze how files are organized in the project."""
        
        organization = {
            "total_files": len(file_paths),
            "directories": set(),
            "file_types": {},
            "depth_distribution": {},
            "naming_consistency": True
        }
        
        for path in file_paths:
            # Extract directory
            if "/" in path:
                directory = "/".join(path.split("/")[:-1])
                organization["directories"].add(directory)
            
            # Extract file type
            if "." in path:
                extension = path.split(".")[-1]
                organization["file_types"][extension] = organization["file_types"].get(extension, 0) + 1
            
            # Calculate depth
            depth = path.count("/")
            organization["depth_distribution"][depth] = organization["depth_distribution"].get(depth, 0) + 1
        
        organization["directories"] = list(organization["directories"])
        
        return organization

    def _analyze_dependencies(self, files: List[Dict]) -> Dict[str, Any]:
        """Analyze dependency structure between files."""
        
        dependencies = {
            "import_map": {},
            "circular_dependencies": [],
            "unused_imports": [],
            "external_dependencies": set()
        }
        
        for file_info in files:
            content = file_info.get("content", "")
            file_path = file_info.get("path", "")
            language = file_info.get("language", "")
            
            if language in ["javascript", "typescript"]:
                # Extract imports
                imports = re.findall(r'import.*from\s+[\'"]([^\'"]+)[\'"]', content)
                dependencies["import_map"][file_path] = imports
                
                # Identify external dependencies
                for imp in imports:
                    if not imp.startswith("."):
                        dependencies["external_dependencies"].add(imp)
                        
            elif language == "python":
                # Extract Python imports
                imports = re.findall(r'from\s+([^\s]+)\s+import|import\s+([^\s]+)', content)
                flat_imports = [imp[0] or imp[1] for imp in imports]
                dependencies["import_map"][file_path] = flat_imports
                
                # Identify external dependencies
                for imp in flat_imports:
                    if not imp.startswith("."):
                        dependencies["external_dependencies"].add(imp)
        
        dependencies["external_dependencies"] = list(dependencies["external_dependencies"])
        
        return dependencies

    def _identify_design_patterns(self, files: List[Dict]) -> List[str]:
        """Identify design patterns used in the code."""
        
        patterns = []
        all_content = " ".join(f.get("content", "") for f in files)
        
        # Pattern indicators
        pattern_indicators = {
            "MVC": ["controller", "model", "view"],
            "Factory": ["factory", "create"],
            "Observer": ["observer", "subscribe", "publish"],
            "Singleton": ["singleton", "instance"],
            "Component": ["component", "props", "render"],
            "HOC": ["withComponent", "hoc", "HigherOrder"],
            "Custom Hooks": ["use[A-Z]\\w+", "hook"],
            "Context API": ["createContext", "useContext", "Provider"]
        }
        
        for pattern_name, indicators in pattern_indicators.items():
            if any(re.search(indicator, all_content, re.IGNORECASE) for indicator in indicators):
                patterns.append(pattern_name)
                
        return patterns

    def _calculate_modularity_score(self, files: List[Dict]) -> float:
        """Calculate a modularity score based on file structure and dependencies."""
        
        if not files:
            return 0.0
        
        # Factors for modularity
        factors = {
            "file_separation": 0,
            "single_responsibility": 0,
            "low_coupling": 0,
            "high_cohesion": 0
        }
        
        # File separation (different types in different directories)
        file_types = {}
        for file_info in files:
            path = file_info.get("path", "")
            file_type = file_info.get("type", "unknown")
            
            if "/" in path:
                directory = path.split("/")[0]
                if directory not in file_types:
                    file_types[directory] = set()
                file_types[directory].add(file_type)
        
        # Calculate separation score
        if file_types:
            avg_types_per_dir = sum(len(types) for types in file_types.values()) / len(file_types)
            factors["file_separation"] = max(0, (2 - avg_types_per_dir) / 2) * 100
        
        # Single responsibility (smaller files are generally better)
        avg_file_size = sum(len(f.get("content", "").split('\n')) for f in files) / len(files)
        factors["single_responsibility"] = max(0, (200 - avg_file_size) / 200) * 100
        
        # Default values for coupling and cohesion (would need more complex analysis)
        factors["low_coupling"] = 75  # Assume good coupling for generated code
        factors["high_cohesion"] = 75  # Assume good cohesion for generated code
        
        # Calculate weighted average
        modularity_score = sum(factors.values()) / len(factors)
        return min(100, max(0, modularity_score))

    def _analyze_separation_of_concerns(self, files: List[Dict], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well concerns are separated."""
        
        separation = {
            "frontend_backend_separation": True,
            "data_logic_separation": True,
            "style_logic_separation": True,
            "config_code_separation": True,
            "concerns_identified": []
        }
        
        file_types = [f.get("type", "") for f in files]
        
        # Check if frontend and backend are properly separated
        has_frontend = any("frontend" in t for t in file_types)
        has_backend = any("backend" in t for t in file_types)
        
        if has_frontend and has_backend:
            # Look for mixed concerns in files
            for file_info in files:
                content = file_info.get("content", "")
                if file_info.get("type") == "frontend" and ("database" in content.lower() or "sql" in content.lower()):
                    separation["frontend_backend_separation"] = False
                    
        # Identify concerns
        for file_info in files:
            path = file_info.get("path", "")
            if "component" in path.lower():
                separation["concerns_identified"].append("UI Components")
            elif "api" in path.lower() or "route" in path.lower():
                separation["concerns_identified"].append("API Logic")
            elif "model" in path.lower() or "schema" in path.lower():
                separation["concerns_identified"].append("Data Models")
            elif "config" in path.lower() or ".env" in path:
                separation["concerns_identified"].append("Configuration")
                
        separation["concerns_identified"] = list(set(separation["concerns_identified"]))
        
        return separation

    def _calculate_python_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python code."""
        
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
                
        return complexity

    def _calculate_json_depth(self, data: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of JSON data."""
        
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(self._calculate_json_depth(value, current_depth + 1) for value in data.values())
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(self._calculate_json_depth(item, current_depth + 1) for item in data)
        else:
            return current_depth

    def _calculate_file_score(self, file_review: Dict[str, Any]) -> float:
        """Calculate a quality score for a single file."""
        
        score = 100.0  # Start with perfect score
        
        # Deduct for security issues
        for issue in file_review.get("security_issues", []):
            severity = issue.get("severity", "low")
            if severity == "high":
                score -= 20
            elif severity == "medium":
                score -= 10
            elif severity == "low":
                score -= 5
                
        # Deduct for performance issues
        for issue in file_review.get("performance_issues", []):
            severity = issue.get("severity", "low")
            if severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 8
            elif severity == "low":
                score -= 3
                
        # Adjust for best practices
        best_practices = file_review.get("best_practices", {})
        bp_score = best_practices.get("score", 100)
        score = score * (bp_score / 100)
        
        # Bonus for language-specific good practices
        language = file_review.get("language", "")
        if language == "python":
            if file_review.get("syntax_valid", False):
                score += 5
            else:
                score -= 30
                
        elif language in ["javascript", "typescript"]:
            if file_review.get("has_export", False):
                score += 2
            if file_review.get("has_jsx", False) and file_review.get("has_react_imports", False):
                score += 3
                
        return max(0, min(100, score))

    def _calculate_category_scores(self, file_reviews: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate scores for different quality categories."""
        
        categories = {
            "code_style": 0.0,
            "security": 0.0,
            "performance": 0.0,
            "maintainability": 0.0,
            "documentation": 0.0,
            "architecture": 0.0
        }
        
        if not file_reviews:
            return categories
        
        # Security score
        total_security_issues = sum(len(review.get("security_issues", [])) for review in file_reviews)
        total_files = len(file_reviews)
        categories["security"] = max(0, 100 - (total_security_issues * 10))
        
        # Performance score
        total_performance_issues = sum(len(review.get("performance_issues", [])) for review in file_reviews)
        categories["performance"] = max(0, 100 - (total_performance_issues * 5))
        
        # Code style score (average of best practices scores)
        style_scores = [review.get("best_practices", {}).get("score", 0) for review in file_reviews]
        categories["code_style"] = sum(style_scores) / len(style_scores) if style_scores else 0
        
        # Maintainability (based on complexity and structure)
        complexity_scores = []
        for review in file_reviews:
            if review.get("language") == "python":
                complexity = review.get("complexity_score", 1)
                # Lower complexity = higher maintainability
                complexity_scores.append(max(0, 100 - complexity * 5))
            else:
                complexity_scores.append(80)  # Default for non-Python files
        categories["maintainability"] = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 80
        
        # Documentation score
        doc_scores = []
        for review in file_reviews:
            if review.get("language") == "python":
                func_analysis = review.get("function_analysis", {})
                total_funcs = func_analysis.get("total_functions", 0)
                documented_funcs = func_analysis.get("functions_with_docstrings", 0)
                if total_funcs > 0:
                    doc_scores.append((documented_funcs / total_funcs) * 100)
                else:
                    doc_scores.append(100)  # No functions to document
            elif review.get("path", "").endswith(".md"):
                doc_scores.append(100)  # Documentation files get full score
            else:
                doc_scores.append(70)  # Default for other files
        categories["documentation"] = sum(doc_scores) / len(doc_scores) if doc_scores else 70
        
        # Architecture score (simplified)
        categories["architecture"] = 85  # Default good score for generated code
        
        return categories

    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall quality score using weighted categories."""
        
        total_score = 0.0
        for category, score in category_scores.items():
            weight = self.quality_weights.get(category, 0.1)
            total_score += score * weight
            
        return min(100, max(0, total_score))

    def _generate_recommendations(self, review_results: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on review results."""
        
        recommendations = []
        
        # Security recommendations
        security_issues = review_results.get("security_issues", [])
        high_security_issues = [issue for issue in security_issues if issue.get("severity") == "high"]
        
        if high_security_issues:
            recommendations.append({
                "category": "security",
                "priority": "high",
                "title": "Address Critical Security Issues",
                "description": f"Found {len(high_security_issues)} high-severity security issues that need immediate attention.",
                "details": [issue["description"] for issue in high_security_issues[:3]],
                "estimated_effort": "1-2 hours"
            })
            
        # Performance recommendations
        performance_issues = review_results.get("performance_issues", [])
        if len(performance_issues) > 5:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "title": "Optimize Performance",
                "description": f"Found {len(performance_issues)} performance optimization opportunities.",
                "details": [issue["description"] for issue in performance_issues[:3]],
                "estimated_effort": "2-4 hours"
            })
            
        # Code quality recommendations
        category_scores = review_results.get("category_scores", {})
        
        if category_scores.get("code_style", 100) < 70:
            recommendations.append({
                "category": "code_style",
                "priority": "medium",
                "title": "Improve Code Style",
                "description": "Code style score is below recommended threshold.",
                "details": ["Add missing type hints", "Follow naming conventions", "Improve code formatting"],
                "estimated_effort": "1-3 hours"
            })
            
        if category_scores.get("documentation", 100) < 60:
            recommendations.append({
                "category": "documentation",
                "priority": "medium",
                "title": "Improve Documentation",
                "description": "Code lacks sufficient documentation.",
                "details": ["Add function docstrings", "Create API documentation", "Add inline comments"],
                "estimated_effort": "2-4 hours"
            })
            
        # Architecture recommendations
        architecture = review_results.get("architecture_feedback", {})
        modularity_score = architecture.get("modularity_score", 100)
        
        if modularity_score < 70:
            recommendations.append({
                "category": "architecture",
                "priority": "low",
                "title": "Improve Modularity",
                "description": "Code structure could be more modular.",
                "details": ["Break down large files", "Improve separation of concerns", "Reduce coupling"],
                "estimated_effort": "3-6 hours"
            })
            
        # Overall recommendations
        overall_score = review_results.get("overall_score", 0)
        if overall_score >= 90:
            recommendations.append({
                "category": "general",
                "priority": "low",
                "title": "Excellent Code Quality",
                "description": "Code quality is excellent. Consider minor optimizations.",
                "details": ["Code is ready for production", "Minor optimizations possible"],
                "estimated_effort": "0-1 hour"
            })
        elif overall_score >= 70:
            recommendations.append({
                "category": "general",
                "priority": "medium", 
                "title": "Good Code Quality",
                "description": "Code quality is good with room for improvement.",
                "details": ["Address medium-priority issues", "Consider refactoring opportunities"],
                "estimated_effort": "2-4 hours"
            })
        else:
            recommendations.append({
                "category": "general",
                "priority": "high",
                "title": "Code Quality Needs Improvement",
                "description": "Significant improvements needed before production.",
                "details": ["Address all high-priority issues", "Major refactoring recommended"],
                "estimated_effort": "6+ hours"
            })
            
        return recommendations

    def _generate_architecture_recommendations(self, architecture_analysis: Dict[str, Any], plan: Dict[str, Any]) -> List[str]:
        """Generate architecture-specific recommendations."""
        
        recommendations = []
        
        file_org = architecture_analysis.get("file_organization", {})
        dependencies = architecture_analysis.get("dependency_structure", {})
        
        # File organization recommendations
        if len(file_org.get("directories", [])) < 3:
            recommendations.append("Consider organizing files into more specific directories (components, utils, services)")
            
        # Dependency recommendations
        external_deps = dependencies.get("external_dependencies", [])
        if len(external_deps) > 20:
            recommendations.append("Large number of external dependencies may increase bundle size")
            
        # Design pattern recommendations
        patterns = architecture_analysis.get("design_patterns", [])
        project_type = plan.get("project_type", "")
        
        if project_type == "web_app" and "Component" not in patterns:
            recommendations.append("Consider using component-based architecture for better maintainability")
            
        if "authentication" in plan.get("analysis", {}).get("features", []) and "Observer" not in patterns:
            recommendations.append("Consider implementing Observer pattern for user state management")
            
        return recommendations

    def _create_review_summary(self, review_results: Dict[str, Any], files: List[Dict]) -> Dict[str, Any]:
        """Create a summary of the review results."""
        
        summary = {
            "overall_quality": "unknown",
            "readiness_for_production": False,
            "key_strengths": [],
            "critical_issues": [],
            "improvement_areas": [],
            "estimated_fix_time": "unknown"
        }
        
        overall_score = review_results.get("overall_score", 0)
        category_scores = review_results.get("category_scores", {})
        
        # Determine overall quality
        if overall_score >= 90:
            summary["overall_quality"] = "excellent"
            summary["readiness_for_production"] = True
        elif overall_score >= 75:
            summary["overall_quality"] = "good"
            summary["readiness_for_production"] = True
        elif overall_score >= 60:
            summary["overall_quality"] = "fair"
            summary["readiness_for_production"] = False
        else:
            summary["overall_quality"] = "poor"
            summary["readiness_for_production"] = False
            
        # Identify strengths
        for category, score in category_scores.items():
            if score >= 85:
                summary["key_strengths"].append(category.replace("_", " ").title())
                
        # Identify critical issues
        security_issues = review_results.get("security_issues", [])
        critical_security = [issue for issue in security_issues if issue.get("severity") == "high"]
        
        if critical_security:
            summary["critical_issues"].append(f"{len(critical_security)} high-severity security issues")
            
        # Identify improvement areas
        for category, score in category_scores.items():
            if score < 70:
                summary["improvement_areas"].append(category.replace("_", " ").title())
                
        # Estimate fix time
        recommendations = review_results.get("recommendations", [])
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
        
        if high_priority:
            summary["estimated_fix_time"] = "4-8 hours"
        elif medium_priority:
            summary["estimated_fix_time"] = "2-4 hours"
        else:
            summary["estimated_fix_time"] = "0-2 hours"
            
        return summary

    async def process_task(self, task) -> Any:
        """Process a task (required by BaseAgent)."""
        # For vibe agents, we don't use the generic task processing
        return {"status": "task_not_supported", "message": "Use review_generated_code instead"}

    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get custom metrics for the critic agent."""
        return {
            "reviews_completed": 0.0,
            "average_quality_score": 0.0,
            "security_issues_found": 0.0,
            "performance_issues_found": 0.0
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_critic():
        from agents.vibe_planner_agent import VibePlannerAgent
        from agents.vibe_coder_agent import VibeCoderAgent
        
        # Create a plan and generate code first
        planner = VibePlannerAgent()
        plan = await planner.decompose_vibe_prompt(
            "Create a simple React app with authentication"
        )
        
        coder = VibeCoderAgent()
        code_result = await coder.generate_code_from_plan(plan, 123)
        
        # Review the generated code
        critic = VibeCriticAgent()
        review = await critic.review_generated_code(code_result["files"], plan)
        
        print("=== VIBE CRITIC REVIEW ===")
        print(f"Overall Score: {review['overall_score']:.1f}/100")
        print(f"Category Scores: {review['category_scores']}")
        print(f"Security Issues: {len(review['security_issues'])}")
        print(f"Performance Issues: {len(review['performance_issues'])}")
        print(f"Recommendations: {len(review['recommendations'])}")
        print(f"Production Ready: {review['summary']['readiness_for_production']}")
        
    # Run the test
    asyncio.run(test_critic())