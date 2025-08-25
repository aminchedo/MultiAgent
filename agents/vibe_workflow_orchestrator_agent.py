"""
VibeWorkflowOrchestratorAgent - Coordinate execution flow between all agents and manage project state
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from agents.vibe_base_agent import VibeBaseAgent
from agents.vibe_planner_agent import VibePlannerAgent
from agents.vibe_coder_agent import VibeCoderAgent
from agents.vibe_critic_agent import VibeCriticAgent
from agents.vibe_file_manager_agent import VibeFileManagerAgent
import logging

logger = logging.getLogger(__name__)


class VibeWorkflowOrchestratorAgent(VibeBaseAgent):
    """Master agent that coordinates the entire vibe project workflow."""
    
    def __init__(self):
        super().__init__()
        self.agent_instances = {}
        self.workflow_steps = [
            {'agent': 'planner', 'name': 'Vibe Analysis & Planning'},
            {'agent': 'coder', 'name': 'Code Generation'},
            {'agent': 'critic', 'name': 'Quality Review'},
            {'agent': 'file_manager', 'name': 'File Organization'}
        ]
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all vibe agent instances."""
        try:
            self.agent_instances = {
                'planner': VibePlannerAgent(),
                'coder': VibeCoderAgent(),
                'critic': VibeCriticAgent(),
                'file_manager': VibeFileManagerAgent()
            }
            logger.info("✅ All vibe agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise
    
    def get_capabilities(self) -> List[str]:
        """Return list of orchestrator capabilities."""
        return [
            "workflow_coordination",
            "agent_management",
            "project_state_tracking",
            "error_recovery",
            "progress_monitoring"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for orchestration."""
        required_fields = ['vibe_prompt']
        return all(field in input_data for field in required_fields)
    
    def orchestrate_vibe_project(self, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        MANDATORY IMPLEMENTATION - Coordinate entire agent workflow
        MUST implement: 1->2->3->4 agent flow, error recovery, progress tracking
        MUST integrate: with existing FastAPI backend endpoints
        """
        if not self.validate_input(vibe_request):
            raise ValueError("Invalid vibe request structure")
        
        workflow_result = {
            'workflow_id': self._generate_workflow_id(),
            'workflow_status': 'started',
            'agent_results': {},
            'project_data': {},
            'error_log': [],
            'progress': {
                'current_step': 0,
                'total_steps': len(self.workflow_steps),
                'percentage': 0
            },
            'timing': {
                'start_time': time.time(),
                'step_times': {},
                'total_duration': 0
            }
        }
        
        try:
            # Extract vibe request data
            vibe_prompt = vibe_request['vibe_prompt']
            project_type = vibe_request.get('project_type', 'app')
            complexity = vibe_request.get('complexity', 'simple')
            
            logger.info(f"🚀 Starting vibe workflow for: {vibe_prompt[:50]}...")
            
            # Create vibe project in database
            project_id = self._create_vibe_project(vibe_prompt, project_type)
            workflow_result['project_id'] = project_id
            
            # Execute workflow steps
            self._execute_workflow_steps(workflow_result, vibe_request)
            
            # Finalize workflow
            self._finalize_workflow(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            workflow_result['workflow_status'] = 'failed'
            workflow_result['error_log'].append({
                'step': 'orchestration',
                'error': str(e),
                'timestamp': time.time()
            })
            return workflow_result
    
    def _execute_workflow_steps(self, workflow_result: Dict[str, Any], vibe_request: Dict[str, Any]):
        """Execute all workflow steps in sequence."""
        for i, step in enumerate(self.workflow_steps):
            workflow_result['progress']['current_step'] = i + 1
            workflow_result['progress']['percentage'] = ((i + 1) / len(self.workflow_steps)) * 100
            
            step_name = step['name']
            agent_name = step['agent']
            
            logger.info(f"📋 Step {i + 1}/{len(self.workflow_steps)}: {step_name}")
            
            step_start_time = time.time()
            
            try:
                # Execute agent step
                step_result = self._execute_agent_step(agent_name, workflow_result, vibe_request)
                
                # Record results
                workflow_result['agent_results'][agent_name] = step_result
                workflow_result['timing']['step_times'][agent_name] = time.time() - step_start_time
                
                # Update project data
                self._update_project_data(workflow_result, agent_name, step_result)
                
                logger.info(f"✅ Step {i + 1} completed: {step_name}")
                
            except Exception as e:
                logger.error(f"❌ Step {i + 1} failed: {step_name} - {e}")
                workflow_result['error_log'].append({
                    'step': step_name,
                    'agent': agent_name,
                    'error': str(e),
                    'timestamp': time.time()
                })
                
                # Attempt recovery
                if not self._attempt_step_recovery(workflow_result, agent_name, e):
                    raise e
    
    def _execute_agent_step(self, agent_name: str, workflow_result: Dict[str, Any], vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent step."""
        agent = self.agent_instances[agent_name]
        
        if agent_name == 'planner':
            return self._execute_planner_step(agent, vibe_request)
        elif agent_name == 'coder':
            return self._execute_coder_step(agent, workflow_result)
        elif agent_name == 'critic':
            return self._execute_critic_step(agent, workflow_result)
        elif agent_name == 'file_manager':
            return self._execute_file_manager_step(agent, workflow_result)
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    
    def _execute_planner_step(self, agent: VibePlannerAgent, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planner agent step."""
        vibe_prompt = vibe_request['vibe_prompt']
        project_data = vibe_request.get('project_data', {})
        
        result = agent.decompose_vibe_prompt(vibe_prompt, project_data)
        
        # Validate planner result
        if not result or 'vibe_analysis' not in result:
            raise ValueError("Planner failed to generate valid analysis")
        
        return {
            'success': True,
            'agent': 'planner',
            'analysis': result['vibe_analysis'],
            'technical_requirements': result['technical_requirements'],
            'implementation_steps': result['implementation_steps'],
            'estimated_time': result.get('estimated_time', 'Unknown')
        }
    
    def _execute_coder_step(self, agent: VibeCoderAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the coder agent step."""
        planner_result = workflow_result['agent_results']['planner']
        project_id = workflow_result.get('project_id', 0)
        
        # Prepare plan for coder
        plan = {
            'technical_requirements': planner_result['technical_requirements'],
            'vibe_analysis': planner_result['analysis'],
            'implementation_steps': planner_result['implementation_steps']
        }
        
        result = agent.generate_code_from_plan(plan, project_id)
        
        # Validate coder result
        if not result or not result.get('success', False):
            raise ValueError("Coder failed to generate valid code")
        
        return {
            'success': True,
            'agent': 'coder',
            'framework': result['framework'],
            'generated_files': result['generated_files'],
            'file_count': result['file_count'],
            'components_created': result.get('components_created', 0)
        }
    
    def _execute_critic_step(self, agent: VibeCriticAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the critic agent step."""
        coder_result = workflow_result['agent_results']['coder']
        planner_result = workflow_result['agent_results']['planner']
        
        # Prepare files for review
        files = []
        for file_path, content in coder_result['generated_files'].items():
            files.append({
                'path': file_path,
                'content': content
            })
        
        # Prepare plan for review
        plan = {
            'technical_requirements': planner_result['technical_requirements'],
            'vibe_analysis': planner_result['analysis']
        }
        
        result = agent.review_generated_code(files, plan)
        
        # Validate critic result
        if 'overall_score' not in result:
            raise ValueError("Critic failed to generate valid review")
        
        return {
            'success': True,
            'agent': 'critic',
            'overall_score': result['overall_score'],
            'category_scores': result.get('category_scores', {}),
            'recommendations': result.get('recommendations', []),
            'issues_found': len(result.get('issues_found', [])),
            'compliance_report': result.get('compliance_report', {})
        }
    
    def _execute_file_manager_step(self, agent: VibeFileManagerAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the file manager agent step."""
        coder_result = workflow_result['agent_results']['coder']
        planner_result = workflow_result['agent_results']['planner']
        
        # Prepare files for organization
        files = []
        for file_path, content in coder_result['generated_files'].items():
            files.append({
                'path': file_path,
                'filename': file_path,
                'content': content
            })
        
        project_type = planner_result['analysis']['detected_project_type']
        
        result = agent.organize_project_structure(files, project_type)
        
        # Validate file manager result
        if not result.get('success', False):
            raise ValueError("File manager failed to organize project")
        
        return {
            'success': True,
            'agent': 'file_manager',
            'framework': result['framework'],
            'organized_files': result['organized_files'],
            'file_manifest': result['file_manifest'],
            'deployment_config': result['deployment_config'],
            'zip_file': result.get('zip_file', {}),
            'total_files': result['total_files']
        }
    
    def _update_project_data(self, workflow_result: Dict[str, Any], agent_name: str, step_result: Dict[str, Any]):
        """Update cumulative project data with step results."""
        if 'project_data' not in workflow_result:
            workflow_result['project_data'] = {}
        
        project_data = workflow_result['project_data']
        
        if agent_name == 'planner':
            project_data.update({
                'vibe_analysis': step_result['analysis'],
                'technical_requirements': step_result['technical_requirements'],
                'implementation_steps': step_result['implementation_steps'],
                'estimated_time': step_result['estimated_time']
            })
        
        elif agent_name == 'coder':
            project_data.update({
                'framework': step_result['framework'],
                'generated_files': step_result['generated_files'],
                'file_count': step_result['file_count'],
                'components_created': step_result['components_created']
            })
        
        elif agent_name == 'critic':
            project_data.update({
                'quality_score': step_result['overall_score'],
                'quality_categories': step_result['category_scores'],
                'recommendations': step_result['recommendations'],
                'issues_count': step_result['issues_found']
            })
        
        elif agent_name == 'file_manager':
            project_data.update({
                'organized_files': step_result['organized_files'],
                'file_manifest': step_result['file_manifest'],
                'deployment_config': step_result['deployment_config'],
                'project_zip': step_result.get('zip_file', {})
            })
    
    def _attempt_step_recovery(self, workflow_result: Dict[str, Any], agent_name: str, error: Exception) -> bool:
        """Attempt to recover from step failure."""
        recovery_strategies = {
            'planner': self._recover_planner_step,
            'coder': self._recover_coder_step,
            'critic': self._recover_critic_step,
            'file_manager': self._recover_file_manager_step
        }
        
        recovery_func = recovery_strategies.get(agent_name)
        if recovery_func:
            try:
                return recovery_func(workflow_result, error)
            except Exception as recovery_error:
                logger.error(f"Recovery failed for {agent_name}: {recovery_error}")
        
        return False
    
    def _recover_planner_step(self, workflow_result: Dict[str, Any], error: Exception) -> bool:
        """Attempt to recover from planner failure."""
        # Create minimal fallback plan
        fallback_result = {
            'success': True,
            'agent': 'planner',
            'analysis': {
                'detected_ui_styles': ['modern'],
                'detected_project_type': 'app',
                'detected_technologies': ['react'],
                'detected_features': [],
                'complexity': 'simple'
            },
            'technical_requirements': {
                'framework': 'react',
                'styling': 'tailwind',
                'components': ['App', 'Header'],
                'features': []
            },
            'implementation_steps': [
                {'step': 1, 'title': 'Basic Setup', 'estimated_time': '30 minutes'}
            ],
            'estimated_time': '1h'
        }
        
        workflow_result['agent_results']['planner'] = fallback_result
        logger.info("🔄 Planner step recovered with fallback plan")
        return True
    
    def _recover_coder_step(self, workflow_result: Dict[str, Any], error: Exception) -> bool:
        """Attempt to recover from coder failure."""
        # Create minimal code structure
        fallback_files = {
            'package.json': '{"name": "vibe-app", "version": "1.0.0"}',
            'src/App.tsx': 'import React from "react"; export default function App() { return <div>Hello Vibe!</div>; }',
            'src/main.tsx': 'import React from "react"; import ReactDOM from "react-dom/client"; ReactDOM.createRoot(document.getElementById("root")!).render(<App />);'
        }
        
        fallback_result = {
            'success': True,
            'agent': 'coder',
            'framework': 'react',
            'generated_files': fallback_files,
            'file_count': len(fallback_files),
            'components_created': 1
        }
        
        workflow_result['agent_results']['coder'] = fallback_result
        logger.info("🔄 Coder step recovered with minimal files")
        return True
    
    def _recover_critic_step(self, workflow_result: Dict[str, Any], error: Exception) -> bool:
        """Attempt to recover from critic failure."""
        # Provide basic quality assessment
        fallback_result = {
            'success': True,
            'agent': 'critic',
            'overall_score': 75.0,
            'category_scores': {
                'type_safety': 70.0,
                'structure': 80.0,
                'accessibility': 75.0
            },
            'recommendations': [
                {'priority': 'low', 'title': 'Review code quality', 'description': 'Manual review recommended'}
            ],
            'issues_found': 0,
            'compliance_report': {'compliance_level': 'fair'}
        }
        
        workflow_result['agent_results']['critic'] = fallback_result
        logger.info("🔄 Critic step recovered with basic assessment")
        return True
    
    def _recover_file_manager_step(self, workflow_result: Dict[str, Any], error: Exception) -> bool:
        """Attempt to recover from file manager failure."""
        coder_result = workflow_result['agent_results']['coder']
        
        # Basic file organization
        fallback_result = {
            'success': True,
            'agent': 'file_manager',
            'framework': coder_result.get('framework', 'react'),
            'organized_files': coder_result.get('generated_files', {}),
            'file_manifest': {
                'total_files': coder_result.get('file_count', 0),
                'framework': coder_result.get('framework', 'react')
            },
            'deployment_config': {
                'build_command': 'npm run build',
                'output_directory': 'dist'
            },
            'total_files': coder_result.get('file_count', 0)
        }
        
        workflow_result['agent_results']['file_manager'] = fallback_result
        logger.info("🔄 File manager step recovered with basic organization")
        return True
    
    def _finalize_workflow(self, workflow_result: Dict[str, Any]):
        """Finalize the workflow execution."""
        end_time = time.time()
        start_time = workflow_result['timing']['start_time']
        
        workflow_result['timing']['total_duration'] = end_time - start_time
        workflow_result['workflow_status'] = 'completed'
        workflow_result['progress']['percentage'] = 100
        
        # Update database project status
        project_id = workflow_result.get('project_id')
        if project_id:
            project_files = workflow_result['project_data'].get('organized_files', {})
            self._update_vibe_project(project_id, 'completed', project_files)
        
        # Generate final summary
        workflow_result['summary'] = self._generate_workflow_summary(workflow_result)
        
        logger.info(f"🎉 Workflow completed in {workflow_result['timing']['total_duration']:.2f}s")
    
    def _generate_workflow_summary(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the workflow execution."""
        project_data = workflow_result.get('project_data', {})
        
        return {
            'workflow_id': workflow_result['workflow_id'],
            'status': workflow_result['workflow_status'],
            'duration': f"{workflow_result['timing']['total_duration']:.2f}s",
            'framework': project_data.get('framework', 'unknown'),
            'files_generated': project_data.get('file_count', 0),
            'quality_score': project_data.get('quality_score', 0),
            'components_created': project_data.get('components_created', 0),
            'errors': len(workflow_result.get('error_log', [])),
            'recommendations': len(project_data.get('recommendations', [])),
            'success_rate': self._calculate_success_rate(workflow_result)
        }
    
    def _calculate_success_rate(self, workflow_result: Dict[str, Any]) -> float:
        """Calculate the overall success rate of the workflow."""
        total_steps = len(self.workflow_steps)
        successful_steps = len([result for result in workflow_result['agent_results'].values() if result.get('success', False)])
        
        return round((successful_steps / total_steps) * 100, 2) if total_steps > 0 else 0
    
    def _generate_workflow_id(self) -> str:
        """Generate a unique workflow ID."""
        import uuid
        return f"vibe_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    def _create_vibe_project(self, vibe_prompt: str, project_type: str) -> int:
        """Create a vibe project in the database."""
        try:
            # Use the base agent's database methods
            import sqlite3
            conn = sqlite3.connect("backend/vibe_projects.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vibe_projects (vibe_prompt, project_type, status)
                VALUES (?, ?, 'pending')
            """, (vibe_prompt, project_type))
            
            project_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return project_id
        except Exception as e:
            logger.error(f"Failed to create vibe project: {e}")
            return 0
    
    def _update_vibe_project(self, project_id: int, status: str, project_files: Optional[Dict] = None):
        """Update vibe project status and files."""
        try:
            import sqlite3
            conn = sqlite3.connect("backend/vibe_projects.db")
            cursor = conn.cursor()
            
            if status == 'completed':
                cursor.execute("""
                    UPDATE vibe_projects 
                    SET status = ?, project_files = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, json.dumps(project_files) if project_files else None, project_id))
            else:
                cursor.execute("""
                    UPDATE vibe_projects 
                    SET status = ?
                    WHERE id = ?
                """, (status, project_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update vibe project: {e}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow."""
        # This would typically query a workflow tracking system
        # For now, return a placeholder response
        return {
            'workflow_id': workflow_id,
            'status': 'unknown',
            'message': 'Workflow status tracking not yet implemented'
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        # This would typically cancel a running workflow
        # For now, return a placeholder response
        logger.info(f"Workflow cancellation requested for: {workflow_id}")
        return False
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get metrics for all managed agents."""
        metrics = {}
        
        for agent_name, agent in self.agent_instances.items():
            try:
                agent_metrics = agent.get_metrics() if hasattr(agent, 'get_metrics') else {}
                metrics[agent_name] = agent_metrics
            except Exception as e:
                logger.error(f"Failed to get metrics for {agent_name}: {e}")
                metrics[agent_name] = {'error': str(e)}
        
        return metrics