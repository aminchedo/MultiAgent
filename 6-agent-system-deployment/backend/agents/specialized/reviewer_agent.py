"""
Reviewer Agent - Quality Control and Validation

This module implements specialized agents for code review, validation,
and quality assurance in the multi-agent system.
"""

import asyncio
import ast
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os
from pathlib import Path

import structlog
from prometheus_client import Counter, Histogram
import aiofiles

from backend.agents.base.base_agent import BaseAgent, AgentCapability
from backend.models.models import AgentType
from backend.memory.context_store import SharedMemoryStore


logger = structlog.get_logger()

# Metrics
code_reviews_counter = Counter('agent_code_reviews_total', 'Total code reviews performed')
validation_errors_counter = Counter('agent_validation_errors_total', 'Total validation errors found', ['error_type'])
review_duration_histogram = Histogram('agent_review_duration_seconds', 'Code review duration')


class ReviewSeverity(Enum):
    """Severity levels for review findings"""
    CRITICAL = "critical"  # Security vulnerabilities, data loss risks
    HIGH = "high"        # Major bugs, performance issues
    MEDIUM = "medium"    # Code quality issues, minor bugs
    LOW = "low"          # Style issues, suggestions
    INFO = "info"        # Informational findings


@dataclass
class ReviewFinding:
    """Represents a single review finding"""
    severity: ReviewSeverity
    category: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 1.0


