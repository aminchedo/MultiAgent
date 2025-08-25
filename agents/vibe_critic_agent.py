"""
VibeCriticAgent - Review generated code for quality and best practices compliance
"""

import re
import ast
import json
from typing import Dict, Any, List, Optional, Tuple
from agents.vibe_base_agent import VibeBaseAgent
import logging

logger = logging.getLogger(__name__)


class VibeCriticAgent(VibeBaseAgent):
    """Agent for reviewing generated code quality and best practices."""
    
    def __init__(self):
        super().__init__()
        self.quality_criteria = {
            'typescript': {
                'type_safety': 0.3,
                'interface_usage': 0.2,
                'proper_imports': 0.2,
                'component_structure': 0.3
            },
            'styling': {
                'consistency': 0.3,
                'responsive_design': 0.3,
                'accessibility': 0.2,
                'performance': 0.2
            },
            'architecture': {
                'component_separation': 0.3,
                'reusability': 0.2,
                'maintainability': 0.3,
                'scalability': 0.2
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "code_quality_analysis",
            "typescript_validation",
            "accessibility_checking",
            "performance_assessment",
            "best_practices_review"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        required_fields = ['files', 'plan']
        return all(field in input_data for field in required_fields)
    
    def review_generated_code(self, files: List[Dict], plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        MANDATORY IMPLEMENTATION - Review code quality
        MUST validate: TypeScript types, styling consistency, accessibility, performance
        MUST return: quality scores, improvement recommendations, compliance reports
        """
        if not self.validate_input({'files': files, 'plan': plan}):
            raise ValueError("Invalid input data for code review")
        
        review_results = {
            'overall_score': 0.0,
            'category_scores': {},
            'file_reviews': {},
            'recommendations': [],
            'compliance_report': {},
            'issues_found': [],
            'best_practices_score': 0.0
        }
        
        try:
            # Analyze each file
            for file_data in files:
                file_path = file_data.get('path', file_data.get('filename', 'unknown'))
                file_content = file_data.get('content', '')
                
                file_review = self._analyze_file(file_path, file_content, plan)
                review_results['file_reviews'][file_path] = file_review
                
                # Collect issues
                review_results['issues_found'].extend(file_review.get('issues', []))
            
            # Calculate category scores
            review_results['category_scores'] = self._calculate_category_scores(review_results['file_reviews'])
            
            # Calculate overall score
            review_results['overall_score'] = self._calculate_overall_score(review_results['category_scores'])
            
            # Generate recommendations
            review_results['recommendations'] = self._generate_recommendations(
                review_results['issues_found'], 
                review_results['category_scores']
            )
            
            # Generate compliance report
            review_results['compliance_report'] = self._generate_compliance_report(
                review_results['file_reviews'], 
                plan
            )
            
            # Calculate best practices score
            review_results['best_practices_score'] = self._calculate_best_practices_score(
                review_results['file_reviews']
            )
            
            return review_results
            
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return {
                'overall_score': 0.0,
                'error': str(e),
                'success': False
            }
    
    def _analyze_file(self, file_path: str, content: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual file for quality metrics."""
        file_extension = file_path.split('.')[-1] if '.' in file_path else ''
        
        analysis = {
            'file_path': file_path,
            'file_type': file_extension,
            'scores': {},
            'issues': [],
            'suggestions': [],
            'metrics': {}
        }
        
        # TypeScript/JavaScript analysis
        if file_extension in ['ts', 'tsx', 'js', 'jsx']:
            analysis.update(self._analyze_typescript_file(content, file_extension, plan))
        
        # CSS/Styling analysis
        elif file_extension in ['css', 'scss', 'sass']:
            analysis.update(self._analyze_css_file(content, plan))
        
        # HTML analysis
        elif file_extension in ['html', 'htm']:
            analysis.update(self._analyze_html_file(content, plan))
        
        # Vue file analysis
        elif file_extension == 'vue':
            analysis.update(self._analyze_vue_file(content, plan))
        
        # JSON configuration analysis
        elif file_extension == 'json':
            analysis.update(self._analyze_json_file(content, file_path))
        
        return analysis
    
    def _analyze_typescript_file(self, content: str, file_extension: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TypeScript/JavaScript file."""
        scores = {}
        issues = []
        suggestions = []
        metrics = {}
        
        # Type safety analysis (for TypeScript)
        if file_extension in ['ts', 'tsx']:
            type_score, type_issues = self._check_typescript_types(content)
            scores['type_safety'] = type_score
            issues.extend(type_issues)
        
        # Component structure analysis
        component_score, component_issues = self._check_component_structure(content, file_extension)
        scores['component_structure'] = component_score
        issues.extend(component_issues)
        
        # Import/Export analysis
        import_score, import_issues = self._check_imports_exports(content)
        scores['imports'] = import_score
        issues.extend(import_issues)
        
        # Code complexity
        complexity_score, complexity_metrics = self._calculate_code_complexity(content)
        scores['complexity'] = complexity_score
        metrics.update(complexity_metrics)
        
        # React-specific checks
        if file_extension in ['jsx', 'tsx']:
            react_score, react_issues = self._check_react_best_practices(content)
            scores['react_practices'] = react_score
            issues.extend(react_issues)
        
        # Generate suggestions
        suggestions = self._generate_typescript_suggestions(scores, content)
        
        return {
            'scores': scores,
            'issues': issues,
            'suggestions': suggestions,
            'metrics': metrics
        }
    
    def _check_typescript_types(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check TypeScript type usage and safety."""
        score = 100.0
        issues = []
        
        # Check for 'any' usage
        any_matches = re.findall(r':\s*any\b', content)
        if any_matches:
            score -= len(any_matches) * 10
            issues.append({
                'type': 'type_safety',
                'severity': 'warning',
                'message': f'Found {len(any_matches)} usages of "any" type',
                'suggestion': 'Replace "any" with specific types'
            })
        
        # Check for interface definitions
        interface_matches = re.findall(r'interface\s+\w+', content)
        if not interface_matches and 'tsx' in content:
            score -= 15
            issues.append({
                'type': 'type_safety',
                'severity': 'info',
                'message': 'No interfaces defined for React components',
                'suggestion': 'Define interfaces for component props'
            })
        
        # Check for proper function typing
        untyped_functions = re.findall(r'function\s+\w+\s*\([^)]*\)\s*{', content)
        if untyped_functions:
            score -= len(untyped_functions) * 5
            issues.append({
                'type': 'type_safety',
                'severity': 'warning',
                'message': f'Found {len(untyped_functions)} untyped functions',
                'suggestion': 'Add return type annotations to functions'
            })
        
        return max(0, score), issues
    
    def _check_component_structure(self, content: str, file_extension: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check component structure and organization."""
        score = 100.0
        issues = []
        
        # Check for single responsibility
        component_count = len(re.findall(r'(function|const)\s+[A-Z]\w*', content))
        if component_count > 1:
            score -= (component_count - 1) * 20
            issues.append({
                'type': 'structure',
                'severity': 'warning',
                'message': f'Multiple components in single file ({component_count})',
                'suggestion': 'Split components into separate files'
            })
        
        # Check for proper exports
        if not re.search(r'export\s+(default|{)', content):
            score -= 30
            issues.append({
                'type': 'structure',
                'severity': 'error',
                'message': 'No export statement found',
                'suggestion': 'Add proper export statement'
            })
        
        # Check for inline styles (anti-pattern)
        inline_styles = re.findall(r'style\s*=\s*{{', content)
        if inline_styles:
            score -= len(inline_styles) * 5
            issues.append({
                'type': 'structure',
                'severity': 'info',
                'message': f'Found {len(inline_styles)} inline styles',
                'suggestion': 'Consider using CSS classes or styled components'
            })
        
        return max(0, score), issues
    
    def _check_imports_exports(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check import/export patterns."""
        score = 100.0
        issues = []
        
        # Check for relative import patterns
        relative_imports = re.findall(r'from\s+[\'"]\.\./', content)
        if len(relative_imports) > 3:
            score -= (len(relative_imports) - 3) * 5
            issues.append({
                'type': 'imports',
                'severity': 'info',
                'message': f'Many relative imports ({len(relative_imports)})',
                'suggestion': 'Consider using absolute imports or path mapping'
            })
        
        # Check for unused imports (basic check)
        import_matches = re.findall(r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"][^\'"]+[\'"]', content)
        for import_match in import_matches:
            imported_items = re.findall(r'(\w+)', import_match)
            for item in imported_items:
                if item not in ['import', 'from'] and content.count(item) < 2:
                    score -= 2
                    issues.append({
                        'type': 'imports',
                        'severity': 'warning',
                        'message': f'Potentially unused import: {item}',
                        'suggestion': 'Remove unused imports'
                    })
        
        return max(0, score), issues
    
    def _calculate_code_complexity(self, content: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate code complexity metrics."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        metrics = {
            'total_lines': len(lines),
            'code_lines': len(non_empty_lines),
            'function_count': len(re.findall(r'function\s+\w+|const\s+\w+\s*=\s*\(', content)),
            'nesting_depth': self._calculate_max_nesting_depth(content)
        }
        
        # Calculate complexity score
        score = 100.0
        
        if metrics['code_lines'] > 300:
            score -= (metrics['code_lines'] - 300) * 0.1
        
        if metrics['nesting_depth'] > 4:
            score -= (metrics['nesting_depth'] - 4) * 10
        
        if metrics['function_count'] > 10:
            score -= (metrics['function_count'] - 10) * 5
        
        return max(0, score), metrics
    
    def _calculate_max_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth in code."""
        depth = 0
        max_depth = 0
        
        for char in content:
            if char == '{':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == '}':
                depth -= 1
        
        return max_depth
    
    def _check_react_best_practices(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check React-specific best practices."""
        score = 100.0
        issues = []
        
        # Check for key prop in lists
        map_without_key = re.findall(r'\.map\([^)]*\)\s*=>\s*<[^>]*(?!.*key=)', content)
        if map_without_key:
            score -= len(map_without_key) * 20
            issues.append({
                'type': 'react',
                'severity': 'warning',
                'message': f'Found {len(map_without_key)} map operations without key prop',
                'suggestion': 'Add key prop to mapped elements'
            })
        
        # Check for useEffect dependencies
        use_effect_no_deps = re.findall(r'useEffect\([^)]+\);', content)
        if use_effect_no_deps:
            score -= len(use_effect_no_deps) * 10
            issues.append({
                'type': 'react',
                'severity': 'warning',
                'message': f'Found {len(use_effect_no_deps)} useEffect without dependencies',
                'suggestion': 'Add dependency array to useEffect'
            })
        
        # Check for proper hook usage
        hooks_in_conditions = re.findall(r'if\s*\([^)]*\)\s*{[^}]*use\w+', content)
        if hooks_in_conditions:
            score -= len(hooks_in_conditions) * 25
            issues.append({
                'type': 'react',
                'severity': 'error',
                'message': f'Found {len(hooks_in_conditions)} hooks inside conditions',
                'suggestion': 'Move hooks to top level of component'
            })
        
        return max(0, score), issues
    
    def _analyze_css_file(self, content: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CSS file for styling quality."""
        scores = {}
        issues = []
        suggestions = []
        
        # Check for consistent naming
        naming_score, naming_issues = self._check_css_naming(content)
        scores['naming'] = naming_score
        issues.extend(naming_issues)
        
        # Check for responsive design
        responsive_score, responsive_issues = self._check_responsive_design(content)
        scores['responsive'] = responsive_score
        issues.extend(responsive_issues)
        
        # Check for accessibility
        accessibility_score, accessibility_issues = self._check_css_accessibility(content)
        scores['accessibility'] = accessibility_score
        issues.extend(accessibility_issues)
        
        return {
            'scores': scores,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_css_naming(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check CSS naming conventions."""
        score = 100.0
        issues = []
        
        # Check for BEM-like naming
        class_names = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', content)
        camelCase_classes = [name for name in class_names if re.match(r'[a-z]+[A-Z]', name)]
        
        if camelCase_classes:
            score -= len(camelCase_classes) * 5
            issues.append({
                'type': 'naming',
                'severity': 'info',
                'message': f'Found {len(camelCase_classes)} camelCase class names',
                'suggestion': 'Consider using kebab-case for CSS class names'
            })
        
        return max(0, score), issues
    
    def _check_responsive_design(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check for responsive design patterns."""
        score = 100.0
        issues = []
        
        # Check for media queries
        media_queries = re.findall(r'@media[^{]*{', content)
        if not media_queries:
            score -= 30
            issues.append({
                'type': 'responsive',
                'severity': 'warning',
                'message': 'No media queries found',
                'suggestion': 'Add responsive breakpoints with media queries'
            })
        
        # Check for fixed widths/heights
        fixed_dimensions = re.findall(r'(width|height):\s*\d+px', content)
        if fixed_dimensions:
            score -= len(fixed_dimensions) * 3
            issues.append({
                'type': 'responsive',
                'severity': 'info',
                'message': f'Found {len(fixed_dimensions)} fixed pixel dimensions',
                'suggestion': 'Consider using relative units (%, em, rem, vw, vh)'
            })
        
        return max(0, score), issues
    
    def _check_css_accessibility(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check CSS for accessibility concerns."""
        score = 100.0
        issues = []
        
        # Check for focus indicators
        focus_styles = re.findall(r':focus[^{]*{', content)
        if not focus_styles:
            score -= 20
            issues.append({
                'type': 'accessibility',
                'severity': 'warning',
                'message': 'No focus styles found',
                'suggestion': 'Add :focus styles for keyboard navigation'
            })
        
        # Check for color contrast considerations
        if 'color:' in content and 'background-color:' in content:
            score += 10  # Bonus for considering color combinations
        
        return max(0, score), issues
    
    def _analyze_html_file(self, content: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze HTML file for semantic and accessibility quality."""
        scores = {}
        issues = []
        
        # Check for semantic HTML
        semantic_score, semantic_issues = self._check_semantic_html(content)
        scores['semantic'] = semantic_score
        issues.extend(semantic_issues)
        
        # Check for accessibility
        accessibility_score, accessibility_issues = self._check_html_accessibility(content)
        scores['accessibility'] = accessibility_score
        issues.extend(accessibility_issues)
        
        return {
            'scores': scores,
            'issues': issues,
            'suggestions': []
        }
    
    def _check_semantic_html(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check for semantic HTML usage."""
        score = 100.0
        issues = []
        
        # Check for semantic elements
        semantic_elements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        found_semantic = sum(1 for element in semantic_elements if f'<{element}' in content)
        
        if found_semantic < 3:
            score -= (3 - found_semantic) * 15
            issues.append({
                'type': 'semantic',
                'severity': 'info',
                'message': f'Only {found_semantic} semantic elements found',
                'suggestion': 'Use more semantic HTML elements (header, nav, main, etc.)'
            })
        
        # Check for excessive div usage
        div_count = content.count('<div')
        total_elements = len(re.findall(r'<[a-zA-Z][^>]*>', content))
        if total_elements > 0 and div_count / total_elements > 0.6:
            score -= 20
            issues.append({
                'type': 'semantic',
                'severity': 'warning',
                'message': 'High ratio of div elements to semantic elements',
                'suggestion': 'Replace some divs with semantic HTML elements'
            })
        
        return max(0, score), issues
    
    def _check_html_accessibility(self, content: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check HTML for accessibility compliance."""
        score = 100.0
        issues = []
        
        # Check for alt attributes on images
        img_tags = re.findall(r'<img[^>]*>', content)
        imgs_without_alt = [img for img in img_tags if 'alt=' not in img]
        if imgs_without_alt:
            score -= len(imgs_without_alt) * 15
            issues.append({
                'type': 'accessibility',
                'severity': 'error',
                'message': f'{len(imgs_without_alt)} images without alt attributes',
                'suggestion': 'Add alt attributes to all images'
            })
        
        # Check for form labels
        input_tags = re.findall(r'<input[^>]*>', content)
        if input_tags:
            labels = content.count('<label')
            if labels < len(input_tags):
                score -= (len(input_tags) - labels) * 10
                issues.append({
                    'type': 'accessibility',
                    'severity': 'warning',
                    'message': 'Some form inputs may be missing labels',
                    'suggestion': 'Associate labels with form inputs'
                })
        
        return max(0, score), issues
    
    def _analyze_vue_file(self, content: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Vue single-file component."""
        # Extract sections
        template_section = self._extract_vue_section(content, 'template')
        script_section = self._extract_vue_section(content, 'script')
        style_section = self._extract_vue_section(content, 'style')
        
        scores = {}
        issues = []
        
        # Analyze template (HTML)
        if template_section:
            template_analysis = self._analyze_html_file(template_section, plan)
            scores.update({f'template_{k}': v for k, v in template_analysis['scores'].items()})
            issues.extend(template_analysis['issues'])
        
        # Analyze script (JavaScript/TypeScript)
        if script_section:
            file_ext = 'ts' if 'lang="ts"' in content else 'js'
            script_analysis = self._analyze_typescript_file(script_section, file_ext, plan)
            scores.update({f'script_{k}': v for k, v in script_analysis['scores'].items()})
            issues.extend(script_analysis['issues'])
        
        # Analyze style (CSS)
        if style_section:
            style_analysis = self._analyze_css_file(style_section, plan)
            scores.update({f'style_{k}': v for k, v in style_analysis['scores'].items()})
            issues.extend(style_analysis['issues'])
        
        return {
            'scores': scores,
            'issues': issues,
            'suggestions': []
        }
    
    def _extract_vue_section(self, content: str, section: str) -> str:
        """Extract specific section from Vue SFC."""
        pattern = rf'<{section}[^>]*>(.*?)</{section}>'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ''
    
    def _analyze_json_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze JSON configuration files."""
        scores = {'format': 100.0}
        issues = []
        
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            scores['format'] = 0.0
            issues.append({
                'type': 'format',
                'severity': 'error',
                'message': f'Invalid JSON: {str(e)}',
                'suggestion': 'Fix JSON syntax errors'
            })
        
        # Check package.json specific issues
        if 'package.json' in file_path:
            package_issues = self._check_package_json(content)
            issues.extend(package_issues)
        
        return {
            'scores': scores,
            'issues': issues,
            'suggestions': []
        }
    
    def _check_package_json(self, content: str) -> List[Dict[str, Any]]:
        """Check package.json for common issues."""
        issues = []
        
        try:
            package_data = json.loads(content)
            
            # Check for required fields
            required_fields = ['name', 'version', 'scripts']
            for field in required_fields:
                if field not in package_data:
                    issues.append({
                        'type': 'package',
                        'severity': 'warning',
                        'message': f'Missing required field: {field}',
                        'suggestion': f'Add {field} field to package.json'
                    })
            
            # Check for development vs production dependencies
            if 'dependencies' in package_data and 'devDependencies' in package_data:
                deps = package_data['dependencies']
                dev_deps = package_data['devDependencies']
                
                # Check for dev tools in production dependencies
                dev_tools = ['eslint', 'prettier', 'jest', 'webpack', 'vite', '@types/']
                for dep in deps:
                    if any(tool in dep for tool in dev_tools):
                        issues.append({
                            'type': 'package',
                            'severity': 'info',
                            'message': f'Development tool in dependencies: {dep}',
                            'suggestion': f'Move {dep} to devDependencies'
                        })
        
        except json.JSONDecodeError:
            pass  # Already handled in _analyze_json_file
        
        return issues
    
    def _calculate_category_scores(self, file_reviews: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate overall scores for different categories."""
        categories = ['type_safety', 'structure', 'accessibility', 'performance', 'maintainability']
        category_scores = {}
        
        for category in categories:
            total_score = 0
            file_count = 0
            
            for file_review in file_reviews.values():
                file_scores = file_review.get('scores', {})
                
                # Map file-specific scores to categories
                relevant_scores = []
                if category == 'type_safety':
                    relevant_scores = [file_scores.get('type_safety', 0)]
                elif category == 'structure':
                    relevant_scores = [file_scores.get('component_structure', 0), file_scores.get('imports', 0)]
                elif category == 'accessibility':
                    relevant_scores = [file_scores.get('accessibility', 0)]
                elif category == 'performance':
                    relevant_scores = [file_scores.get('complexity', 0)]
                elif category == 'maintainability':
                    relevant_scores = [file_scores.get('naming', 0), file_scores.get('react_practices', 0)]
                
                if relevant_scores:
                    avg_score = sum(score for score in relevant_scores if score > 0) / len([s for s in relevant_scores if s > 0]) if any(relevant_scores) else 0
                    total_score += avg_score
                    file_count += 1
            
            category_scores[category] = total_score / file_count if file_count > 0 else 0
        
        return category_scores
    
    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            'type_safety': 0.25,
            'structure': 0.25,
            'accessibility': 0.2,
            'performance': 0.15,
            'maintainability': 0.15
        }
        
        overall_score = sum(category_scores.get(category, 0) * weight for category, weight in weights.items())
        return round(overall_score, 2)
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]], category_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on issues and scores."""
        recommendations = []
        
        # Priority recommendations based on severity
        error_issues = [issue for issue in issues if issue.get('severity') == 'error']
        warning_issues = [issue for issue in issues if issue.get('severity') == 'warning']
        
        if error_issues:
            recommendations.append({
                'priority': 'high',
                'category': 'critical_fixes',
                'title': 'Fix Critical Issues',
                'description': f'Address {len(error_issues)} critical errors that prevent proper functionality',
                'actions': [issue['suggestion'] for issue in error_issues[:3]]
            })
        
        if warning_issues:
            recommendations.append({
                'priority': 'medium',
                'category': 'code_quality',
                'title': 'Improve Code Quality',
                'description': f'Address {len(warning_issues)} warnings to improve code quality',
                'actions': [issue['suggestion'] for issue in warning_issues[:3]]
            })
        
        # Category-specific recommendations
        for category, score in category_scores.items():
            if score < 70:
                recommendations.append({
                    'priority': 'medium' if score < 50 else 'low',
                    'category': category,
                    'title': f'Improve {category.replace("_", " ").title()}',
                    'description': f'Current score: {score:.1f}/100',
                    'actions': self._get_category_improvement_actions(category)
                })
        
        return recommendations
    
    def _get_category_improvement_actions(self, category: str) -> List[str]:
        """Get specific improvement actions for a category."""
        actions_map = {
            'type_safety': [
                'Add proper TypeScript types and interfaces',
                'Remove usage of "any" type',
                'Add return type annotations to functions'
            ],
            'structure': [
                'Split large components into smaller ones',
                'Improve component organization',
                'Add proper import/export statements'
            ],
            'accessibility': [
                'Add alt attributes to images',
                'Ensure proper form labeling',
                'Add focus indicators for keyboard navigation'
            ],
            'performance': [
                'Reduce code complexity',
                'Optimize component rendering',
                'Remove unused code and imports'
            ],
            'maintainability': [
                'Follow consistent naming conventions',
                'Add proper documentation',
                'Improve code organization'
            ]
        }
        
        return actions_map.get(category, ['Review and improve code quality'])
    
    def _generate_compliance_report(self, file_reviews: Dict[str, Dict[str, Any]], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance report against coding standards."""
        total_files = len(file_reviews)
        error_count = sum(len([issue for issue in review.get('issues', []) if issue.get('severity') == 'error']) for review in file_reviews.values())
        warning_count = sum(len([issue for issue in review.get('issues', []) if issue.get('severity') == 'warning']) for review in file_reviews.values())
        
        compliance_level = 'excellent'
        if error_count > 0:
            compliance_level = 'poor'
        elif warning_count > 5:
            compliance_level = 'fair'
        elif warning_count > 0:
            compliance_level = 'good'
        
        return {
            'compliance_level': compliance_level,
            'total_files_reviewed': total_files,
            'total_errors': error_count,
            'total_warnings': warning_count,
            'standards_met': {
                'typescript_usage': error_count == 0,
                'component_structure': warning_count < 3,
                'accessibility_basics': error_count == 0,
                'code_organization': True
            }
        }
    
    def _calculate_best_practices_score(self, file_reviews: Dict[str, Dict[str, Any]]) -> float:
        """Calculate best practices adherence score."""
        total_score = 0
        total_files = len(file_reviews)
        
        for review in file_reviews.values():
            file_score = 100
            
            # Deduct points for each issue
            issues = review.get('issues', [])
            for issue in issues:
                if issue.get('severity') == 'error':
                    file_score -= 20
                elif issue.get('severity') == 'warning':
                    file_score -= 10
                elif issue.get('severity') == 'info':
                    file_score -= 5
            
            total_score += max(0, file_score)
        
        return round(total_score / total_files if total_files > 0 else 0, 2)
    
    def _generate_typescript_suggestions(self, scores: Dict[str, float], content: str) -> List[str]:
        """Generate TypeScript-specific suggestions."""
        suggestions = []
        
        if scores.get('type_safety', 100) < 80:
            suggestions.append('Consider adding stricter TypeScript configuration')
            suggestions.append('Replace "any" types with specific interfaces')
        
        if scores.get('component_structure', 100) < 70:
            suggestions.append('Split large components into smaller, focused components')
            suggestions.append('Consider using custom hooks for complex logic')
        
        if 'useState' in content and 'useCallback' not in content:
            suggestions.append('Consider using useCallback for event handlers in components with state')
        
        return suggestions