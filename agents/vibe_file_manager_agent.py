"""
VibeFileManagerAgent - Create and manage project directory structures and file organization
"""

import os
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from agents.vibe_base_agent import VibeBaseAgent
import logging

logger = logging.getLogger(__name__)


class VibeFileManagerAgent(VibeBaseAgent):
    """Agent for organizing project structures and managing files."""
    
    def __init__(self):
        super().__init__()
        self.project_structures = {
            'react': {
                'directories': [
                    'src/components',
                    'src/pages', 
                    'src/hooks',
                    'src/utils',
                    'src/types',
                    'src/styles',
                    'public'
                ],
                'root_files': ['package.json', 'tsconfig.json', 'vite.config.ts', 'index.html'],
                'src_files': ['App.tsx', 'main.tsx', 'index.css']
            },
            'vue': {
                'directories': [
                    'src/components',
                    'src/views',
                    'src/router',
                    'src/store',
                    'src/composables',
                    'src/types',
                    'src/assets',
                    'public'
                ],
                'root_files': ['package.json', 'tsconfig.json', 'vite.config.ts', 'index.html'],
                'src_files': ['App.vue', 'main.ts', 'style.css']
            },
            'vanilla': {
                'directories': [
                    'src/js',
                    'src/css',
                    'src/assets',
                    'src/components'
                ],
                'root_files': ['package.json', 'index.html'],
                'src_files': ['script.js', 'style.css']
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "directory_structure_creation",
            "file_organization", 
            "project_optimization",
            "zip_file_generation",
            "deployment_preparation"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        required_fields = ['files', 'project_type']
        return all(field in input_data for field in required_fields)
    
    def organize_project_structure(self, files: List[Dict], project_type: str) -> Dict[str, Any]:
        """
        MANDATORY IMPLEMENTATION - Create proper directory structures
        MUST handle: React/Vue/Vanilla structures, file naming, optimization
        MUST return: organized project structure, file manifest, deployment config
        """
        if not self.validate_input({'files': files, 'project_type': project_type}):
            raise ValueError("Invalid input data for file organization")
        
        try:
            # Determine framework from project type or files
            framework = self._detect_framework(files, project_type)
            
            # Create organized structure
            organized_structure = self._create_project_structure(framework)
            
            # Organize files into structure
            organized_files = self._organize_files_by_structure(files, organized_structure, framework)
            
            # Generate file manifest
            file_manifest = self._generate_file_manifest(organized_files, framework)
            
            # Create deployment configuration
            deployment_config = self._generate_deployment_config(framework, organized_files)
            
            # Optimize file organization
            optimization_report = self._optimize_file_organization(organized_files, framework)
            
            # Generate project ZIP
            zip_info = self._create_project_zip(organized_files, framework)
            
            return {
                'success': True,
                'framework': framework,
                'project_structure': organized_structure,
                'organized_files': organized_files,
                'file_manifest': file_manifest,
                'deployment_config': deployment_config,
                'optimization_report': optimization_report,
                'zip_file': zip_info,
                'total_files': len(organized_files),
                'directory_count': len(organized_structure['directories'])
            }
            
        except Exception as e:
            logger.error(f"File organization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'framework': framework if 'framework' in locals() else 'unknown'
            }
    
    def _detect_framework(self, files: List[Dict], project_type: str) -> str:
        """Detect the framework from files and project type."""
        file_extensions = set()
        file_names = set()
        
        for file_data in files:
            file_path = file_data.get('path', file_data.get('filename', ''))
            if file_path:
                file_names.add(os.path.basename(file_path))
                if '.' in file_path:
                    file_extensions.add(file_path.split('.')[-1])
        
        # Check for framework-specific indicators
        if any(name.endswith('.tsx') or name.endswith('.jsx') for name in file_names) or 'tsx' in file_extensions or 'jsx' in file_extensions:
            return 'react'
        elif any(name.endswith('.vue') for name in file_names) or 'vue' in file_extensions:
            return 'vue'
        elif 'App.tsx' in file_names or 'main.tsx' in file_names:
            return 'react'
        elif 'App.vue' in file_names or 'main.ts' in file_names:
            return 'vue'
        else:
            return 'vanilla'
    
    def _create_project_structure(self, framework: str) -> Dict[str, Any]:
        """Create the base project structure for the framework."""
        structure_template = self.project_structures.get(framework, self.project_structures['react'])
        
        return {
            'framework': framework,
            'directories': structure_template['directories'],
            'root_files': structure_template['root_files'],
            'src_files': structure_template['src_files'],
            'structure_type': 'standard'
        }
    
    def _organize_files_by_structure(self, files: List[Dict], structure: Dict[str, Any], framework: str) -> Dict[str, Dict[str, Any]]:
        """Organize files according to the project structure."""
        organized_files = {}
        
        for file_data in files:
            original_path = file_data.get('path', file_data.get('filename', ''))
            content = file_data.get('content', '')
            
            if not original_path:
                continue
                
            # Determine the proper path for this file
            new_path = self._determine_file_path(original_path, content, framework)
            
            organized_files[new_path] = {
                'content': content,
                'original_path': original_path,
                'size': len(content),
                'type': self._get_file_type(new_path),
                'category': self._get_file_category(new_path, framework)
            }
        
        # Add missing essential files
        organized_files.update(self._add_missing_essential_files(organized_files, framework))
        
        return organized_files
    
    def _determine_file_path(self, original_path: str, content: str, framework: str) -> str:
        """Determine the proper path for a file based on its content and type."""
        filename = os.path.basename(original_path)
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        
        # Root level files
        if filename in ['package.json', 'tsconfig.json', 'vite.config.ts', 'vite.config.js', 
                       'index.html', 'tailwind.config.js', 'postcss.config.js']:
            return filename
        
        # Framework-specific main files
        if framework == 'react':
            if filename in ['App.tsx', 'App.jsx', 'main.tsx', 'main.jsx', 'index.css']:
                return f'src/{filename}'
            elif filename.endswith(('.tsx', '.jsx')) and self._is_component_file(content):
                component_name = filename.replace('.tsx', '').replace('.jsx', '')
                return f'src/components/{component_name}.tsx' if framework == 'react' else f'src/components/{filename}'
            elif filename.endswith(('.ts', '.js')) and self._is_utility_file(content):
                return f'src/utils/{filename}'
            elif filename.endswith(('.ts', '.tsx')) and 'interface' in content:
                return f'src/types/{filename}'
        
        elif framework == 'vue':
            if filename in ['App.vue', 'main.ts', 'main.js', 'style.css']:
                return f'src/{filename}'
            elif filename.endswith('.vue') and self._is_component_file(content):
                return f'src/components/{filename}'
            elif filename.endswith(('.ts', '.js')) and self._is_utility_file(content):
                return f'src/composables/{filename}'
        
        elif framework == 'vanilla':
            if filename.endswith(('.js', '.ts')):
                return f'src/js/{filename}'
            elif filename.endswith('.css'):
                return f'src/css/{filename}'
        
        # CSS files
        if file_extension in ['css', 'scss', 'sass']:
            return f'src/styles/{filename}'
        
        # Asset files
        if file_extension in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico']:
            return f'public/{filename}' if framework in ['react', 'vue'] else f'src/assets/{filename}'
        
        # Default placement
        return f'src/{filename}'
    
    def _is_component_file(self, content: str) -> bool:
        """Check if file content indicates it's a component."""
        component_indicators = [
            'export default',
            'function Component',
            'const Component',
            'React.FC',
            'defineComponent',
            'export { default }'
        ]
        return any(indicator in content for indicator in component_indicators)
    
    def _is_utility_file(self, content: str) -> bool:
        """Check if file content indicates it's a utility file."""
        utility_indicators = [
            'export function',
            'export const',
            'export class',
            'utility',
            'helper',
            'utils'
        ]
        return any(indicator in content for indicator in utility_indicators)
    
    def _get_file_type(self, file_path: str) -> str:
        """Get the type of file based on its extension."""
        extension = file_path.split('.')[-1] if '.' in file_path else ''
        
        type_map = {
            'tsx': 'typescript-react',
            'jsx': 'javascript-react', 
            'ts': 'typescript',
            'js': 'javascript',
            'vue': 'vue-component',
            'css': 'stylesheet',
            'scss': 'sass',
            'sass': 'sass',
            'html': 'markup',
            'json': 'configuration',
            'md': 'documentation',
            'png': 'image',
            'jpg': 'image',
            'svg': 'vector-image'
        }
        
        return type_map.get(extension, 'unknown')
    
    def _get_file_category(self, file_path: str, framework: str) -> str:
        """Get the category of file based on its location and purpose."""
        if file_path in ['package.json', 'tsconfig.json', 'vite.config.ts', 'tailwind.config.js']:
            return 'configuration'
        elif 'components' in file_path:
            return 'component'
        elif 'utils' in file_path or 'composables' in file_path:
            return 'utility'
        elif 'styles' in file_path or file_path.endswith('.css'):
            return 'styling'
        elif 'types' in file_path:
            return 'type-definition'
        elif file_path.startswith('public/'):
            return 'asset'
        elif file_path in ['src/App.tsx', 'src/App.vue', 'src/main.tsx', 'src/main.ts']:
            return 'entry-point'
        else:
            return 'source'
    
    def _add_missing_essential_files(self, organized_files: Dict[str, Dict[str, Any]], framework: str) -> Dict[str, Dict[str, Any]]:
        """Add missing essential files for the framework."""
        missing_files = {}
        
        # Check for essential files
        essential_files = {
            'react': {
                'README.md': self._generate_readme_content(framework),
                '.gitignore': self._generate_gitignore_content(framework),
                'src/index.css': '/* Global styles */' if 'src/index.css' not in organized_files else None
            },
            'vue': {
                'README.md': self._generate_readme_content(framework),
                '.gitignore': self._generate_gitignore_content(framework),
                'src/style.css': '/* Global styles */' if 'src/style.css' not in organized_files else None
            },
            'vanilla': {
                'README.md': self._generate_readme_content(framework),
                '.gitignore': self._generate_gitignore_content(framework)
            }
        }
        
        framework_essentials = essential_files.get(framework, essential_files['react'])
        
        for file_path, content in framework_essentials.items():
            if content and file_path not in organized_files:
                missing_files[file_path] = {
                    'content': content,
                    'original_path': file_path,
                    'size': len(content),
                    'type': self._get_file_type(file_path),
                    'category': 'documentation' if file_path.endswith('.md') else 'configuration'
                }
        
        return missing_files
    
    def _generate_readme_content(self, framework: str) -> str:
        """Generate README.md content for the project."""
        return f"""# Vibe Generated {framework.title()} Project

This project was generated using the Vibe Coding Platform.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

- `src/components/` - Reusable components
- `src/styles/` - CSS and styling files
{'- `src/utils/` - Utility functions' if framework == 'react' else ''}
{'- `src/composables/` - Vue composables' if framework == 'vue' else ''}
{'- `src/types/` - TypeScript type definitions' if framework in ['react', 'vue'] else ''}

## Features

- Modern {framework.title()} setup
- TypeScript support
- Tailwind CSS styling
- Responsive design
- Development server with hot reload

## Contributing

Feel free to customize this project to fit your needs!
"""
    
    def _generate_gitignore_content(self, framework: str) -> str:
        """Generate .gitignore content for the project."""
        return """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production builds
/dist
/build

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
logs
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity
"""
    
    def _generate_file_manifest(self, organized_files: Dict[str, Dict[str, Any]], framework: str) -> Dict[str, Any]:
        """Generate a manifest of all project files."""
        categories = {}
        total_size = 0
        
        for file_path, file_info in organized_files.items():
            category = file_info['category']
            if category not in categories:
                categories[category] = {
                    'files': [],
                    'count': 0,
                    'total_size': 0
                }
            
            categories[category]['files'].append({
                'path': file_path,
                'type': file_info['type'],
                'size': file_info['size']
            })
            categories[category]['count'] += 1
            categories[category]['total_size'] += file_info['size']
            total_size += file_info['size']
        
        return {
            'framework': framework,
            'total_files': len(organized_files),
            'total_size': total_size,
            'categories': categories,
            'structure_valid': self._validate_project_structure(organized_files, framework),
            'generated_at': self._get_current_timestamp()
        }
    
    def _generate_deployment_config(self, framework: str, organized_files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate deployment configuration."""
        config = {
            'framework': framework,
            'build_command': self._get_build_command(framework),
            'dev_command': self._get_dev_command(framework),
            'output_directory': self._get_output_directory(framework),
            'public_directory': self._get_public_directory(framework),
            'environment_variables': self._get_env_variables(framework),
            'deployment_platforms': self._get_deployment_platforms(framework)
        }
        
        # Add Vercel configuration
        if framework in ['react', 'vue']:
            config['vercel'] = {
                'buildCommand': config['build_command'],
                'outputDirectory': config['output_directory'],
                'installCommand': 'npm install',
                'framework': framework
            }
        
        # Add Netlify configuration
        config['netlify'] = {
            'build': {
                'command': config['build_command'],
                'publish': config['output_directory']
            }
        }
        
        return config
    
    def _get_build_command(self, framework: str) -> str:
        """Get the build command for the framework."""
        commands = {
            'react': 'npm run build',
            'vue': 'npm run build', 
            'vanilla': 'npm run build'
        }
        return commands.get(framework, 'npm run build')
    
    def _get_dev_command(self, framework: str) -> str:
        """Get the development command for the framework."""
        return 'npm run dev'
    
    def _get_output_directory(self, framework: str) -> str:
        """Get the output directory for the framework."""
        return 'dist'
    
    def _get_public_directory(self, framework: str) -> str:
        """Get the public directory for the framework."""
        return 'public' if framework in ['react', 'vue'] else 'src/assets'
    
    def _get_env_variables(self, framework: str) -> List[str]:
        """Get recommended environment variables."""
        return [
            'NODE_ENV',
            'VITE_API_URL',
            'VITE_APP_TITLE'
        ]
    
    def _get_deployment_platforms(self, framework: str) -> List[Dict[str, str]]:
        """Get recommended deployment platforms."""
        return [
            {
                'name': 'Vercel',
                'url': 'https://vercel.com',
                'recommended': True,
                'supports_framework': True
            },
            {
                'name': 'Netlify', 
                'url': 'https://netlify.com',
                'recommended': True,
                'supports_framework': True
            },
            {
                'name': 'GitHub Pages',
                'url': 'https://pages.github.com',
                'recommended': False,
                'supports_framework': framework == 'vanilla'
            }
        ]
    
    def _optimize_file_organization(self, organized_files: Dict[str, Dict[str, Any]], framework: str) -> Dict[str, Any]:
        """Analyze and optimize file organization."""
        optimization_report = {
            'issues': [],
            'suggestions': [],
            'score': 100,
            'optimizations_applied': []
        }
        
        # Check for proper component organization
        component_files = [path for path, info in organized_files.items() if info['category'] == 'component']
        if len(component_files) > 5 and not any('components' in path for path in component_files):
            optimization_report['issues'].append({
                'type': 'organization',
                'message': 'Components should be organized in a components directory',
                'severity': 'medium'
            })
            optimization_report['score'] -= 15
        
        # Check for CSS organization
        css_files = [path for path, info in organized_files.items() if info['type'] in ['stylesheet', 'sass']]
        if len(css_files) > 2 and not any('styles' in path for path in css_files):
            optimization_report['suggestions'].append({
                'type': 'organization',
                'message': 'Consider organizing CSS files in a styles directory',
                'impact': 'low'
            })
        
        # Check for utility organization
        utility_files = [path for path, info in organized_files.items() if info['category'] == 'utility']
        if len(utility_files) > 3:
            optimization_report['suggestions'].append({
                'type': 'organization',
                'message': 'Consider creating index files for utilities for easier imports',
                'impact': 'medium'
            })
        
        # Check file sizes
        large_files = [path for path, info in organized_files.items() if info['size'] > 10000]
        if large_files:
            optimization_report['issues'].append({
                'type': 'performance',
                'message': f'{len(large_files)} files are larger than 10KB',
                'severity': 'low',
                'files': large_files[:3]
            })
        
        return optimization_report
    
    def _validate_project_structure(self, organized_files: Dict[str, Dict[str, Any]], framework: str) -> bool:
        """Validate that the project structure is correct."""
        required_files = {
            'react': ['package.json', 'src/App.tsx', 'src/main.tsx'],
            'vue': ['package.json', 'src/App.vue', 'src/main.ts'],
            'vanilla': ['package.json', 'index.html', 'src/script.js']
        }
        
        framework_required = required_files.get(framework, required_files['react'])
        
        for required_file in framework_required:
            if required_file not in organized_files:
                return False
        
        return True
    
    def _create_project_zip(self, organized_files: Dict[str, Dict[str, Any]], framework: str) -> Dict[str, Any]:
        """Create a ZIP file of the organized project."""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            project_name = f'vibe-{framework}-project'
            project_path = os.path.join(temp_dir, project_name)
            
            # Create project directory structure
            os.makedirs(project_path, exist_ok=True)
            
            # Write all files
            for file_path, file_info in organized_files.items():
                full_path = os.path.join(project_path, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
            
            # Create ZIP file
            zip_path = os.path.join(temp_dir, f'{project_name}.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_path)
                        zipf.write(file_path, arcname)
            
            # Get zip file stats
            zip_size = os.path.getsize(zip_path)
            
            return {
                'success': True,
                'zip_path': zip_path,
                'zip_size': zip_size,
                'project_name': project_name,
                'temp_directory': temp_dir
            }
            
        except Exception as e:
            logger.error(f"Failed to create project ZIP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def cleanup_temp_files(self, zip_info: Dict[str, Any]) -> bool:
        """Clean up temporary files created during ZIP generation."""
        try:
            if zip_info.get('temp_directory') and os.path.exists(zip_info['temp_directory']):
                shutil.rmtree(zip_info['temp_directory'])
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
        return False
    
    def get_project_stats(self, organized_files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the organized project."""
        stats = {
            'total_files': len(organized_files),
            'total_size': sum(info['size'] for info in organized_files.values()),
            'file_types': {},
            'categories': {},
            'largest_files': []
        }
        
        # Count file types and categories
        for file_path, file_info in organized_files.items():
            file_type = file_info['type']
            category = file_info['category']
            
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        # Find largest files
        sorted_files = sorted(organized_files.items(), key=lambda x: x[1]['size'], reverse=True)
        stats['largest_files'] = [
            {'path': path, 'size': info['size'], 'type': info['type']} 
            for path, info in sorted_files[:5]
        ]
        
        return stats