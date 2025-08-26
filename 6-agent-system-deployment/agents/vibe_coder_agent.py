"""
VibeCoderAgent - Generate code files based on technical plans from VibePlannerAgent
"""

import json
from typing import Dict, Any, List, Optional
from agents.vibe_base_agent import VibeBaseAgent
import logging

logger = logging.getLogger(__name__)


class VibeCoderAgent(VibeBaseAgent):
    """Agent for generating actual code files from technical plans."""
    
    def __init__(self):
        super().__init__()
        self.framework_templates = {
            'react': self._get_react_templates(),
            'vue': self._get_vue_templates(),
            'vanilla': self._get_vanilla_templates()
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "code_generation",
            "component_creation",
            "project_scaffolding",
            "typescript_support",
            "styling_integration"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        required_fields = ['technical_requirements', 'vibe_analysis']
        return all(field in input_data for field in required_fields)
    
    def generate_code_from_plan(self, plan: Dict[str, Any], project_id: int) -> Dict[str, Any]:
        """
        MANDATORY IMPLEMENTATION - Generate actual code files
        MUST support: React TypeScript, Vue, Vanilla HTML/CSS/JS
        MUST create: package.json, components, styling, project structure
        """
        if not self.validate_input(plan):
            raise ValueError("Invalid plan structure provided")
        
        tech_requirements = plan['technical_requirements']
        vibe_analysis = plan['vibe_analysis']
        framework = tech_requirements.get('framework', 'react')
        
        generated_files = {}
        
        try:
            # Generate package.json
            generated_files['package.json'] = self._generate_package_json(framework, tech_requirements)
            
            # Generate main app file
            generated_files.update(self._generate_app_files(framework, vibe_analysis, tech_requirements))
            
            # Generate components
            component_files = self._generate_components(
                tech_requirements.get('components', []), 
                framework, 
                vibe_analysis
            )
            generated_files.update(component_files)
            
            # Generate styling
            style_files = self._generate_styles(framework, vibe_analysis, tech_requirements)
            generated_files.update(style_files)
            
            # Generate configuration files
            config_files = self._generate_config_files(framework, tech_requirements)
            generated_files.update(config_files)
            
            return {
                'project_id': project_id,
                'framework': framework,
                'generated_files': generated_files,
                'file_count': len(generated_files),
                'success': True,
                'components_created': len(tech_requirements.get('components', [])),
                'features_implemented': tech_requirements.get('features', [])
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                'project_id': project_id,
                'success': False,
                'error': str(e),
                'generated_files': generated_files
            }
    
    def _generate_package_json(self, framework: str, tech_requirements: Dict[str, Any]) -> str:
        """Generate package.json based on framework and requirements."""
        base_packages = {
            'react': {
                "name": "vibe-generated-app",
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview",
                    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                },
                "devDependencies": {
                    "@types/react": "^18.2.15",
                    "@types/react-dom": "^18.2.7",
                    "@typescript-eslint/eslint-plugin": "^6.0.0",
                    "@typescript-eslint/parser": "^6.0.0",
                    "@vitejs/plugin-react": "^4.0.3",
                    "eslint": "^8.45.0",
                    "eslint-plugin-react-hooks": "^4.6.0",
                    "eslint-plugin-react-refresh": "^0.4.3",
                    "typescript": "^5.0.2",
                    "vite": "^4.4.5"
                }
            },
            'vue': {
                "name": "vibe-generated-vue-app",
                "version": "1.0.0",
                "scripts": {
                    "dev": "vite",
                    "build": "vue-tsc && vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "vue": "^3.3.4"
                },
                "devDependencies": {
                    "@vitejs/plugin-vue": "^4.2.3",
                    "typescript": "^5.0.2",
                    "vite": "^4.4.5",
                    "vue-tsc": "^1.8.5"
                }
            },
            'vanilla': {
                "name": "vibe-generated-vanilla-app",
                "version": "1.0.0",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                },
                "devDependencies": {
                    "vite": "^4.4.5"
                }
            }
        }
        
        package_config = base_packages.get(framework, base_packages['react'])
        
        # Add Tailwind CSS if required
        if tech_requirements.get('styling') == 'tailwind':
            package_config['devDependencies']['tailwindcss'] = '^3.3.3'
            package_config['devDependencies']['autoprefixer'] = '^10.4.14'
            package_config['devDependencies']['postcss'] = '^8.4.27'
        
        # Add feature-specific dependencies
        features = tech_requirements.get('features', [])
        if 'authentication' in features:
            if framework == 'react':
                package_config['dependencies']['@auth0/auth0-react'] = '^2.2.1'
        
        if 'real-time' in features:
            package_config['dependencies']['socket.io-client'] = '^4.7.2'
        
        return json.dumps(package_config, indent=2)
    
    def _generate_app_files(self, framework: str, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> Dict[str, str]:
        """Generate main application files."""
        files = {}
        
        if framework == 'react':
            files['src/App.tsx'] = self._generate_react_app(vibe_analysis, tech_requirements)
            files['src/main.tsx'] = self._generate_react_main()
            files['index.html'] = self._generate_html_template('React Vibe App')
            
        elif framework == 'vue':
            files['src/App.vue'] = self._generate_vue_app(vibe_analysis, tech_requirements)
            files['src/main.ts'] = self._generate_vue_main()
            files['index.html'] = self._generate_html_template('Vue Vibe App')
            
        elif framework == 'vanilla':
            files['index.html'] = self._generate_vanilla_html(vibe_analysis, tech_requirements)
            files['src/script.js'] = self._generate_vanilla_js(vibe_analysis, tech_requirements)
        
        return files
    
    def _generate_react_app(self, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> str:
        """Generate React App.tsx file."""
        components = tech_requirements.get('components', [])
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        
        theme_class = 'dark' if 'dark' in ui_styles else 'light'
        
        imports = ['import React from "react"']
        if tech_requirements.get('styling') == 'tailwind':
            imports.append('import "./index.css"')
        
        # Add component imports
        for component in components:
            imports.append(f'import {component} from "./components/{component}"')
        
        jsx_components = [f'      <{comp} />' for comp in components]
        
        return f'''
{chr(10).join(imports)}

function App() {{
  return (
    <div className="{theme_class} min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4">
{chr(10).join(jsx_components)}
      </div>
    </div>
  )
}}

export default App
'''.strip()
    
    def _generate_react_main(self) -> str:
        """Generate React main.tsx file."""
        return '''
import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''.strip()
    
    def _generate_vue_app(self, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> str:
        """Generate Vue App.vue file."""
        components = tech_requirements.get('components', [])
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        
        theme_class = 'dark' if 'dark' in ui_styles else 'light'
        
        component_imports = []
        component_registrations = []
        component_usage = []
        
        for comp in components:
            component_imports.append(f"import {comp} from './components/{comp}.vue'")
            component_registrations.append(f"    {comp},")
            component_usage.append(f"    <{comp} />")
        
        return f'''
<template>
  <div class="{theme_class} min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="container mx-auto px-4">
{chr(10).join(component_usage)}
    </div>
  </div>
</template>

<script setup lang="ts">
{chr(10).join(component_imports)}
</script>

<style scoped>
</style>
'''.strip()
    
    def _generate_vue_main(self) -> str:
        """Generate Vue main.ts file."""
        return '''
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

createApp(App).mount('#app')
'''.strip()
    
    def _generate_vanilla_html(self, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> str:
        """Generate vanilla HTML file."""
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        project_type = vibe_analysis.get('detected_project_type', 'app')
        
        theme_class = 'dark-theme' if 'dark' in ui_styles else 'light-theme'
        
        return f'''
<!DOCTYPE html>
<html lang="en" class="{theme_class}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Generated {project_type.title()}</title>
    <link rel="stylesheet" href="src/style.css">
</head>
<body>
    <div id="app">
        <header class="header">
            <h1>Welcome to Your {project_type.title()}</h1>
        </header>
        <main class="main-content">
            <p>Your vibe-generated application is ready!</p>
        </main>
    </div>
    <script src="src/script.js"></script>
</body>
</html>
'''.strip()
    
    def _generate_vanilla_js(self, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> str:
        """Generate vanilla JavaScript file."""
        return '''
// Vibe-generated application logic
document.addEventListener('DOMContentLoaded', function() {
    console.log('Vibe app initialized!');
    
    // Add interactivity here
    const app = document.getElementById('app');
    if (app) {
        app.addEventListener('click', function(e) {
            console.log('App clicked:', e.target);
        });
    }
});
'''.strip()
    
    def _generate_components(self, components: List[str], framework: str, vibe_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate component files."""
        files = {}
        
        for component in components:
            if framework == 'react':
                files[f'src/components/{component}.tsx'] = self._generate_react_component(component, vibe_analysis)
            elif framework == 'vue':
                files[f'src/components/{component}.vue'] = self._generate_vue_component(component, vibe_analysis)
            elif framework == 'vanilla':
                files[f'src/components/{component.lower()}.js'] = self._generate_vanilla_component(component, vibe_analysis)
        
        return files
    
    def _generate_react_component(self, component_name: str, vibe_analysis: Dict[str, Any]) -> str:
        """Generate React component."""
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        is_modern = 'modern' in ui_styles
        
        base_classes = 'p-4 ' + ('rounded-lg shadow-sm' if is_modern else 'border')
        
        return f'''
import React from 'react'

interface {component_name}Props {{
  className?: string
}}

const {component_name}: React.FC<{component_name}Props> = ({{ className = '' }}) => {{
  return (
    <div className="{base_classes} {{className}}">
      <h2 className="text-xl font-semibold mb-2">{component_name}</h2>
      <p className="text-gray-600 dark:text-gray-300">
        This is the {component_name} component.
      </p>
    </div>
  )
}}

export default {component_name}
'''.strip()
    
    def _generate_vue_component(self, component_name: str, vibe_analysis: Dict[str, Any]) -> str:
        """Generate Vue component."""
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        is_modern = 'modern' in ui_styles
        
        base_classes = 'p-4 ' + ('rounded-lg shadow-sm' if is_modern else 'border')
        
        return f'''
<template>
  <div :class="['{base_classes}', className]">
    <h2 class="text-xl font-semibold mb-2">{component_name}</h2>
    <p class="text-gray-600 dark:text-gray-300">
      This is the {component_name} component.
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {{
  className?: string
}}

withDefaults(defineProps<Props>(), {{
  className: ''
}})
</script>

<style scoped>
</style>
'''.strip()
    
    def _generate_vanilla_component(self, component_name: str, vibe_analysis: Dict[str, Any]) -> str:
        """Generate vanilla JavaScript component."""
        return f'''
// {component_name} Component
function create{component_name}(container) {{
    const element = document.createElement('div');
    element.className = '{component_name.lower()}-component';
    element.innerHTML = `
        <h2>{component_name}</h2>
        <p>This is the {component_name} component.</p>
    `;
    
    if (container) {{
        container.appendChild(element);
    }}
    
    return element;
}}

export {{ create{component_name} }};
'''.strip()
    
    def _generate_styles(self, framework: str, vibe_analysis: Dict[str, Any], tech_requirements: Dict[str, Any]) -> Dict[str, str]:
        """Generate styling files."""
        files = {}
        
        if tech_requirements.get('styling') == 'tailwind':
            files['src/index.css'] = self._generate_tailwind_css()
            files['tailwind.config.js'] = self._generate_tailwind_config()
            files['postcss.config.js'] = self._generate_postcss_config()
        else:
            if framework == 'vanilla':
                files['src/style.css'] = self._generate_vanilla_css(vibe_analysis)
            else:
                files['src/index.css'] = self._generate_basic_css(vibe_analysis)
        
        return files
    
    def _generate_tailwind_css(self) -> str:
        """Generate Tailwind CSS file."""
        return '''
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: 'Inter', system-ui, sans-serif;
  }
}

