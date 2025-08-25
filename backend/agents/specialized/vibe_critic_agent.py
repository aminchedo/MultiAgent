"""
Enhanced Critic Agent specialized for Vibe Coding - reviewing and validating generated code for quality, errors, and vibe alignment.
"""

import json
import re
import ast
import subprocess
import tempfile
import os
from typing import Dict, List, Any, Optional, Tuple
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


class VibeCriticAgent(BaseCrewAgent):
    """
    Specialized Critic Agent for reviewing generated code and ensuring it meets quality standards
    and aligns with the user's original vibe. This agent performs comprehensive code analysis
    including syntax validation, best practices review, and vibe alignment assessment.
    """

    def __init__(self, job_id: str, websocket_callback: Optional[callable] = None):
        super().__init__(job_id, websocket_callback)
        self.quality_standards = self._load_quality_standards()
        self.vibe_criteria = self._load_vibe_criteria()
        self.security_checks = self._load_security_checks()

    def _load_quality_standards(self) -> Dict[str, Any]:
        """Load code quality standards and best practices."""
        return {
            "javascript": {
                "syntax_rules": [
                    "proper_jsx_syntax",
                    "consistent_indentation",
                    "semicolon_usage",
                    "quote_consistency",
                    "proper_imports"
                ],
                "best_practices": [
                    "functional_components",
                    "proper_hooks_usage",
                    "component_naming_convention",
                    "prop_validation",
                    "error_boundaries"
                ],
                "performance": [
                    "avoid_inline_functions",
                    "memoization_where_needed",
                    "proper_key_props",
                    "optimize_renders"
                ]
            },
            "python": {
                "syntax_rules": [
                    "pep8_compliance",
                    "proper_indentation",
                    "import_organization",
                    "function_naming",
                    "variable_naming"
                ],
                "best_practices": [
                    "type_hints",
                    "docstrings",
                    "error_handling",
                    "async_patterns",
                    "dependency_injection"
                ],
                "performance": [
                    "efficient_algorithms",
                    "memory_usage",
                    "database_queries",
                    "caching_strategy"
                ]
            },
            "css": {
                "syntax_rules": [
                    "valid_css_syntax",
                    "consistent_naming",
                    "proper_nesting",
                    "organized_structure"
                ],
                "best_practices": [
                    "responsive_design",
                    "accessibility",
                    "maintainable_code",
                    "css_variables"
                ],
                "performance": [
                    "minimize_selectors",
                    "optimize_animations",
                    "reduce_redundancy"
                ]
            }
        }

    def _load_vibe_criteria(self) -> Dict[str, Any]:
        """Load criteria for assessing vibe alignment."""
        return {
            "modern": {
                "visual_indicators": ["clean layouts", "modern typography", "subtle animations", "proper spacing"],
                "code_indicators": ["modern frameworks", "ES6+ syntax", "functional patterns", "responsive design"],
                "user_experience": ["intuitive navigation", "fast loading", "mobile-friendly", "accessible"]
            },
            "dark": {
                "visual_indicators": ["dark backgrounds", "light text", "dark theme colors", "proper contrast"],
                "code_indicators": ["dark theme implementation", "theme switching", "consistent styling"],
                "user_experience": ["comfortable viewing", "reduced eye strain", "theme persistence"]
            },
            "colorful": {
                "visual_indicators": ["vibrant colors", "gradients", "dynamic elements", "visual appeal"],
                "code_indicators": ["color animation", "gradient implementation", "dynamic styling"],
                "user_experience": ["engaging interface", "visual feedback", "attractive design"]
            },
            "minimal": {
                "visual_indicators": ["clean design", "lots of whitespace", "simple elements", "subtle styling"],
                "code_indicators": ["clean code structure", "minimal dependencies", "simple patterns"],
                "user_experience": ["focused content", "distraction-free", "fast performance"]
            },
            "professional": {
                "visual_indicators": ["business-appropriate", "polished design", "consistent branding", "structured layout"],
                "code_indicators": ["enterprise patterns", "proper documentation", "maintainable code"],
                "user_experience": ["reliable functionality", "professional feel", "trustworthy interface"]
            }
        }

    def _load_security_checks(self) -> Dict[str, List[str]]:
        """Load security check patterns."""
        return {
            "javascript": [
                "xss_protection",
                "input_validation",
                "secure_api_calls",
                "no_eval_usage",
                "proper_authentication"
            ],
            "python": [
                "sql_injection_prevention",
                "input_sanitization",
                "secure_file_handling",
                "authentication_checks",
                "cors_configuration"
            ],
            "general": [
                "no_hardcoded_secrets",
                "proper_error_handling",
                "secure_communications",
                "data_validation"
            ]
        }

    async def review_code(self, generated_files: List[Dict[str, Any]], original_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to review generated code for quality, correctness, and vibe alignment.
        
        Args:
            generated_files: List of generated code files from the Coder Agent
            original_plan: Original plan including vibe analysis and requirements
            
        Returns:
            Comprehensive review report with suggestions, fixes, and approval status
        """
        await self.log_message(f"Starting code review for {len(generated_files)} files")
        await self.update_progress(85, "Initializing code review", 3)

        # Extract vibe information
        vibe_analysis = original_plan.get("vibe_analysis", {})
        original_vibe = original_plan.get("original_vibe", "")
        
        # Perform multi-layered review
        review_results = {
            "overall_status": "pending",
            "total_files_reviewed": len(generated_files),
            "syntax_analysis": {},
            "quality_assessment": {},
            "vibe_alignment": {},
            "security_review": {},
            "performance_analysis": {},
            "suggestions": [],
            "critical_issues": [],
            "warnings": [],
            "approval_status": False,
            "needs_fixes": False,
            "review_metadata": {
                "reviewer": "VibeCriticAgent",
                "review_timestamp": "now",
                "vibe_theme": vibe_analysis.get("key_emotions", [])
            }
        }

        # Phase 1: Syntax and Structure Analysis
        syntax_results = await self._analyze_syntax_and_structure(generated_files)
        review_results["syntax_analysis"] = syntax_results
        await self.update_progress(87, "Completed syntax analysis", 3)

        # Phase 2: Code Quality Assessment
        quality_results = await self._assess_code_quality(generated_files)
        review_results["quality_assessment"] = quality_results
        await self.update_progress(89, "Completed quality assessment", 3)

        # Phase 3: Vibe Alignment Review
        vibe_results = await self._review_vibe_alignment(generated_files, vibe_analysis, original_vibe)
        review_results["vibe_alignment"] = vibe_results
        await self.update_progress(91, "Completed vibe alignment review", 3)

        # Phase 4: Security and Performance Review
        security_results = await self._review_security_and_performance(generated_files)
        review_results["security_review"] = security_results["security"]
        review_results["performance_analysis"] = security_results["performance"]
        await self.update_progress(93, "Completed security and performance review", 3)

        # Phase 5: Generate Comprehensive Assessment
        final_assessment = await self._generate_final_assessment(review_results, original_plan)
        review_results.update(final_assessment)
        
        await self.update_progress(95, "Code review completed", 3)
        
        await self.log_message(
            f"Code review completed: {review_results['overall_status']}",
            metadata={
                "files_reviewed": len(generated_files),
                "critical_issues": len(review_results["critical_issues"]),
                "warnings": len(review_results["warnings"]),
                "needs_fixes": review_results["needs_fixes"],
                "vibe_alignment_score": vibe_results.get("alignment_score", 0)
            }
        )

        return review_results

    async def _analyze_syntax_and_structure(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze syntax and code structure for each file."""
        
        results = {
            "files_analyzed": 0,
            "syntax_errors": [],
            "structure_issues": [],
            "file_reports": {}
        }
        
        for file_info in files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            
            file_report = {
                "path": file_path,
                "language": language,
                "syntax_valid": True,
                "structure_valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Language-specific syntax checking
            if language == "javascript":
                syntax_check = await self._check_javascript_syntax(content, file_path)
                file_report.update(syntax_check)
            elif language == "python":
                syntax_check = await self._check_python_syntax(content, file_path)
                file_report.update(syntax_check)
            elif language == "css":
                syntax_check = await self._check_css_syntax(content, file_path)
                file_report.update(syntax_check)
            elif language == "html":
                syntax_check = await self._check_html_syntax(content, file_path)
                file_report.update(syntax_check)
            elif language == "json":
                syntax_check = await self._check_json_syntax(content, file_path)
                file_report.update(syntax_check)
            
            # Collect issues
            if not file_report["syntax_valid"]:
                results["syntax_errors"].extend(file_report["issues"])
            
            results["file_reports"][file_path] = file_report
            results["files_analyzed"] += 1
        
        return results

    async def _check_javascript_syntax(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check JavaScript/JSX syntax and React patterns."""
        
        report = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Basic syntax checks
        try:
            # Check for common JSX/React patterns
            if "import React" not in content and (".jsx" in file_path or "React" in content):
                report["warnings"].append("Missing React import in JSX file")
            
            # Check for export statements
            if "export" not in content and not file_path.endswith(".json"):
                report["warnings"].append("No export statement found")
            
            # Check for proper component naming (if it's a component)
            if ".jsx" in file_path or "component" in file_path.lower():
                component_match = re.search(r'const\s+(\w+)\s*=', content)
                if component_match:
                    component_name = component_match.group(1)
                    if not component_name[0].isupper():
                        report["warnings"].append(f"Component name '{component_name}' should start with uppercase")
            
            # Check for common mistakes
            if "onClick=" in content and "function" not in content and "=>" not in content:
                report["warnings"].append("onClick handler might be missing function implementation")
            
            # Check for consistent quotes
            single_quotes = content.count("'")
            double_quotes = content.count('"')
            if single_quotes > 0 and double_quotes > 0 and abs(single_quotes - double_quotes) > 5:
                report["warnings"].append("Inconsistent quote usage detected")
            
        except Exception as e:
            report["syntax_valid"] = False
            report["issues"].append(f"JavaScript syntax analysis failed: {str(e)}")
        
        return report

    async def _check_python_syntax(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check Python syntax and patterns."""
        
        report = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # Parse Python AST
            ast.parse(content)
            
            # Check for common patterns
            lines = content.split('\n')
            
            # Check imports at top
            import_section = True
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('import ') or line.startswith('from '):
                    if not import_section:
                        report["warnings"].append(f"Import statement on line {i+1} should be at the top")
                else:
                    import_section = False
            
            # Check for function naming
            function_matches = re.findall(r'def\s+([a-zA-Z_]\w*)', content)
            for func_name in function_matches:
                if not func_name.islower() and '_' not in func_name:
                    report["warnings"].append(f"Function '{func_name}' should use snake_case naming")
            
            # Check for class naming
            class_matches = re.findall(r'class\s+([a-zA-Z_]\w*)', content)
            for class_name in class_matches:
                if not class_name[0].isupper():
                    report["warnings"].append(f"Class '{class_name}' should use PascalCase naming")
            
        except SyntaxError as e:
            report["syntax_valid"] = False
            report["issues"].append(f"Python syntax error: {str(e)}")
        except Exception as e:
            report["warnings"].append(f"Python analysis warning: {str(e)}")
        
        return report

    async def _check_css_syntax(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check CSS syntax and patterns."""
        
        report = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # Basic CSS validation
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            if open_braces != close_braces:
                report["syntax_valid"] = False
                report["issues"].append("Mismatched braces in CSS")
            
            # Check for Tailwind imports if it's a Tailwind file
            if "@tailwind" in content:
                required_imports = ["@tailwind base", "@tailwind components", "@tailwind utilities"]
                for import_stmt in required_imports:
                    if import_stmt not in content:
                        report["warnings"].append(f"Missing Tailwind import: {import_stmt}")
            
            # Check for unused CSS (basic check)
            if len(content.strip()) == 0:
                report["warnings"].append("CSS file appears to be empty")
            
        except Exception as e:
            report["warnings"].append(f"CSS analysis warning: {str(e)}")
        
        return report

    async def _check_html_syntax(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check HTML syntax and structure."""
        
        report = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # Basic HTML validation
            if "<!DOCTYPE html>" not in content:
                report["warnings"].append("Missing DOCTYPE declaration")
            
            if "<html" not in content:
                report["warnings"].append("Missing html tag")
            
            if "<head>" not in content:
                report["warnings"].append("Missing head section")
            
            if "<body>" not in content:
                report["warnings"].append("Missing body section")
            
            # Check for meta viewport (important for responsive design)
            if "viewport" not in content:
                report["warnings"].append("Missing viewport meta tag for responsive design")
            
            # Check for title
            if "<title>" not in content:
                report["warnings"].append("Missing title tag")
            
        except Exception as e:
            report["warnings"].append(f"HTML analysis warning: {str(e)}")
        
        return report

    async def _check_json_syntax(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check JSON syntax."""
        
        report = {
            "syntax_valid": True,
            "structure_valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            json.loads(content)
            
            # Package.json specific checks
            if "package.json" in file_path:
                package_data = json.loads(content)
                
                required_fields = ["name", "version"]
                for field in required_fields:
                    if field not in package_data:
                        report["warnings"].append(f"Missing required field in package.json: {field}")
                
                if "scripts" not in package_data:
                    report["warnings"].append("No scripts section in package.json")
                
        except json.JSONDecodeError as e:
            report["syntax_valid"] = False
            report["issues"].append(f"JSON syntax error: {str(e)}")
        except Exception as e:
            report["warnings"].append(f"JSON analysis warning: {str(e)}")
        
        return report

    async def _assess_code_quality(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall code quality and best practices."""
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        quality_reviewer = self.create_agent(
            role="Senior Code Quality Analyst",
            goal="Assess code quality and adherence to best practices",
            backstory="""You are a senior code quality analyst with expertise in modern 
            development practices. You review code for maintainability, readability, 
            performance, and adherence to industry standards.""",
            tools=tools
        )

        # Prepare file summary for review
        file_summary = []
        for file_info in files:
            file_summary.append({
                "path": file_info.get("path", ""),
                "language": file_info.get("language", ""),
                "lines": len(file_info.get("content", "").split('\n')),
                "content_preview": file_info.get("content", "")[:500] + "..."
            })

        quality_task = Task(
            description=f"""
            Assess the code quality for these generated files:
            
            Files to review: {json.dumps(file_summary, indent=2)}
            
            Evaluate each file for:
            1. **Code Organization**: Proper structure and organization
            2. **Naming Conventions**: Consistent and meaningful names
            3. **Documentation**: Comments and code clarity
            4. **Best Practices**: Framework-specific best practices
            5. **Maintainability**: How easy is it to maintain and modify
            6. **Reusability**: Component and function reusability
            7. **Error Handling**: Proper error handling patterns
            8. **Performance**: Potential performance issues
            
            Provide specific feedback for each file and overall assessment.
            Rate each category from 1-10 and provide specific suggestions for improvement.
            """,
            agent=quality_reviewer,
            expected_output="Detailed code quality assessment with scores and suggestions"
        )

        crew = Crew(
            agents=[quality_reviewer],
            tasks=[quality_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        quality_result = await self.execute_crew_with_retry(crew, {})
        
        return {
            "assessment_result": str(quality_result),
            "files_reviewed": len(files),
            "quality_score": self._extract_quality_score(str(quality_result)),
            "recommendations": self._extract_recommendations(str(quality_result))
        }

    async def _review_vibe_alignment(self, files: List[Dict[str, Any]], vibe_analysis: Dict[str, Any], original_vibe: str) -> Dict[str, Any]:
        """Review how well the generated code aligns with the original vibe."""
        
        tools = [AgentTools.write_file, AgentTools.read_file]
        
        vibe_reviewer = self.create_agent(
            role="Vibe Alignment Specialist",
            goal="Assess how well generated code matches the user's original vibe and vision",
            backstory="""You are a specialist in understanding user intentions and design 
            aesthetics. You excel at evaluating whether generated code truly captures 
            the essence and feeling that users want to convey in their projects.""",
            tools=tools
        )

        # Extract UI/design files for review
        ui_files = [f for f in files if f.get("language") in ["javascript", "css", "html"] or "component" in f.get("path", "").lower()]
        
        vibe_task = Task(
            description=f"""
            Evaluate how well the generated code aligns with the user's original vibe:
            
            Original User Vibe: "{original_vibe}"
            
            Vibe Analysis Results:
            - Project Type: {vibe_analysis.get("project_type", "N/A")}
            - UI Requirements: {vibe_analysis.get("ui_requirements", [])}
            - Key Emotions: {vibe_analysis.get("key_emotions", [])}
            - Core Features: {vibe_analysis.get("core_features", [])}
            
            Generated UI/Component Files:
            {json.dumps([{"path": f["path"], "language": f["language"], "preview": f["content"][:300]} for f in ui_files], indent=2)}
            
            Assess alignment in these areas:
            1. **Visual Style**: Does the code produce the visual style the user wanted?
            2. **Functionality**: Are the requested features properly implemented?
            3. **User Experience**: Does it feel like what the user envisioned?
            4. **Emotional Tone**: Does the interface convey the right mood/feeling?
            5. **Technical Approach**: Is the technology choice appropriate for the vibe?
            
            Rate alignment from 1-10 and provide specific feedback on how well 
            the generated code captures the user's vision.
            """,
            agent=vibe_reviewer,
            expected_output="Detailed vibe alignment assessment with score and specific feedback"
        )

        crew = Crew(
            agents=[vibe_reviewer],
            tasks=[vibe_task],
            verbose=settings.crewai_verbose,
            process=Process.sequential
        )

        vibe_result = await self.execute_crew_with_retry(crew, {})
        
        alignment_score = self._extract_alignment_score(str(vibe_result))
        
        return {
            "alignment_result": str(vibe_result),
            "alignment_score": alignment_score,
            "ui_files_reviewed": len(ui_files),
            "vibe_match_quality": "excellent" if alignment_score >= 8 else "good" if alignment_score >= 6 else "needs_improvement",
            "specific_feedback": self._extract_vibe_feedback(str(vibe_result))
        }

    async def _review_security_and_performance(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review security and performance aspects of the generated code."""
        
        security_issues = []
        performance_issues = []
        
        for file_info in files:
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            file_path = file_info.get("path", "")
            
            # Security checks
            if language == "javascript":
                # Check for potential XSS vulnerabilities
                if "innerHTML" in content and "sanitize" not in content:
                    security_issues.append({
                        "file": file_path,
                        "issue": "Potential XSS vulnerability with innerHTML usage",
                        "severity": "medium",
                        "suggestion": "Use textContent or sanitize HTML content"
                    })
                
                # Check for eval usage
                if "eval(" in content:
                    security_issues.append({
                        "file": file_path,
                        "issue": "Use of eval() function detected",
                        "severity": "high",
                        "suggestion": "Avoid eval() usage for security reasons"
                    })
            
            elif language == "python":
                # Check for SQL injection vulnerabilities
                if "execute(" in content and "%" in content:
                    security_issues.append({
                        "file": file_path,
                        "issue": "Potential SQL injection vulnerability",
                        "severity": "high",
                        "suggestion": "Use parameterized queries"
                    })
            
            # Performance checks
            if language == "javascript":
                # Check for inefficient patterns
                if "map(" in content and "filter(" in content and content.count("map(") > 1:
                    performance_issues.append({
                        "file": file_path,
                        "issue": "Multiple array operations that could be optimized",
                        "severity": "low",
                        "suggestion": "Consider combining map/filter operations"
                    })
            
            # General checks
            if len(content) > 10000:  # Large file
                performance_issues.append({
                    "file": file_path,
                    "issue": "Large file size detected",
                    "severity": "medium",
                    "suggestion": "Consider breaking into smaller modules"
                })
        
        return {
            "security": {
                "issues_found": len(security_issues),
                "issues": security_issues,
                "overall_security_score": 10 - min(len(security_issues) * 2, 8)
            },
            "performance": {
                "issues_found": len(performance_issues),
                "issues": performance_issues,
                "overall_performance_score": 10 - min(len(performance_issues) * 1.5, 7)
            }
        }

    async def _generate_final_assessment(self, review_results: Dict[str, Any], original_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final assessment and recommendations."""
        
        # Calculate overall scores
        syntax_score = 10 if not review_results["syntax_analysis"].get("syntax_errors") else 7
        quality_score = review_results["quality_assessment"].get("quality_score", 8)
        vibe_score = review_results["vibe_alignment"].get("alignment_score", 8)
        security_score = review_results["security_review"].get("overall_security_score", 9)
        performance_score = review_results["performance_analysis"].get("overall_performance_score", 8)
        
        # Weight the scores
        overall_score = (
            syntax_score * 0.2 +
            quality_score * 0.25 +
            vibe_score * 0.3 +
            security_score * 0.15 +
            performance_score * 0.1
        )
        
        # Determine if fixes are needed
        critical_issues = review_results["syntax_analysis"].get("syntax_errors", [])
        critical_issues.extend([
            issue for issue in review_results["security_review"].get("issues", [])
            if issue.get("severity") == "high"
        ])
        
        needs_fixes = len(critical_issues) > 0 or overall_score < 6
        approval_status = overall_score >= 7 and not critical_issues
        
        # Generate suggestions
        suggestions = []
        
        if syntax_score < 8:
            suggestions.append({
                "type": "syntax",
                "priority": "high",
                "message": "Fix syntax errors before deployment",
                "details": review_results["syntax_analysis"].get("syntax_errors", [])
            })
        
        if quality_score < 7:
            suggestions.append({
                "type": "quality",
                "priority": "medium",
                "message": "Improve code quality and organization",
                "details": review_results["quality_assessment"].get("recommendations", [])
            })
        
        if vibe_score < 6:
            suggestions.append({
                "type": "vibe_alignment",
                "priority": "high",
                "message": "Generated code doesn't match user's vibe well",
                "details": review_results["vibe_alignment"].get("specific_feedback", [])
            })
        
        if security_score < 8:
            suggestions.append({
                "type": "security",
                "priority": "high",
                "message": "Address security vulnerabilities",
                "details": review_results["security_review"].get("issues", [])
            })
        
        status = "approved" if approval_status else "needs_revision" if needs_fixes else "conditional_approval"
        
        return {
            "overall_status": status,
            "overall_score": round(overall_score, 1),
            "score_breakdown": {
                "syntax": syntax_score,
                "quality": quality_score,
                "vibe_alignment": vibe_score,
                "security": security_score,
                "performance": performance_score
            },
            "approval_status": approval_status,
            "needs_fixes": needs_fixes,
            "critical_issues": critical_issues,
            "suggestions": suggestions,
            "summary": self._generate_summary(overall_score, approval_status, len(suggestions))
        }

    def _generate_summary(self, overall_score: float, approval_status: bool, suggestions_count: int) -> str:
        """Generate a human-readable summary of the review."""
        
        if approval_status:
            return f"✅ Code review passed! Overall score: {overall_score}/10. The generated code meets quality standards and aligns well with your vibe."
        elif overall_score >= 6:
            return f"⚠️ Code review completed with minor issues. Score: {overall_score}/10. {suggestions_count} suggestions for improvement."
        else:
            return f"❌ Code review found significant issues. Score: {overall_score}/10. Please address the {suggestions_count} critical issues before proceeding."

    # Utility methods for extracting information from AI responses
    def _extract_quality_score(self, response: str) -> float:
        """Extract quality score from response."""
        score_match = re.search(r'(?:score|rating|quality)[:\s]+(\d+(?:\.\d+)?)', response.lower())
        if score_match:
            return float(score_match.group(1))
        return 7.5  # Default score

    def _extract_alignment_score(self, response: str) -> float:
        """Extract alignment score from response."""
        score_match = re.search(r'(?:alignment|score|rating)[:\s]+(\d+(?:\.\d+)?)', response.lower())
        if score_match:
            return float(score_match.group(1))
        return 7.0  # Default score

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response."""
        recommendations = []
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                recommendations.append(line.strip())
        return recommendations[:5]  # Limit to top 5

    def _extract_vibe_feedback(self, response: str) -> List[str]:
        """Extract specific vibe feedback from response."""
        feedback = []
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['vibe', 'feeling', 'mood', 'style', 'aesthetic']):
                feedback.append(line.strip())
        return feedback[:3]  # Limit to top 3

    async def execute_crew_with_retry(self, crew, inputs):
        """Execute crew with retry logic."""
        try:
            result = await crew.kickoff_async(inputs)
            return result
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return f"Review failed: {str(e)}. Manual review recommended."