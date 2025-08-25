"""
VibePlannerAgent - Analyze vibe prompts using pattern matching and create comprehensive technical plans
"""

import re
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)


class VibePlannerAgent(BaseAgent):
    """Agent for analyzing vibe prompts and creating technical implementation plans."""
    
    def __init__(self):
        super().__init__()
        self.ui_patterns = {
            'modern': ['modern', 'contemporary', 'sleek', 'minimalist', 'clean'],
            'dark': ['dark', 'dark mode', 'night', 'black', 'dark theme'],
            'colorful': ['colorful', 'vibrant', 'bright', 'rainbow', 'multicolor'],
            'professional': ['professional', 'business', 'corporate', 'formal', 'enterprise']
        }
        
        self.project_patterns = {
            'dashboard': ['dashboard', 'admin', 'analytics', 'metrics', 'stats'],
            'blog': ['blog', 'articles', 'posts', 'news', 'content'],
            'portfolio': ['portfolio', 'showcase', 'gallery', 'work', 'projects'],
            'landing': ['landing', 'homepage', 'marketing', 'promo', 'intro'],
            'app': ['app', 'application', 'tool', 'utility', 'platform']
        }
        
        self.tech_patterns = {
            'react': ['react', 'jsx', 'hooks', 'components'],
            'vue': ['vue', 'nuxt', 'vuex', 'vue.js'],
            'vanilla': ['vanilla', 'html', 'css', 'javascript', 'js']
        }
        
        self.feature_patterns = {
            'authentication': ['auth', 'login', 'signup', 'user', 'account'],
            'database': ['database', 'data', 'storage', 'persistence'],
            'responsive': ['responsive', 'mobile', 'tablet', 'device'],
            'real-time': ['real-time', 'live', 'websocket', 'instant'],
            'search': ['search', 'filter', 'find', 'query'],
            'forms': ['form', 'input', 'submit', 'validation']
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "vibe_prompt_analysis",
            "pattern_matching", 
            "technical_planning",
            "complexity_assessment",
            "technology_recommendation"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        return 'vibe_prompt' in input_data and isinstance(input_data['vibe_prompt'], str)
    
    def decompose_vibe_prompt(self, vibe_prompt: str, project_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        MANDATORY IMPLEMENTATION - Analyze vibe prompt and create technical plan
        MUST detect: UI styles, project types, technology preferences, features, complexity
        MUST return: vibe_analysis, technical_requirements, implementation_steps
        """
        if not self.validate_input({'vibe_prompt': vibe_prompt}):
            raise ValueError("Invalid vibe prompt provided")
        
        prompt_lower = vibe_prompt.lower()
        
        # Detect UI styles
        detected_ui_styles = []
        for style, keywords in self.ui_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_ui_styles.append(style)
        
        # Detect project type
        detected_project_type = None
        project_scores = {}
        for proj_type, keywords in self.project_patterns.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower)
            project_scores[proj_type] = score
        
        if project_scores:
            detected_project_type = max(project_scores, key=project_scores.get)
            if project_scores[detected_project_type] == 0:
                detected_project_type = 'app'  # Default
        
        # Detect technology preferences
        detected_technologies = []
        for tech, keywords in self.tech_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_technologies.append(tech)
        
        if not detected_technologies:
            detected_technologies = ['react']  # Default to React
        
        # Detect features
        detected_features = []
        for feature, keywords in self.feature_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_features.append(feature)
        
        # Assess complexity
        complexity_indicators = len(detected_features) + len(detected_ui_styles)
        if complexity_indicators <= 2:
            complexity = 'simple'
        elif complexity_indicators <= 4:
            complexity = 'moderate'
        else:
            complexity = 'complex'
        
        # Create technical requirements
        tech_requirements = {
            'framework': detected_technologies[0],
            'styling': 'tailwind' if 'modern' in detected_ui_styles else 'css',
            'components': self._determine_components(detected_project_type, detected_features),
            'features': detected_features,
            'ui_theme': detected_ui_styles
        }
        
        # Create implementation steps
        implementation_steps = self._create_implementation_steps(
            detected_project_type, detected_technologies[0], detected_features
        )
        
        return {
            'vibe_analysis': {
                'original_prompt': vibe_prompt,
                'detected_ui_styles': detected_ui_styles,
                'detected_project_type': detected_project_type,
                'detected_technologies': detected_technologies,
                'detected_features': detected_features,
                'complexity': complexity
            },
            'technical_requirements': tech_requirements,
            'implementation_steps': implementation_steps,
            'estimated_time': self._estimate_time(complexity, len(detected_features)),
            'recommended_structure': self._recommend_structure(detected_technologies[0])
        }
    
    def _determine_components(self, project_type: str, features: List[str]) -> List[str]:
        """Determine required components based on project type and features."""
        components = []
        
        # Base components for each project type
        component_map = {
            'dashboard': ['Header', 'Sidebar', 'Dashboard', 'Chart', 'Table'],
            'blog': ['Header', 'PostList', 'PostDetail', 'Footer'],
            'portfolio': ['Header', 'Hero', 'ProjectCard', 'Contact', 'Footer'],
            'landing': ['Hero', 'Features', 'CTA', 'Footer'],
            'app': ['Header', 'MainContent', 'Sidebar']
        }
        
        components.extend(component_map.get(project_type, ['App', 'Header', 'Main']))
        
        # Add feature-specific components
        if 'authentication' in features:
            components.extend(['Login', 'Register', 'UserProfile'])
        if 'search' in features:
            components.append('SearchBar')
        if 'forms' in features:
            components.append('Form')
        
        return list(set(components))
    
    def _create_implementation_steps(self, project_type: str, technology: str, features: List[str]) -> List[Dict[str, Any]]:
        """Create detailed implementation steps."""
        steps = [
            {
                'step': 1,
                'title': 'Project Setup',
                'description': f'Initialize {technology} project with required dependencies',
                'estimated_time': '15 minutes'
            },
            {
                'step': 2,
                'title': 'Base Structure',
                'description': f'Create basic {project_type} structure and routing',
                'estimated_time': '30 minutes'
            },
            {
                'step': 3,
                'title': 'Component Development',
                'description': 'Build core components and layouts',
                'estimated_time': '45 minutes'
            },
            {
                'step': 4,
                'title': 'Styling Implementation',
                'description': 'Apply UI styles and responsive design',
                'estimated_time': '30 minutes'
            }
        ]
        
        # Add feature-specific steps
        if 'authentication' in features:
            steps.append({
                'step': len(steps) + 1,
                'title': 'Authentication Setup',
                'description': 'Implement user authentication and authorization',
                'estimated_time': '45 minutes'
            })
        
        if 'database' in features:
            steps.append({
                'step': len(steps) + 1,
                'title': 'Database Integration',
                'description': 'Set up data storage and API connections',
                'estimated_time': '30 minutes'
            })
        
        steps.append({
            'step': len(steps) + 1,
            'title': 'Testing & Optimization',
            'description': 'Test functionality and optimize performance',
            'estimated_time': '20 minutes'
        })
        
        return steps
    
    def _estimate_time(self, complexity: str, feature_count: int) -> str:
        """Estimate total implementation time."""
        base_times = {
            'simple': 90,      # 1.5 hours
            'moderate': 180,   # 3 hours
            'complex': 300     # 5 hours
        }
        
        base_time = base_times[complexity]
        additional_time = feature_count * 20  # 20 minutes per feature
        total_minutes = base_time + additional_time
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _recommend_structure(self, technology: str) -> Dict[str, Any]:
        """Recommend project structure based on technology."""
        structures = {
            'react': {
                'directories': ['src/components', 'src/pages', 'src/hooks', 'src/utils', 'src/styles'],
                'key_files': ['App.tsx', 'index.tsx', 'package.json', 'tailwind.config.js'],
                'build_tool': 'vite'
            },
            'vue': {
                'directories': ['src/components', 'src/views', 'src/router', 'src/store', 'src/assets'],
                'key_files': ['App.vue', 'main.ts', 'package.json', 'vite.config.ts'],
                'build_tool': 'vite'
            },
            'vanilla': {
                'directories': ['src/js', 'src/css', 'src/assets'],
                'key_files': ['index.html', 'style.css', 'script.js'],
                'build_tool': 'none'
            }
        }
        
        return structures.get(technology, structures['react'])
    
    def analyze_patterns(self, text: str) -> Dict[str, List[str]]:
        """Analyze text for various patterns."""
        return {
            'ui_styles': [style for style, keywords in self.ui_patterns.items() 
                         if any(keyword in text.lower() for keyword in keywords)],
            'project_types': [proj_type for proj_type, keywords in self.project_patterns.items() 
                             if any(keyword in text.lower() for keyword in keywords)],
            'technologies': [tech for tech, keywords in self.tech_patterns.items() 
                           if any(keyword in text.lower() for keyword in keywords)],
            'features': [feature for feature, keywords in self.feature_patterns.items() 
                        if any(keyword in text.lower() for keyword in keywords)]
        }