@layer components {
  .btn-primary {
    @apply bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded;
  }
}
'''.strip()
    
    def _generate_basic_css(self, vibe_analysis: Dict[str, Any]) -> str:
        """Generate basic CSS styles."""
        ui_styles = vibe_analysis.get('detected_ui_styles', [])
        is_dark = 'dark' in ui_styles
        is_modern = 'modern' in ui_styles
        
        bg_color = '#1a1a1a' if is_dark else '#ffffff'
        text_color = '#ffffff' if is_dark else '#333333'
        border_radius = '8px' if is_modern else '4px'
        
        return f'''
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: {bg_color};
  color: {text_color};
  line-height: 1.6;
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}}

.component {{
  padding: 20px;
  margin: 10px 0;
  border-radius: {border_radius};
  background: {'#2a2a2a' if is_dark else '#f9f9f9'};
}}

h1, h2, h3 {{
  margin-bottom: 15px;
}}

.btn {{
  padding: 10px 20px;
  border: none;
  border-radius: {border_radius};
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}}

.btn-primary {{
  background-color: #3b82f6;
  color: white;
}}

.btn-primary:hover {{
  background-color: #2563eb;
}}
'''.strip()
    
    def _generate_vanilla_css(self, vibe_analysis: Dict[str, Any]) -> str:
        """Generate vanilla CSS with theme support."""
        return self._generate_basic_css(vibe_analysis)
    
    def _generate_config_files(self, framework: str, tech_requirements: Dict[str, Any]) -> Dict[str, str]:
        """Generate configuration files."""
        files = {}
        
        if framework in ['react', 'vue']:
            files['vite.config.ts'] = self._generate_vite_config(framework)
            files['tsconfig.json'] = self._generate_tsconfig(framework)
        
        return files
    
    def _generate_vite_config(self, framework: str) -> str:
        """Generate Vite configuration."""
        plugin = 'react()' if framework == 'react' else 'vue()'
        import_line = '@vitejs/plugin-react' if framework == 'react' else '@vitejs/plugin-vue'
        
        return f'''
