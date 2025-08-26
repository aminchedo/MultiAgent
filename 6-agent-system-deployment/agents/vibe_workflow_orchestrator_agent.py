"""
VibeWorkflowOrchestratorAgent - Coordinate execution flow between all agents and manage project state
Enhanced with real-time WebSocket updates and production error handling
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable
from agents.vibe_base_agent import VibeBaseAgent
from agents.vibe_planner_agent import VibePlannerAgent
from agents.vibe_coder_agent import VibeCoderAgent
from agents.vibe_critic_agent import VibeCriticAgent
from agents.vibe_file_manager_agent import VibeFileManagerAgent
from agents.vibe_qa_validator_agent import VibeQAValidatorAgent
import logging
import traceback
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    IDLE = "idle"
    STARTING = "starting"
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    ORGANIZING = "organizing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentTask:
    """Agent task definition"""
    agent_name: str
    display_name: str
    description: str
    timeout: int = 300
    retries: int = 2

class VibeWorkflowOrchestratorAgent(VibeBaseAgent):
    """Master agent that coordinates the entire vibe project workflow with real-time updates."""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        super().__init__()
        self.progress_callback = progress_callback
        self.current_job_id = None
        self.workflow_status = WorkflowStatus.IDLE
        
        # Define enhanced 6-agent workflow steps
        self.workflow_steps = [
            AgentTask(
                agent_name='planner',
                display_name='Project Planner',
                description='Analyzing requirements and creating project structure',
                timeout=120,
                retries=2
            ),
            AgentTask(
                agent_name='coder',
                display_name='Code Generator',
                description='Generating production-ready code files',
                timeout=300,
                retries=3
            ),
            AgentTask(
                agent_name='critic',
                display_name='Code Reviewer',
                description='Reviewing code quality and best practices',
                timeout=180,
                retries=2
            ),
            AgentTask(
                agent_name='file_manager',
                display_name='File Manager',
                description='Organizing project structure and creating deployment config',
                timeout=120,
                retries=2
            ),
            AgentTask(
                agent_name='qa_validator',
                display_name='QA Validator',
                description='Performing comprehensive testing and quality validation',
                timeout=240,
                retries=3
            )
        ]
        
        self.agent_instances = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all 6 vibe agent instances with error handling."""
        try:
            self.agent_instances = {
                'planner': VibePlannerAgent(),
                'coder': VibeCoderAgent(),
                'critic': VibeCriticAgent(),
                'file_manager': VibeFileManagerAgent(),
                'qa_validator': VibeQAValidatorAgent()
            }
            logger.info("✅ All 6 vibe agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise RuntimeError(f"Agent initialization failed: {e}")
    
    def get_capabilities(self) -> List[str]:
        """Return list of orchestrator capabilities."""
        return [
            "workflow_coordination",
            "real_time_progress_tracking",
            "error_recovery_management",
            "agent_failure_handling",
            "project_state_management",
            "websocket_integration",
            "production_deployment_preparation"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the orchestrator."""
        required_fields = ['prompt']
        
        # Check if required fields are present
        for field in required_fields:
            if field not in input_data:
                return False
            
        # Validate prompt is not empty
        if not input_data.get('prompt', '').strip():
            return False
            
        # Validate framework if provided
        valid_frameworks = ['react', 'vue', 'nextjs', 'vanilla', 'python']
        framework = input_data.get('framework', 'react')
        if framework not in valid_frameworks:
            return False
            
        # Validate complexity if provided
        valid_complexities = ['simple', 'intermediate', 'advanced']
        complexity = input_data.get('complexity', 'intermediate')
        if complexity not in valid_complexities:
            return False
            
        return True
    
    async def send_progress_update(self, agent_name: str, status: str, progress: float, 
                                 current_task: str, details: Optional[Dict] = None):
        """Send progress update via callback if available."""
        if self.progress_callback and self.current_job_id:
            try:
                await self.progress_callback(
                    self.current_job_id, agent_name, status, progress, current_task, details
                )
            except Exception as e:
                logger.warning(f"Failed to send progress update: {e}")
    
    def execute_vibe_workflow(self, vibe_request: Dict[str, Any], job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete vibe workflow with real-time progress updates.
        This is the main entry point for project generation.
        """
        start_time = time.time()
        self.current_job_id = job_id
        self.workflow_status = WorkflowStatus.STARTING
        
        # Initialize workflow result structure
        workflow_result = {
            'workflow_status': 'starting',
            'start_time': start_time,
            'job_id': job_id,
            'vibe_request': vibe_request,
            'agent_results': {},
            'project_data': {
                'files': {},
                'metadata': {},
                'deployment_config': {},
                'statistics': {
                    'total_files': 0,
                    'total_lines': 0,
                    'components_created': 0
                }
            },
            'timing': {
                'total_time': 0,
                'step_times': {}
            },
            'progress': {
                'current_step': 0,
                'total_steps': len(self.workflow_steps),
                'percentage': 0
            },
            'error_log': [],
            'recovery_attempts': {}
        }
        
        try:
            logger.info(f"🚀 Starting enhanced vibe workflow execution for job: {job_id}")
            
            # Send initial status
            asyncio.create_task(self.send_progress_update(
                "orchestrator", "starting", 5.0, "Initializing workflow coordination"
            ))
            
            # Execute workflow steps with enhanced error handling
            asyncio.create_task(self._execute_workflow_steps_async(workflow_result, vibe_request))
            
            # Finalize workflow
            self._finalize_workflow(workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            logger.error(traceback.format_exc())
            
            workflow_result['workflow_status'] = 'failed'
            workflow_result['error_log'].append({
                'step': 'orchestration',
                'error': str(e),
                'timestamp': time.time(),
                'traceback': traceback.format_exc()
            })
            
            # Send error status
            asyncio.create_task(self.send_progress_update(
                "orchestrator", "error", 0.0, f"Workflow failed: {str(e)}"
            ))
            
            return workflow_result
    
    async def _execute_workflow_steps_async(self, workflow_result: Dict[str, Any], vibe_request: Dict[str, Any]):
        """Execute all workflow steps asynchronously with progress updates."""
        try:
            for i, step in enumerate(self.workflow_steps):
                workflow_result['progress']['current_step'] = i + 1
                base_progress = (i / len(self.workflow_steps)) * 100
                workflow_result['progress']['percentage'] = base_progress
                
                step_name = step.display_name
                agent_name = step.agent_name
                
                logger.info(f"📋 Step {i + 1}/{len(self.workflow_steps)}: {step_name}")
                
                # Send step start update
                await self.send_progress_update(
                    agent_name, "starting", base_progress, f"Starting {step.description}"
                )
                
                step_start_time = time.time()
                
                try:
                    # Execute agent step with timeout and retries
                    step_result = await self._execute_agent_step_with_retries(
                        agent_name, workflow_result, vibe_request, step
                    )
                    
                    # Record results
                    workflow_result['agent_results'][agent_name] = step_result
                    workflow_result['timing']['step_times'][agent_name] = time.time() - step_start_time
                    
                    # Update project data
                    self._update_project_data(workflow_result, agent_name, step_result)
                    
                    # Send completion update
                    completion_progress = ((i + 1) / len(self.workflow_steps)) * 100
                    await self.send_progress_update(
                        agent_name, "completed", 100.0, f"{step_name} completed successfully"
                    )
                    
                    logger.info(f"✅ Step {i + 1} completed: {step_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Step {i + 1} failed: {step_name} - {e}")
                    workflow_result['error_log'].append({
                        'step': step_name,
                        'agent': agent_name,
                        'error': str(e),
                        'timestamp': time.time(),
                        'traceback': traceback.format_exc()
                    })
                    
                    # Send error update
                    await self.send_progress_update(
                        agent_name, "error", 0.0, f"Failed: {str(e)}"
                    )
                    
                    # Attempt recovery
                    if not await self._attempt_step_recovery(workflow_result, agent_name, e, step):
                        raise e
                        
        except Exception as e:
            logger.error(f"❌ Workflow steps execution failed: {e}")
            raise
    
    async def _execute_agent_step_with_retries(self, agent_name: str, workflow_result: Dict[str, Any], 
                                             vibe_request: Dict[str, Any], step: AgentTask) -> Dict[str, Any]:
        """Execute agent step with timeout and retry logic."""
        last_error = None
        
        for attempt in range(step.retries + 1):
            try:
                if attempt > 0:
                    await self.send_progress_update(
                        agent_name, "retrying", 0.0, f"Retry attempt {attempt}/{step.retries}"
                    )
                    logger.warning(f"🔄 Retrying {agent_name} step (attempt {attempt + 1}/{step.retries + 1})")
                
                # Set active status
                await self.send_progress_update(
                    agent_name, "active", 25.0, step.description
                )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute_agent_step_sync(agent_name, workflow_result, vibe_request),
                    timeout=step.timeout
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Agent {agent_name} timed out after {step.timeout}s")
                await self.send_progress_update(
                    agent_name, "timeout", 0.0, f"Timeout after {step.timeout}s"
                )
                
            except Exception as e:
                last_error = e
                await self.send_progress_update(
                    agent_name, "error", 0.0, f"Error: {str(e)}"
                )
                
            # Wait before retry
            if attempt < step.retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        raise last_error or Exception(f"Agent {agent_name} failed after all retries")
    
    async def _execute_agent_step_sync(self, agent_name: str, workflow_result: Dict[str, Any], 
                                     vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent step synchronously (wrapped in async for timeout)."""
        if agent_name == 'qa_validator':
            # QA Validator is async, so handle it directly
            return await self._execute_qa_validator_step(self.agent_instances[agent_name], workflow_result)
        
        def sync_execution():
            if agent_name == 'planner':
                return self._execute_planner_step(self.agent_instances[agent_name], vibe_request)
            elif agent_name == 'coder':
                return self._execute_coder_step(self.agent_instances[agent_name], workflow_result)
            elif agent_name == 'critic':
                return self._execute_critic_step(self.agent_instances[agent_name], workflow_result)
            elif agent_name == 'file_manager':
                return self._execute_file_manager_step(self.agent_instances[agent_name], workflow_result)
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
        
        # Run synchronous function in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execution)
    
    def _execute_planner_step(self, agent: VibePlannerAgent, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planner agent step with enhanced validation."""
        vibe_prompt = vibe_request['vibe_prompt']
        project_data = vibe_request.get('project_data', {})
        
        logger.info(f"🎯 Planner analyzing vibe prompt: {vibe_prompt[:100]}...")
        
        result = agent.decompose_vibe_prompt(vibe_prompt, project_data)
        
        # Enhanced validation
        if not result or 'vibe_analysis' not in result:
            raise ValueError("Planner failed to generate valid analysis")
            
        if not result.get('technical_requirements'):
            raise ValueError("Planner failed to generate technical requirements")
            
        if not result.get('implementation_steps'):
            raise ValueError("Planner failed to generate implementation steps")
        
        return {
            'success': True,
            'agent': 'planner',
            'analysis': result['vibe_analysis'],
            'technical_requirements': result['technical_requirements'],
            'implementation_steps': result['implementation_steps'],
            'estimated_time': result.get('estimated_time', 'Unknown'),
            'framework': result.get('recommended_framework', 'react'),
            'complexity': result.get('complexity_assessment', 'intermediate')
        }
    
    def _execute_coder_step(self, agent: VibeCoderAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the coder agent step with enhanced file generation."""
        planner_result = workflow_result['agent_results']['planner']
        project_id = workflow_result.get('project_id', int(time.time()))
        
        # Prepare comprehensive plan for coder
        plan = {
            'technical_requirements': planner_result['technical_requirements'],
            'vibe_analysis': planner_result['analysis'],
            'implementation_steps': planner_result['implementation_steps'],
            'framework': planner_result.get('framework', 'react'),
            'complexity': planner_result.get('complexity', 'intermediate')
        }
        
        logger.info(f"💻 Coder generating files for {plan['framework']} project...")
        
        result = agent.generate_code_from_plan(plan, project_id)
        
        # Enhanced validation
        if not result or not result.get('success', False):
            raise ValueError("Coder failed to generate valid code")
            
        if not result.get('generated_files'):
            raise ValueError("Coder failed to generate any files")
            
        file_count = len(result.get('generated_files', {}))
        if file_count == 0:
            raise ValueError("Coder generated empty file set")
        
        logger.info(f"📁 Generated {file_count} files")
        
        return {
            'success': True,
            'agent': 'coder',
            'framework': result['framework'],
            'generated_files': result['generated_files'],
            'file_count': file_count,
            'components_created': result.get('components_created', 0),
            'total_lines': sum(len(content.split('\n')) for content in result['generated_files'].values())
        }
    
    def _execute_critic_step(self, agent: VibeCriticAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the critic agent step with comprehensive review."""
        coder_result = workflow_result['agent_results']['coder']
        planner_result = workflow_result['agent_results']['planner']
        
        # Prepare files for review
        files = []
        for file_path, content in coder_result['generated_files'].items():
            files.append({
                'path': file_path,
                'content': content,
                'type': file_path.split('.')[-1] if '.' in file_path else 'unknown'
            })
        
        # Prepare plan for review
        plan = {
            'technical_requirements': planner_result['technical_requirements'],
            'vibe_analysis': planner_result['analysis'],
            'framework': coder_result['framework']
        }
        
        logger.info(f"🔍 Critic reviewing {len(files)} generated files...")
        
        result = agent.review_generated_code(files, plan)
        
        # Enhanced validation
        if 'overall_score' not in result:
            raise ValueError("Critic failed to generate valid review")
            
        overall_score = result.get('overall_score', 0)
        if overall_score < 0.5:  # Score is typically 0-1
            logger.warning(f"⚠️ Low code quality score: {overall_score}")
        
        return {
            'success': True,
            'agent': 'critic',
            'overall_score': overall_score,
            'category_scores': result.get('category_scores', {}),
            'recommendations': result.get('recommendations', []),
            'issues_found': len(result.get('issues_found', [])),
            'compliance_report': result.get('compliance_report', {}),
            'quality_grade': self._calculate_quality_grade(overall_score)
        }
    
    def _execute_file_manager_step(self, agent: VibeFileManagerAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the file manager agent step with deployment preparation."""
        coder_result = workflow_result['agent_results']['coder']
        planner_result = workflow_result['agent_results']['planner']
        
        # Prepare files for organization
        files = []
        for file_path, content in coder_result['generated_files'].items():
            files.append({
                'path': file_path,
                'filename': file_path,
                'content': content,
                'size': len(content.encode('utf-8'))
            })
        
        project_type = planner_result['analysis'].get('detected_project_type', 'web')
        framework = coder_result.get('framework', 'react')
        
        logger.info(f"📁 File manager organizing {framework} {project_type} project...")
        
        result = agent.organize_project_structure(files, project_type)
        
        # Enhanced validation
        if not result.get('success', False):
            raise ValueError("File manager failed to organize project")
            
        if not result.get('organized_files'):
            raise ValueError("File manager failed to organize any files")
        
        return {
            'success': True,
            'agent': 'file_manager',
            'framework': framework,
            'organized_files': result['organized_files'],
            'file_manifest': result.get('file_manifest', {}),
            'deployment_config': result.get('deployment_config', {}),
            'zip_file': result.get('zip_file', {}),
            'total_files': len(result.get('organized_files', {})),
            'project_size': sum(len(str(content).encode('utf-8')) for content in result.get('organized_files', {}).values())
        }
    
    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate quality grade from score."""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B+"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C+"
        else:
            return "C"
    
    def _update_project_data(self, workflow_result: Dict[str, Any], agent_name: str, step_result: Dict[str, Any]):
        """Update cumulative project data with step results."""
        if 'project_data' not in workflow_result:
            workflow_result['project_data'] = {
                'files': {},
                'metadata': {},
                'deployment_config': {},
                'statistics': {}
            }
        
        project_data = workflow_result['project_data']
        
        if agent_name == 'planner':
            project_data['metadata'].update({
                'vibe_analysis': step_result['analysis'],
                'technical_requirements': step_result['technical_requirements'],
                'implementation_steps': step_result['implementation_steps'],
                'estimated_time': step_result['estimated_time'],
                'framework': step_result.get('framework', 'react'),
                'complexity': step_result.get('complexity', 'intermediate')
            })
            
        elif agent_name == 'coder':
            project_data['files'].update(step_result['generated_files'])
            project_data['metadata'].update({
                'file_count': step_result['file_count'],
                'components_created': step_result.get('components_created', 0),
                'total_lines': step_result.get('total_lines', 0)
            })
            
        elif agent_name == 'critic':
            project_data['metadata'].update({
                'quality_score': step_result['overall_score'],
                'quality_grade': step_result.get('quality_grade', 'Unknown'),
                'code_review': {
                    'category_scores': step_result.get('category_scores', {}),
                    'recommendations': step_result.get('recommendations', []),
                    'issues_found': step_result.get('issues_found', 0)
                }
            })
            
        elif agent_name == 'file_manager':
            # Update files with organized structure
            project_data['files'] = step_result['organized_files']
            project_data['deployment_config'] = step_result.get('deployment_config', {})
            project_data['metadata'].update({
                'file_manifest': step_result.get('file_manifest', {}),
                'total_files': step_result.get('total_files', 0),
                'project_size': step_result.get('project_size', 0)
            })
    
    async def _attempt_step_recovery(self, workflow_result: Dict[str, Any], agent_name: str, 
                                   error: Exception, step: AgentTask) -> bool:
        """Attempt to recover from step failure."""
        recovery_key = f"{agent_name}_recovery"
        
        if recovery_key not in workflow_result['recovery_attempts']:
            workflow_result['recovery_attempts'][recovery_key] = 0
        
        workflow_result['recovery_attempts'][recovery_key] += 1
        
        # Simple recovery strategies
        if isinstance(error, TimeoutError):
            logger.info(f"🔄 Attempting timeout recovery for {agent_name}")
            # Could implement timeout-specific recovery
            return False
            
        elif "connection" in str(error).lower():
            logger.info(f"🔄 Attempting connection recovery for {agent_name}")
            # Could implement connection retry
            await asyncio.sleep(5)
            return workflow_result['recovery_attempts'][recovery_key] <= 2
            
        else:
            logger.info(f"🔄 No recovery strategy for {agent_name} error: {error}")
            return False
    
    async def _execute_qa_validator_step(self, agent: VibeQAValidatorAgent, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the QA validator agent step with comprehensive testing."""
        logger.info("🔍 QA Validator performing comprehensive project validation")
        
        # Prepare project files for validation from previous agent results
        project_files = {}
        
        # Extract generated files from coder results
        if 'coder' in workflow_result['agent_results']:
            coder_result = workflow_result['agent_results']['coder']
            project_files.update({
                'frontend_files': coder_result.get('frontend_files', {}),
                'backend_files': coder_result.get('backend_files', {}),
                'configuration_files': coder_result.get('configuration_files', {}),
                'test_files': coder_result.get('test_files', {})
            })
        
        # Extract organized files from file manager
        if 'file_manager' in workflow_result['agent_results']:
            file_manager_result = workflow_result['agent_results']['file_manager']
            # Update with organized structure
            organized_files = file_manager_result.get('organized_files', {})
            for category, files in organized_files.items():
                if category in project_files:
                    project_files[category].update(files)
                else:
                    project_files[category] = files
        
        # Validate with QA agent
        job_id = workflow_result.get('job_id', 'unknown')
        validation_results = await agent.validate_project(project_files, job_id)
        
        # Enhanced validation
        if not validation_results:
            raise ValueError("QA Validator failed to generate validation results")
        
        if validation_results.get('validation_status') != 'completed':
            raise ValueError(f"QA validation incomplete: {validation_results.get('validation_status')}")
        
        quality_score = validation_results.get('quality_score', 0)
        final_approval = validation_results.get('final_approval', False)
        
        logger.info(f"📊 QA Validation Results - Quality Score: {quality_score}%, Approved: {final_approval}")
        
        return {
            'success': True,
            'agent': 'qa_validator',
            'validation_results': validation_results,
            'quality_score': quality_score,
            'final_approval': final_approval,
            'test_results': validation_results.get('functional_tests', {}),
            'security_scan': validation_results.get('security_scan', {}),
            'performance_metrics': validation_results.get('performance', {}),
            'recommendations': validation_results.get('recommendations', []),
            'qa_report': await agent.generate_qa_report(validation_results)
        }

    def _finalize_workflow(self, workflow_result: Dict[str, Any]):
        """Finalize workflow execution and prepare results."""
        end_time = time.time()
        workflow_result['timing']['total_time'] = end_time - workflow_result['start_time']
        workflow_result['end_time'] = end_time
        
        # Determine final status
        if len(workflow_result['agent_results']) == len(self.workflow_steps):
            workflow_result['workflow_status'] = 'completed'
            self.workflow_status = WorkflowStatus.COMPLETED
            
            # Calculate final statistics including QA validation
            qa_results = workflow_result['agent_results'].get('qa_validator', {})
            quality_score = qa_results.get('quality_score', workflow_result['project_data']['metadata'].get('quality_score', 0))
            final_approval = qa_results.get('final_approval', False)
            
            stats = workflow_result['project_data']['statistics'] = {
                'total_files': len(workflow_result['project_data']['files']),
                'total_lines': sum(len(str(content).split('\n')) for content in workflow_result['project_data']['files'].values()),
                'components_created': workflow_result['project_data']['metadata'].get('components_created', 0),
                'quality_score': quality_score,
                'final_approval': final_approval,
                'tests_executed': len(qa_results.get('test_results', {})),
                'security_issues': qa_results.get('security_scan', {}).get('vulnerabilities_found', 0),
                'performance_score': qa_results.get('performance_metrics', {}).get('performance_score', 0),
                'generation_time': workflow_result['timing']['total_time']
            }
            
            logger.info(f"✅ Workflow completed successfully!")
            logger.info(f"📊 Generated {stats['total_files']} files, {stats['total_lines']} lines in {stats['generation_time']:.2f}s")
            
        else:
            workflow_result['workflow_status'] = 'failed'
            self.workflow_status = WorkflowStatus.FAILED
            
        workflow_result['progress']['percentage'] = 100 if workflow_result['workflow_status'] == 'completed' else 0
        
        # Reset job tracking
        self.current_job_id = None
    
    async def orchestrate_project_creation(self, prompt: str, job_id: str) -> Dict[str, Any]:
        """
        Master orchestration method for the enhanced 6-agent workflow.
        This is the main entry point for the complete project generation system.
        """
        logger.info(f"🎭 Starting 6-agent project orchestration for job: {job_id}")
        
        workflow_result = {
            'job_id': job_id,
            'status': 'in_progress',
            'current_agent': 'orchestrator',
            'progress': 0,
            'agents_completed': [],
            'final_validation': False,
            'start_time': time.time()
        }
        
        try:
            # Prepare vibe request
            vibe_request = {
                'vibe_prompt': prompt,
                'project_data': {},
                'requirements': {
                    'quality_score_minimum': 85,
                    'security_scan_required': True,
                    'performance_testing': True,
                    'comprehensive_validation': True
                }
            }
            
            # Execute the complete 6-agent workflow
            result = self.execute_vibe_workflow(vibe_request, job_id)
            
            # Extract final results
            final_result = {
                'status': 'completed' if result['workflow_status'] == 'completed' else 'failed',
                'job_id': job_id,
                'project_files': result['project_data']['files'],
                'statistics': result['project_data']['statistics'],
                'quality_validation': result['agent_results'].get('qa_validator', {}),
                'download_ready': result['workflow_status'] == 'completed',
                'execution_time': result['timing']['total_time'],
                'agents_executed': list(result['agent_results'].keys())
            }
            
            # Include QA-specific results
            if 'qa_validator' in result['agent_results']:
                qa_results = result['agent_results']['qa_validator']
                final_result.update({
                    'test_results': qa_results.get('test_results', {}),
                    'quality_score': qa_results.get('quality_score', 0),
                    'final_approval': qa_results.get('final_approval', False),
                    'qa_report': qa_results.get('qa_report', ''),
                    'recommendations': qa_results.get('recommendations', [])
                })
            
            logger.info(f"✅ 6-agent orchestration completed for job: {job_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 6-agent orchestration failed for job {job_id}: {str(e)}")
            await self.handle_workflow_error(job_id, e)
            
            return {
                'status': 'failed',
                'job_id': job_id,
                'error': str(e),
                'execution_time': time.time() - workflow_result['start_time'],
                'agents_executed': workflow_result.get('agents_completed', [])
            }
    
    async def handle_workflow_error(self, job_id: str, error: Exception):
        """Handle comprehensive workflow errors with detailed logging."""
        logger.error(f"🚨 Workflow error in job {job_id}: {str(error)}")
        logger.error(traceback.format_exc())
        
        # Send error notification via progress callback if available
        if self.progress_callback:
            try:
                await self.send_progress_update(
                    "orchestrator", "error", 0.0, f"Workflow failed: {str(error)}"
                )
            except Exception as callback_error:
                logger.error(f"Failed to send error update: {callback_error}")
    
    async def broadcast_status(self, job_id: str, message: str, progress: int, agent: str = "orchestrator"):
        """Broadcast status update via WebSocket if progress callback is available."""
        if self.progress_callback:
            try:
                status_data = {
                    'job_id': job_id,
                    'message': message,
                    'progress': progress,
                    'timestamp': time.time(),
                    'agent': agent
                }
                await self.progress_callback(job_id, agent, 'active', progress, message, status_data)
            except Exception as e:
                logger.warning(f"Failed to broadcast status: {e}")
    
    def orchestrate_vibe_project(self, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method name for backward compatibility."""
        return self.execute_vibe_workflow(vibe_request)
    
    def get_workflow_status(self) -> str:
        """Get current workflow status."""
        return self.workflow_status.value
    
    def cancel_workflow(self):
        """Cancel current workflow execution."""
        if self.workflow_status not in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            self.workflow_status = WorkflowStatus.CANCELLED
            logger.info("🛑 Workflow cancelled by user request")