class CodeReviewerAgent(BaseAgent):
    """
    Specialized agent for code review and validation.
    
    Performs static analysis, security checks, best practice validation,
    and provides improvement suggestions.
    """
    
    def __init__(self, agent_id: str, memory_store: SharedMemoryStore):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.REVIEWER,
            memory_store=memory_store
        )
        
        # Define capabilities
        self.capabilities = {
            AgentCapability.CODE_REVIEW,
            AgentCapability.SECURITY_SCAN,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.BEST_PRACTICES,
            AgentCapability.DEPENDENCY_CHECK
        }
        
        # Review rules and patterns
        self.security_patterns = self._load_security_patterns()
        self.code_smell_patterns = self._load_code_smell_patterns()
        self.best_practices = self._load_best_practices()
        
        # Tool configurations
        self.linters = {
            'python': ['pylint', 'flake8', 'mypy', 'bandit'],
            'javascript': ['eslint', 'jshint'],
            'typescript': ['tslint', 'eslint'],
            'go': ['golint', 'go vet'],
            'rust': ['clippy'],
            'java': ['checkstyle', 'spotbugs']
        }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a review task"""
        task_type = task.get('task_type')
        
        if task_type == 'code_review':
            return await self.review_code(task.get('payload', {}))
        elif task_type == 'security_scan':
            return await self.security_scan(task.get('payload', {}))
        elif task_type == 'validate_output':
            return await self.validate_agent_output(task.get('payload', {}))
        elif task_type == 'performance_review':
            return await self.review_performance(task.get('payload', {}))
        else:
            return {
                'success': False,
                'error': f'Unknown task type: {task_type}'
            }
    
    async def review_code(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive code review.
        
        Args:
            payload: Contains code artifacts, language, and review criteria
            
        Returns:
            Review results with findings and suggestions
        """
        with review_duration_histogram.time():
            code_reviews_counter.inc()
            
            artifacts = payload.get('artifacts', [])
            language = payload.get('language', 'python')
            review_criteria = payload.get('criteria', {})
            
            all_findings = []
            
            for artifact in artifacts:
                file_path = artifact.get('path', 'unknown')
                content = artifact.get('content', '')
                
                # Run multiple review checks in parallel
                findings = await asyncio.gather(
                    self._static_analysis(content, language, file_path),
                    self._security_check(content, language, file_path),
                    self._complexity_analysis(content, language, file_path),
                    self._style_check(content, language, file_path),
                    self._dependency_check(content, language, file_path)
                )
                
                # Flatten findings
                for finding_list in findings:
                    all_findings.extend(finding_list)
            
            # Categorize and prioritize findings
            categorized = self._categorize_findings(all_findings)
            
            # Generate improvement suggestions
            suggestions = await self._generate_suggestions(all_findings, artifacts)
            
            # Calculate overall score
            score = self._calculate_code_quality_score(all_findings)
            
            return {
                'success': True,
                'findings': [self._finding_to_dict(f) for f in all_findings],
                'summary': categorized,
                'suggestions': suggestions,
                'quality_score': score,
                'passed': score >= review_criteria.get('min_score', 0.7)
            }
    
    async def _static_analysis(self, code: str, language: str, file_path: str) -> List[ReviewFinding]:
        """Run static code analysis"""
        findings = []
        
        if language == 'python':
            # AST-based analysis for Python
            try:
                tree = ast.parse(code)
                findings.extend(self._analyze_python_ast(tree, file_path))
            except SyntaxError as e:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.CRITICAL,
                    category='syntax_error',
                    message=f'Syntax error: {str(e)}',
                    file_path=file_path,
                    line_number=e.lineno
                ))
        
        # Run external linters
        linter_findings = await self._run_linters(code, language, file_path)
        findings.extend(linter_findings)
        
        return findings
    
    def _analyze_python_ast(self, tree: ast.AST, file_path: str) -> List[ReviewFinding]:
        """Analyze Python AST for common issues"""
        findings = []
        
        class CodeAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.findings = []
                self.current_function = None
                self.function_complexity = {}
            
            def visit_FunctionDef(self, node):
                self.current_function = node.name
                self.function_complexity[node.name] = 0
                
                # Check function length
                func_length = node.end_lineno - node.lineno
                if func_length > 50:
                    self.findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category='code_smell',
                        message=f'Function {node.name} is too long ({func_length} lines)',
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion='Consider breaking this function into smaller functions'
                    ))
                
                # Check parameter count
                if len(node.args.args) > 5:
                    self.findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category='code_smell',
                        message=f'Function {node.name} has too many parameters ({len(node.args.args)})',
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion='Consider using a configuration object or builder pattern'
                    ))
                
                self.generic_visit(node)
                
                # Check cyclomatic complexity
                if self.function_complexity[node.name] > 10:
                    self.findings.append(ReviewFinding(
                        severity=ReviewSeverity.HIGH,
                        category='complexity',
                        message=f'Function {node.name} has high cyclomatic complexity ({self.function_complexity[node.name]})',
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion='Simplify the logic or extract helper methods'
                    ))
                
                self.current_function = None
            
            def visit_If(self, node):
                if self.current_function:
                    self.function_complexity[self.current_function] += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                if self.current_function:
                    self.function_complexity[self.current_function] += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                if self.current_function:
                    self.function_complexity[self.current_function] += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                if self.current_function:
                    self.function_complexity[self.current_function] += 1
                
                # Check for bare except
                if node.type is None:
                    self.findings.append(ReviewFinding(
                        severity=ReviewSeverity.HIGH,
                        category='error_handling',
                        message='Bare except clause found',
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion='Specify the exception type to catch'
                    ))
                
                self.generic_visit(node)
        
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        findings.extend(analyzer.findings)
        
        return findings
    
    async def _security_check(self, code: str, language: str, file_path: str) -> List[ReviewFinding]:
        """Check for security vulnerabilities"""
        findings = []
        
        # Check against security patterns
        for pattern_name, pattern_config in self.security_patterns.items():
            regex = pattern_config['regex']
            if re.search(regex, code, re.IGNORECASE | re.MULTILINE):
                for match in re.finditer(regex, code, re.IGNORECASE | re.MULTILINE):
                    line_num = code[:match.start()].count('\n') + 1
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity[pattern_config['severity']],
                        category='security',
                        message=pattern_config['message'],
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=match.group(0),
                        suggestion=pattern_config.get('suggestion')
                    ))
        
        # Language-specific security checks
        if language == 'python':
            # Check for dangerous functions
            dangerous_funcs = ['eval', 'exec', 'compile', '__import__']
            for func in dangerous_funcs:
                if re.search(rf'\b{func}\s*\(', code):
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.HIGH,
                        category='security',
                        message=f'Use of potentially dangerous function: {func}',
                        file_path=file_path,
                        suggestion=f'Avoid using {func} or ensure input is properly sanitized'
                    ))
        
        return findings
    
    async def _run_linters(self, code: str, language: str, file_path: str) -> List[ReviewFinding]:
        """Run external linting tools"""
        findings = []
        
        if language not in self.linters:
            return findings
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_file_extension(language), delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            for linter in self.linters.get(language, []):
                if await self._is_tool_available(linter):
                    linter_findings = await self._run_linter(linter, temp_file, language)
                    findings.extend(linter_findings)
        finally:
            os.unlink(temp_file)
        
        return findings
    
    async def _run_linter(self, linter: str, file_path: str, language: str) -> List[ReviewFinding]:
        """Run a specific linter tool"""
        findings = []
        
        try:
            # Configure linter command based on tool
            if linter == 'pylint':
                cmd = ['pylint', '--output-format=json', file_path]
            elif linter == 'eslint':
                cmd = ['eslint', '--format=json', file_path]
            elif linter == 'bandit':
                cmd = ['bandit', '-f', 'json', file_path]
            else:
                # Generic command
                cmd = [linter, file_path]
            
            # Run linter
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse output based on linter
            if linter in ['pylint', 'eslint', 'bandit']:
                findings.extend(self._parse_json_linter_output(stdout, linter))
            
        except Exception as e:
            logger.error(f"Error running linter {linter}: {str(e)}")
        
        return findings
    
    def _load_security_patterns(self) -> Dict[str, Any]:
        """Load security vulnerability patterns"""
        return {
            'sql_injection': {
                'regex': r'(execute|cursor\.execute)\s*\(\s*["\'].*%[s|d].*["\'].*%',
                'severity': 'CRITICAL',
                'message': 'Potential SQL injection vulnerability',
                'suggestion': 'Use parameterized queries instead of string formatting'
            },
            'hardcoded_password': {
                'regex': r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
                'severity': 'CRITICAL',
                'message': 'Hardcoded password detected',
                'suggestion': 'Use environment variables or secure key management'
            },
            'weak_crypto': {
                'regex': r'(md5|sha1)\s*\(',
                'severity': 'HIGH',
                'message': 'Weak cryptographic algorithm used',
                'suggestion': 'Use SHA-256 or stronger algorithms'
            },
            'insecure_random': {
                'regex': r'random\.(random|randint|choice)\s*\(',
                'severity': 'MEDIUM',
                'message': 'Insecure random number generation for security purposes',
                'suggestion': 'Use secrets module for cryptographic randomness'
            }
        }
    
    def _load_code_smell_patterns(self) -> Dict[str, Any]:
        """Load code smell patterns"""
        return {
            'todo_fixme': {
                'regex': r'#\s*(TODO|FIXME|XXX|HACK)',
                'severity': 'LOW',
                'message': 'Unresolved TODO/FIXME comment',
                'suggestion': 'Address the TODO or create a tracking issue'
            },
            'print_statements': {
                'regex': r'^\s*print\s*\(',
                'severity': 'LOW',
                'message': 'Debug print statement found',
                'suggestion': 'Use proper logging instead of print statements'
            },
            'long_line': {
                'regex': r'^.{121,}$',
                'severity': 'LOW',
                'message': 'Line exceeds 120 characters',
                'suggestion': 'Break long lines for better readability'
            }
        }
    
    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load best practice rules"""
        return {
            'python': [
                'Use type hints for function parameters and return values',
                'Follow PEP 8 style guidelines',
                'Write docstrings for all public functions and classes',
                'Use context managers for resource handling',
                'Prefer list comprehensions over map/filter when appropriate'
            ],
            'javascript': [
                'Use const/let instead of var',
                'Prefer arrow functions for callbacks',
                'Use async/await over promises when possible',
                'Implement proper error handling',
                'Use strict equality (===) instead of loose equality (==)'
            ]
        }
    
    def _calculate_code_quality_score(self, findings: List[ReviewFinding]) -> float:
        """Calculate overall code quality score"""
        if not findings:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            ReviewSeverity.CRITICAL: 0.4,
            ReviewSeverity.HIGH: 0.3,
            ReviewSeverity.MEDIUM: 0.2,
            ReviewSeverity.LOW: 0.08,
            ReviewSeverity.INFO: 0.02
        }
        
        total_weight = sum(severity_weights[f.severity] for f in findings)
        
        # Score decreases with more/severe findings
        score = max(0.0, 1.0 - (total_weight / 10))
        
        return round(score, 2)
    
    def _categorize_findings(self, findings: List[ReviewFinding]) -> Dict[str, Any]:
        """Categorize findings by severity and type"""
        categorized = {
            'by_severity': {},
            'by_category': {},
            'total': len(findings)
        }
        
        for finding in findings:
            # By severity
            severity = finding.severity.value
            if severity not in categorized['by_severity']:
                categorized['by_severity'][severity] = 0
            categorized['by_severity'][severity] += 1
            
            # By category
            category = finding.category
            if category not in categorized['by_category']:
                categorized['by_category'][category] = 0
            categorized['by_category'][category] += 1
            
            # Track validation errors
            validation_errors_counter.labels(error_type=category).inc()
        
        return categorized
    
    async def _generate_suggestions(self, findings: List[ReviewFinding], 
                                  artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on findings"""
        suggestions = []
        
        # Group findings by file
        findings_by_file = {}
        for finding in findings:
            file_path = finding.file_path or 'general'
            if file_path not in findings_by_file:
                findings_by_file[file_path] = []
            findings_by_file[file_path].append(finding)
        
        # Generate file-specific suggestions
        for file_path, file_findings in findings_by_file.items():
            if len(file_findings) > 10:
                suggestions.append({
                    'type': 'refactor',
                    'file': file_path,
                    'message': f'This file has {len(file_findings)} issues. Consider refactoring.',
                    'priority': 'high'
                })
            
            # Check for patterns
            security_issues = [f for f in file_findings if f.category == 'security']
            if len(security_issues) > 2:
                suggestions.append({
                    'type': 'security_review',
                    'file': file_path,
                    'message': 'Multiple security issues found. Requires security review.',
                    'priority': 'critical'
                })
        
        return suggestions
    
    def _finding_to_dict(self, finding: ReviewFinding) -> Dict[str, Any]:
        """Convert ReviewFinding to dictionary"""
        return {
            'severity': finding.severity.value,
            'category': finding.category,
            'message': finding.message,
            'file_path': finding.file_path,
            'line_number': finding.line_number,
            'code_snippet': finding.code_snippet,
            'suggestion': finding.suggestion,
            'confidence': finding.confidence
        }
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'go': '.go',
            'rust': '.rs',
            'java': '.java'
        }
        return extensions.get(language, '.txt')
    
    async def _is_tool_available(self, tool: str) -> bool:
        """Check if a tool is available in the system"""
        try:
            process = await asyncio.create_subprocess_exec(
                'which', tool,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
    
    def _parse_json_linter_output(self, output: bytes, linter: str) -> List[ReviewFinding]:
        """Parse JSON output from linters"""
        findings = []
        
        try:
            data = json.loads(output.decode('utf-8'))
            
            if linter == 'pylint':
                for issue in data:
                    findings.append(ReviewFinding(
                        severity=self._map_pylint_severity(issue.get('type', 'warning')),
                        category='linter',
                        message=f"{issue.get('symbol', '')}: {issue.get('message', '')}",
                        file_path=issue.get('path'),
                        line_number=issue.get('line'),
                        code_snippet=issue.get('obj', '')
                    ))
            
            elif linter == 'eslint':
                for file_result in data:
                    for message in file_result.get('messages', []):
                        findings.append(ReviewFinding(
                            severity=self._map_eslint_severity(message.get('severity', 1)),
                            category='linter',
                            message=message.get('message', ''),
                            file_path=file_result.get('filePath'),
                            line_number=message.get('line'),
                            suggestion=message.get('fix', {}).get('text')
                        ))
        
        except Exception as e:
            logger.error(f"Error parsing {linter} output: {str(e)}")
        
        return findings
    
    def _map_pylint_severity(self, pylint_type: str) -> ReviewSeverity:
        """Map pylint message types to review severity"""
        mapping = {
            'error': ReviewSeverity.HIGH,
            'warning': ReviewSeverity.MEDIUM,
            'refactor': ReviewSeverity.LOW,
            'convention': ReviewSeverity.LOW,
            'info': ReviewSeverity.INFO
        }
        return mapping.get(pylint_type, ReviewSeverity.LOW)
    
    def _map_eslint_severity(self, eslint_severity: int) -> ReviewSeverity:
        """Map eslint severity to review severity"""
        if eslint_severity == 2:
            return ReviewSeverity.HIGH
        else:
            return ReviewSeverity.MEDIUM
    
    async def validate_agent_output(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output from other agents"""
        agent_type = payload.get('agent_type')
        output = payload.get('output', {})
        validation_rules = payload.get('validation_rules', {})
        
        findings = []
        
        # Validate based on agent type
        if agent_type == AgentType.CODE_GENERATOR.value:
            findings.extend(await self._validate_generated_code(output))
        elif agent_type == AgentType.PLANNER.value:
            findings.extend(self._validate_plan(output))
        elif agent_type == AgentType.DOC_GENERATOR.value:
            findings.extend(self._validate_documentation(output))
        
        # Apply custom validation rules
        for rule_name, rule_config in validation_rules.items():
            rule_findings = await self._apply_validation_rule(output, rule_config)
            findings.extend(rule_findings)
        
        passed = all(f.severity not in [ReviewSeverity.CRITICAL, ReviewSeverity.HIGH] 
                    for f in findings)
        
        return {
            'success': True,
            'validated': True,
            'passed': passed,
            'findings': [self._finding_to_dict(f) for f in findings]
        }
    
    async def _validate_generated_code(self, output: Dict[str, Any]) -> List[ReviewFinding]:
        """Validate code generator output"""
        findings = []
        
        artifacts = output.get('artifacts', [])
        if not artifacts:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category='validation',
                message='No code artifacts found in output'
            ))
            return findings
        
        for artifact in artifacts:
            # Check for required files
            if artifact.get('type') == 'code' and not artifact.get('content'):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.HIGH,
                    category='validation',
                    message=f'Empty code file: {artifact.get("name", "unknown")}'
                ))
        
        return findings
    
    def _validate_plan(self, output: Dict[str, Any]) -> List[ReviewFinding]:
        """Validate planner output"""
        findings = []
        
        # Check for required plan components
        required_components = ['phases', 'structure', 'technologies']
        for component in required_components:
            if component not in output:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.HIGH,
                    category='validation',
                    message=f'Missing required plan component: {component}'
                ))
        
        # Validate plan structure
        if 'phases' in output and not isinstance(output['phases'], list):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category='validation',
                message='Plan phases should be a list'
            ))
        
        return findings
    
    def _validate_documentation(self, output: Dict[str, Any]) -> List[ReviewFinding]:
        """Validate documentation generator output"""
        findings = []
        
        docs = output.get('documentation', {})
        
        # Check for minimum documentation
        if not docs.get('readme'):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category='validation',
                message='Missing README documentation'
            ))
        
        # Check for API documentation if applicable
        if output.get('has_api') and not docs.get('api_docs'):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category='validation',
                message='Missing API documentation'
            ))
        
        return findings
    
    async def _apply_validation_rule(self, output: Dict[str, Any], 
                                   rule_config: Dict[str, Any]) -> List[ReviewFinding]:
        """Apply a custom validation rule"""
        findings = []
        
        rule_type = rule_config.get('type')
        
        if rule_type == 'required_field':
            field_path = rule_config.get('field_path', '').split('.')
            current = output
            
            for field in field_path:
                if field not in current:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.HIGH,
                        category='validation',
                        message=f'Required field missing: {rule_config.get("field_path")}'
                    ))
                    break
                current = current[field]
        
        elif rule_type == 'pattern_match':
            pattern = rule_config.get('pattern')
            field_value = output.get(rule_config.get('field'))
            
            if field_value and not re.match(pattern, str(field_value)):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category='validation',
                    message=f'Field {rule_config.get("field")} does not match required pattern'
                ))
        
        return findings
    
    async def security_scan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform dedicated security scan"""
        artifacts = payload.get('artifacts', [])
        scan_type = payload.get('scan_type', 'full')
        
        findings = []
        
        for artifact in artifacts:
            if artifact.get('type') == 'code':
                content = artifact.get('content', '')
                file_path = artifact.get('path', 'unknown')
                language = artifact.get('language', 'python')
                
                # Run security-focused checks
                sec_findings = await self._deep_security_scan(content, language, file_path)
                findings.extend(sec_findings)
        
        # Check for dependency vulnerabilities
        dep_findings = await self._scan_dependencies(payload.get('dependencies', []))
        findings.extend(dep_findings)
        
        # Calculate security score
        security_score = self._calculate_security_score(findings)
        
        return {
            'success': True,
            'findings': [self._finding_to_dict(f) for f in findings],
            'security_score': security_score,
            'passed': security_score >= 0.8
        }
    
    async def _deep_security_scan(self, code: str, language: str, file_path: str) -> List[ReviewFinding]:
        """Perform deep security analysis"""
        findings = []
        
        # OWASP Top 10 checks
        owasp_checks = {
            'injection': r'(system|exec|eval|subprocess\.call)\s*\([^)]*\+[^)]*\)',
            'broken_auth': r'(session|token|auth).*=.*["\'][^"\']+["\']',
            'sensitive_exposure': r'(api_key|secret|private_key)\s*=\s*["\'][^"\']+["\']',
            'xxe': r'(parseXML|XMLParser).*resolve_entities\s*=\s*True',
            'broken_access': r'@app\.route.*methods\s*=\s*\[[^\]]*\](?!.*@login_required)',
            'security_misconfig': r'DEBUG\s*=\s*True',
            'xss': r'innerHTML\s*=|document\.write\(',
            'insecure_deserialization': r'pickle\.loads?\(|yaml\.load\(',
            'vulnerable_components': r'requirements\.txt.*==\s*[0-9]+\.[0-9]+\.[0-9]+',
            'insufficient_logging': r'except.*:\s*pass'
        }
        
        for vuln_type, pattern in owasp_checks.items():
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.CRITICAL,
                    category='security',
                    message=f'Potential {vuln_type.replace("_", " ")} vulnerability',
                    file_path=file_path
                ))
        
        return findings
    
    async def _scan_dependencies(self, dependencies: List[Dict[str, Any]]) -> List[ReviewFinding]:
        """Scan dependencies for known vulnerabilities"""
        findings = []
        
        # This would integrate with vulnerability databases
        # For now, check for outdated versions
        for dep in dependencies:
            name = dep.get('name')
            version = dep.get('version')
            
            # Simplified check - in production, query CVE database
            if version and re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', version):
                major, minor, patch = map(int, version.split('.'))
                if major == 0:  # Pre-1.0 versions often have security issues
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category='dependency',
                        message=f'Pre-release dependency: {name}@{version}',
                        suggestion='Consider using a stable version'
                    ))
        
        return findings
    
    def _calculate_security_score(self, findings: List[ReviewFinding]) -> float:
        """Calculate security score based on findings"""
        if not findings:
            return 1.0
        
        critical_count = sum(1 for f in findings if f.severity == ReviewSeverity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == ReviewSeverity.HIGH)
        
        # Heavy penalty for critical security issues
        score = 1.0 - (critical_count * 0.3) - (high_count * 0.15)
        
        return max(0.0, score)
    
    async def review_performance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Review code for performance issues"""
        artifacts = payload.get('artifacts', [])
        findings = []
        
        for artifact in artifacts:
            if artifact.get('type') == 'code':
                content = artifact.get('content', '')
                language = artifact.get('language', 'python')
                file_path = artifact.get('path', 'unknown')
                
                perf_findings = await self._analyze_performance(content, language, file_path)
                findings.extend(perf_findings)
        
        return {
            'success': True,
            'findings': [self._finding_to_dict(f) for f in findings],
            'performance_score': self._calculate_performance_score(findings)
        }
    
    async def _analyze_performance(self, code: str, language: str, file_path: str) -> List[ReviewFinding]:
        """Analyze code for performance issues"""
        findings = []
        
        # Common performance anti-patterns
        if language == 'python':
            patterns = {
                'nested_loops': r'for\s+\w+\s+in\s+.*:\s*\n\s*for\s+\w+\s+in',
                'string_concat_loop': r'for.*:\s*\n.*\+=\s*["\']',
                'inefficient_list_comp': r'\[.*for.*for.*\]',
                'unnecessary_list_conversion': r'list\(.*\.keys\(\)\)',
                'repeated_regex_compile': r'for.*:\s*\n.*re\.(search|match|findall)\('
            }
            
            for issue, pattern in patterns.items():
                if re.search(pattern, code, re.MULTILINE):
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category='performance',
                        message=f'Potential performance issue: {issue.replace("_", " ")}',
                        file_path=file_path
                    ))
        
        return findings
    
    def _calculate_performance_score(self, findings: List[ReviewFinding]) -> float:
        """Calculate performance score"""
        perf_findings = [f for f in findings if f.category == 'performance']
        
        if not perf_findings:
            return 1.0
        
        # Deduct points for each performance issue
        score = 1.0 - (len(perf_findings) * 0.1)
        
        return max(0.0, score)