import {{ defineConfig }} from 'vite'
import {framework} from '{import_line}'

export default defineConfig({{
  plugins: [{plugin}],
  server: {{
    port: 3000,
    open: true
  }}
}})
'''.strip()
    
    def _generate_tsconfig(self, framework: str) -> str:
        """Generate TypeScript configuration."""
        jsx = '"react-jsx"' if framework == 'react' else '"preserve"'
        
        return f'''
{{
  "compilerOptions": {{
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": {jsx},
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }},
  "include": ["src"],
  "references": [{{ "path": "./tsconfig.node.json" }}]
}}
'''.strip()
    
    def _generate_tailwind_config(self) -> str:
        """Generate Tailwind configuration."""
        return '''
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue}",
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
'''.strip()
    
    def _generate_postcss_config(self) -> str:
        """Generate PostCSS configuration."""
        return '''
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''.strip()
    
    def _generate_html_template(self, title: str) -> str:
        """Generate HTML template."""
        return f'''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''.strip()
    
    def _get_react_templates(self) -> Dict[str, str]:
        """Get React component templates."""
        return {
            'functional': 'React.FC template',
            'class': 'React.Component template',
            'hook': 'Custom hook template'
        }
    
    def _get_vue_templates(self) -> Dict[str, str]:
        """Get Vue component templates."""
        return {
            'composition': 'Composition API template',
            'options': 'Options API template'
        }
    
    def _get_vanilla_templates(self) -> Dict[str, str]:
        """Get vanilla JavaScript templates."""
        return {
            'module': 'ES6 module template',
            'class': 'Class-based component template'
        }