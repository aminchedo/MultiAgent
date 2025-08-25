"""
VibeWorkflowOrchestratorAgent - Orchestrates the complete vibe coding workflow.

This agent coordinates all other vibe agents to create a complete development workflow
from vibe prompt to final organized and reviewed code project.
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from agents.base_agent import BaseAgent


class VibeWorkflowOrchestratorAgent(BaseAgent):
    """
    Agent responsible for orchestrating the complete vibe coding workflow.
    
    This agent:
    1. Coordinates all vibe agents (Planner, Coder, Critic, FileManager)
    2. Manages the workflow execution and error handling
    3. Tracks progress and provides status updates
    4. Ensures quality gates are met at each stage
    5. Produces final deliverables and project summaries
    """
    
    def __init__(self, agent_id: str = None, name: str = "VibeWorkflowOrchestratorAgent"):
        # Initialize capabilities as empty list for BaseAgent
        capabilities = []
        super().__init__("vibe_orchestrator", capabilities)
        self.logger = logging.getLogger(__name__)
        
        # Agent capabilities (stored as simple list for this implementation)
        self.vibe_capabilities = [
            "workflow_orchestration",
            "agent_coordination", 
            "progress_tracking",
            "quality_gate_management",
            "error_handling",
            "deliverable_compilation"
        ]
        
        # Workflow stages and their dependencies
        self.workflow_stages = {
            "planning": {
                "agent": "VibePlannerAgent",
                "method": "decompose_vibe_prompt",
                "dependencies": [],
                "required_inputs": ["vibe_prompt", "project_data"],
                "quality_threshold": 0.0,  # No threshold for planning
                "timeout_seconds": 60
            },
            "coding": {
                "agent": "VibeCoderAgent", 
                "method": "generate_code_from_plan",
                "dependencies": ["planning"],
                "required_inputs": ["plan", "project_id"],
                "quality_threshold": 0.0,  # No threshold for initial coding
                "timeout_seconds": 120
            },
            "review": {
                "agent": "VibeCriticAgent",
                "method": "review_generated_code", 
                "dependencies": ["coding"],
                "required_inputs": ["files", "plan"],
                "quality_threshold": 60.0,  # Minimum 60% quality score
                "timeout_seconds": 90
            },
            "organization": {
                "agent": "VibeFileManagerAgent",
                "method": "organize_project_structure",
                "dependencies": ["coding"],
                "required_inputs": ["files", "project_type"],
                "quality_threshold": 70.0,  # Minimum 70% organization score
                "timeout_seconds": 60
            },
            "final_review": {
                "agent": "VibeCriticAgent",
                "method": "review_generated_code",
                "dependencies": ["organization"],
                "required_inputs": ["files", "plan"],
                "quality_threshold": 75.0,  # Higher threshold for final review
                "timeout_seconds": 90
            }
        }
        
        # Quality gates configuration
        self.quality_gates = {
            "minimum_overall_score": 70.0,
            "maximum_high_security_issues": 0,
            "maximum_medium_security_issues": 2,
            "minimum_documentation_score": 60.0,
            "minimum_organization_score": 70.0
        }
        
        # Retry configuration
        self.retry_config = {
            "max_retries": 2,
            "retry_delay_seconds": 5,
            "exponential_backoff": True
        }

    async def orchestrate_vibe_project(self, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration method that manages the complete vibe workflow.
        
        Args:
            vibe_request: Complete vibe request with prompt and configuration
            
        Returns:
            Complete project result with all deliverables and metadata
        """
        start_time = time.time()
        workflow_id = f"vibe_workflow_{int(time.time())}"
        
        try:
            self.logger.info(f"Starting vibe workflow orchestration: {workflow_id}")
            
            # Initialize workflow state
            workflow_state = {
                "workflow_id": workflow_id,
                "status": "running",
                "current_stage": "initialization",
                "completed_stages": [],
                "failed_stages": [],
                "stage_results": {},
                "quality_checks": {},
                "retry_counts": {},
                "start_time": datetime.utcnow().isoformat(),
                "progress_percentage": 0
            }
            
            # Validate input request
            validation_result = self._validate_vibe_request(vibe_request)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid vibe request: {validation_result['errors']}")
            
            # Extract request parameters
            vibe_prompt = vibe_request.get("vibe_prompt", "")
            project_type = vibe_request.get("project_type", "web_app")
            complexity = vibe_request.get("complexity", "moderate")
            project_id = vibe_request.get("project_id", int(time.time()))
            
            # Stage 1: Planning
            workflow_state["current_stage"] = "planning"
            workflow_state["progress_percentage"] = 10
            
            planning_result = await self._execute_stage_with_retries(
                "planning",
                {
                    "vibe_prompt": vibe_prompt,
                    "project_data": {
                        "project_type": project_type,
                        "complexity": complexity,
                        "project_id": project_id
                    }
                },
                workflow_state
            )
            
            if not planning_result["success"]:
                return self._create_failure_response(workflow_state, "Planning stage failed", start_time)
            
            plan = planning_result["result"]
            workflow_state["stage_results"]["planning"] = plan
            workflow_state["completed_stages"].append("planning")
            
            # Stage 2: Code Generation
            workflow_state["current_stage"] = "coding"
            workflow_state["progress_percentage"] = 30
            
            coding_result = await self._execute_stage_with_retries(
                "coding",
                {
                    "plan": plan,
                    "project_id": project_id
                },
                workflow_state
            )
            
            if not coding_result["success"]:
                return self._create_failure_response(workflow_state, "Coding stage failed", start_time)
                
            code_result = coding_result["result"]
            workflow_state["stage_results"]["coding"] = code_result
            workflow_state["completed_stages"].append("coding")
            
            # Stage 3: Initial Code Review
            workflow_state["current_stage"] = "review"
            workflow_state["progress_percentage"] = 50
            
            review_result = await self._execute_stage_with_retries(
                "review",
                {
                    "files": code_result.get("files", []),
                    "plan": plan
                },
                workflow_state
            )
            
            if not review_result["success"]:
                return self._create_failure_response(workflow_state, "Review stage failed", start_time)
                
            review = review_result["result"]
            workflow_state["stage_results"]["review"] = review
            workflow_state["completed_stages"].append("review")
            
            # Check quality gate after initial review
            quality_gate_result = self._check_quality_gates(review, "initial_review")
            workflow_state["quality_checks"]["initial_review"] = quality_gate_result
            
            # Stage 4: File Organization
            workflow_state["current_stage"] = "organization"
            workflow_state["progress_percentage"] = 70
            
            organization_result = await self._execute_stage_with_retries(
                "organization",
                {
                    "files": code_result.get("files", []),
                    "project_type": plan.get("project_type", project_type)
                },
                workflow_state
            )
            
            if not organization_result["success"]:
                return self._create_failure_response(workflow_state, "Organization stage failed", start_time)
                
            organization = organization_result["result"]
            workflow_state["stage_results"]["organization"] = organization
            workflow_state["completed_stages"].append("organization")
            
            # Stage 5: Final Review
            workflow_state["current_stage"] = "final_review"
            workflow_state["progress_percentage"] = 85
            
            final_review_result = await self._execute_stage_with_retries(
                "final_review",
                {
                    "files": organization.get("organized_files", []),
                    "plan": plan
                },
                workflow_state
            )
            
            if not final_review_result["success"]:
                return self._create_failure_response(workflow_state, "Final review stage failed", start_time)
                
            final_review = final_review_result["result"]
            workflow_state["stage_results"]["final_review"] = final_review
            workflow_state["completed_stages"].append("final_review")
            
            # Final quality gate check
            final_quality_gate = self._check_quality_gates(final_review, "final_review")
            workflow_state["quality_checks"]["final_review"] = final_quality_gate
            
            # Stage 6: Compile final deliverables
            workflow_state["current_stage"] = "compilation"
            workflow_state["progress_percentage"] = 95
            
            final_deliverables = self._compile_final_deliverables(workflow_state, vibe_request)
            
            # Mark workflow as completed
            workflow_state["status"] = "completed"
            workflow_state["current_stage"] = "completed"
            workflow_state["progress_percentage"] = 100
            workflow_state["end_time"] = datetime.utcnow().isoformat()
            workflow_state["total_duration"] = time.time() - start_time
            
            # Create final result
            final_result = {
                "workflow_status": "success",
                "workflow_id": workflow_id,
                "vibe_prompt": vibe_prompt,
                "project_type": plan.get("project_type", project_type),
                "deliverables": final_deliverables,
                "workflow_state": workflow_state,
                "quality_summary": self._create_quality_summary(workflow_state),
                "performance_metrics": self._calculate_performance_metrics(workflow_state),
                "files_generated": len(organization.get("organized_files", [])),
                "final_quality_score": final_review.get("overall_score", 0),
                "production_ready": final_quality_gate.get("passed", False),
                "metadata": {
                    "orchestrator_agent_id": self.agent_id,
                    "completion_timestamp": datetime.utcnow().isoformat(),
                    "total_processing_time": time.time() - start_time,
                    "workflow_version": "1.0"
                }
            }
            
            self.logger.info(f"Vibe workflow completed successfully in {time.time() - start_time:.2f}s")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Vibe workflow orchestration failed: {str(e)}")
            
            if 'workflow_state' in locals():
                workflow_state["status"] = "failed"
                workflow_state["error"] = str(e)
                workflow_state["end_time"] = datetime.utcnow().isoformat()
                workflow_state["total_duration"] = time.time() - start_time
                
            return {
                "workflow_status": "failed",
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_state": locals().get('workflow_state', {}),
                "metadata": {
                    "orchestrator_agent_id": self.agent_id,
                    "error_timestamp": datetime.utcnow().isoformat(),
                    "processing_time": time.time() - start_time
                }
            }

    def _validate_vibe_request(self, vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the vibe request structure and content."""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required fields
        required_fields = ["vibe_prompt"]
        for field in required_fields:
            if field not in vibe_request or not vibe_request[field]:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
                
        # Validate vibe prompt
        vibe_prompt = vibe_request.get("vibe_prompt", "")
        if len(vibe_prompt) < 10:
            validation_result["errors"].append("Vibe prompt too short (minimum 10 characters)")
            validation_result["valid"] = False
        elif len(vibe_prompt) > 5000:
            validation_result["warnings"].append("Vibe prompt is very long, may affect processing time")
            
        # Validate project type
        valid_project_types = ["web_app", "api", "mobile_app", "dashboard", "cli_tool", "library"]
        project_type = vibe_request.get("project_type", "web_app")
        if project_type not in valid_project_types:
            validation_result["warnings"].append(f"Unknown project type: {project_type}, using default")
            
        # Validate complexity
        valid_complexities = ["simple", "moderate", "complex", "enterprise"]
        complexity = vibe_request.get("complexity", "moderate")
        if complexity not in valid_complexities:
            validation_result["warnings"].append(f"Unknown complexity: {complexity}, using default")
            
        return validation_result

    async def _execute_stage_with_retries(self, stage_name: str, inputs: Dict[str, Any], workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow stage with retry logic."""
        
        stage_config = self.workflow_stages[stage_name]
        max_retries = self.retry_config["max_retries"]
        retry_delay = self.retry_config["retry_delay_seconds"]
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Executing stage {stage_name}, attempt {attempt + 1}")
                
                # Import and instantiate the agent
                agent_instance = await self._get_agent_instance(stage_config["agent"])
                
                # Get the method to call
                method = getattr(agent_instance, stage_config["method"])
                
                # Prepare arguments based on required inputs
                method_args = []
                for input_name in stage_config["required_inputs"]:
                    if input_name in inputs:
                        method_args.append(inputs[input_name])
                    else:
                        raise ValueError(f"Missing required input: {input_name} for stage {stage_name}")
                
                # Execute with timeout
                try:
                    result = await asyncio.wait_for(
                        method(*method_args),
                        timeout=stage_config["timeout_seconds"]
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Stage {stage_name} timed out after {stage_config['timeout_seconds']} seconds")
                
                # Check for errors in result
                if isinstance(result, dict) and "error" in result:
                    raise RuntimeError(f"Stage {stage_name} returned error: {result['error']}")
                
                # Check quality threshold if specified
                quality_threshold = stage_config.get("quality_threshold", 0)
                if quality_threshold > 0:
                    quality_score = self._extract_quality_score(result)
                    if quality_score < quality_threshold:
                        if attempt < max_retries:
                            self.logger.warning(f"Stage {stage_name} quality score {quality_score} below threshold {quality_threshold}, retrying...")
                            await asyncio.sleep(retry_delay)
                            if self.retry_config["exponential_backoff"]:
                                retry_delay *= 2
                            continue
                        else:
                            self.logger.warning(f"Stage {stage_name} quality score {quality_score} below threshold {quality_threshold}, but max retries reached")
                
                # Stage successful
                workflow_state["retry_counts"][stage_name] = attempt
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1,
                    "execution_time": time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Stage {stage_name} attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries:
                    self.logger.info(f"Retrying stage {stage_name} in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    if self.retry_config["exponential_backoff"]:
                        retry_delay *= 2
                else:
                    # All retries exhausted
                    workflow_state["failed_stages"].append(stage_name)
                    workflow_state["retry_counts"][stage_name] = attempt + 1
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": attempt + 1
                    }

    async def _get_agent_instance(self, agent_class_name: str):
        """Get an instance of the specified agent."""
        
        if agent_class_name == "VibePlannerAgent":
            from agents.vibe_planner_agent import VibePlannerAgent
            return VibePlannerAgent()
        elif agent_class_name == "VibeCoderAgent":
            from agents.vibe_coder_agent import VibeCoderAgent
            return VibeCoderAgent()
        elif agent_class_name == "VibeCriticAgent":
            from agents.vibe_critic_agent import VibeCriticAgent
            return VibeCriticAgent()
        elif agent_class_name == "VibeFileManagerAgent":
            from agents.vibe_file_manager_agent import VibeFileManagerAgent
            return VibeFileManagerAgent()
        else:
            raise ValueError(f"Unknown agent class: {agent_class_name}")

    def _extract_quality_score(self, result: Dict[str, Any]) -> float:
        """Extract quality score from a stage result."""
        
        # Different stages return scores in different formats
        if "overall_score" in result:
            return result["overall_score"]
        elif "metrics" in result and "organization_score" in result["metrics"]:
            return result["metrics"]["organization_score"]
        elif "score" in result:
            return result["score"]
        else:
            return 100.0  # Default to perfect score if no score found

    def _check_quality_gates(self, review_result: Dict[str, Any], gate_name: str) -> Dict[str, Any]:
        """Check if quality gates are met."""
        
        gate_result = {
            "gate_name": gate_name,
            "passed": True,
            "issues": [],
            "warnings": [],
            "score_breakdown": {}
        }
        
        overall_score = review_result.get("overall_score", 0)
        security_issues = review_result.get("security_issues", [])
        category_scores = review_result.get("category_scores", {})
        
        # Check minimum overall score
        min_score = self.quality_gates["minimum_overall_score"]
        if overall_score < min_score:
            gate_result["issues"].append(f"Overall score {overall_score:.1f} below minimum {min_score}")
            gate_result["passed"] = False
            
        # Check security issues
        high_security_issues = [issue for issue in security_issues if issue.get("severity") == "high"]
        medium_security_issues = [issue for issue in security_issues if issue.get("severity") == "medium"]
        
        max_high = self.quality_gates["maximum_high_security_issues"]
        max_medium = self.quality_gates["maximum_medium_security_issues"]
        
        if len(high_security_issues) > max_high:
            gate_result["issues"].append(f"Too many high security issues: {len(high_security_issues)} (max {max_high})")
            gate_result["passed"] = False
            
        if len(medium_security_issues) > max_medium:
            gate_result["warnings"].append(f"Many medium security issues: {len(medium_security_issues)} (max {max_medium})")
            
        # Check documentation score
        doc_score = category_scores.get("documentation", 100)
        min_doc_score = self.quality_gates["minimum_documentation_score"]
        if doc_score < min_doc_score:
            gate_result["warnings"].append(f"Documentation score {doc_score:.1f} below recommended {min_doc_score}")
            
        gate_result["score_breakdown"] = {
            "overall_score": overall_score,
            "documentation_score": doc_score,
            "high_security_issues": len(high_security_issues),
            "medium_security_issues": len(medium_security_issues)
        }
        
        return gate_result

    def _create_failure_response(self, workflow_state: Dict[str, Any], error_message: str, start_time: float) -> Dict[str, Any]:
        """Create a standardized failure response."""
        
        workflow_state["status"] = "failed"
        workflow_state["error"] = error_message
        workflow_state["end_time"] = datetime.utcnow().isoformat()
        workflow_state["total_duration"] = time.time() - start_time
        
        return {
            "workflow_status": "failed",
            "workflow_id": workflow_state.get("workflow_id", "unknown"),
            "error": error_message,
            "workflow_state": workflow_state,
            "metadata": {
                "orchestrator_agent_id": self.agent_id,
                "failure_timestamp": datetime.utcnow().isoformat(),
                "processing_time": time.time() - start_time
            }
        }

    def _compile_final_deliverables(self, workflow_state: Dict[str, Any], vibe_request: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all deliverables into final package."""
        
        stage_results = workflow_state.get("stage_results", {})
        
        # Get organized files from file manager
        organization_result = stage_results.get("organization", {})
        organized_files = organization_result.get("organized_files", [])
        
        # Get plan from planner
        plan = stage_results.get("planning", {})
        
        # Get reviews
        initial_review = stage_results.get("review", {})
        final_review = stage_results.get("final_review", {})
        
        # Compile deliverables
        deliverables = {
            "project_files": organized_files,
            "project_structure": organization_result.get("optimal_structure", {}),
            "build_configurations": organization_result.get("build_optimizations", {}),
            "documentation": self._compile_documentation(plan, organization_result, final_review),
            "deployment_guide": self._create_deployment_guide(plan, organization_result),
            "quality_report": self._create_quality_report(initial_review, final_review),
            "development_plan": plan,
            "setup_instructions": self._create_setup_instructions(plan, organized_files),
            "recommended_next_steps": self._create_next_steps(final_review, organization_result)
        }
        
        return deliverables

    def _compile_documentation(self, plan: Dict[str, Any], organization: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, Any]:
        """Compile comprehensive project documentation."""
        
        return {
            "project_overview": {
                "description": plan.get("vibe_prompt", "Generated project"),
                "project_type": plan.get("project_type", "web_app"),
                "complexity": plan.get("complexity", "moderate"),
                "technology_stack": plan.get("technology_stack", {}),
                "estimated_timeline": plan.get("estimates", {}).get("estimated_days", "Unknown")
            },
            "architecture": plan.get("specifications", {}),
            "api_documentation": plan.get("specifications", {}).get("api_endpoints", []),
            "file_structure": organization.get("optimal_structure", {}),
            "quality_metrics": {
                "overall_score": review.get("overall_score", 0),
                "category_scores": review.get("category_scores", {}),
                "production_ready": review.get("summary", {}).get("readiness_for_production", False)
            }
        }

    def _create_deployment_guide(self, plan: Dict[str, Any], organization: Dict[str, Any]) -> Dict[str, Any]:
        """Create deployment guide based on project configuration."""
        
        tech_stack = plan.get("technology_stack", {})
        build_opts = organization.get("build_optimizations", {})
        
        return {
            "deployment_options": tech_stack.get("deployment", ["Vercel", "Netlify"]),
            "build_commands": build_opts.get("build_scripts", {}),
            "environment_setup": plan.get("specifications", {}).get("deployment_config", {}),
            "prerequisites": self._determine_prerequisites(tech_stack),
            "deployment_steps": self._generate_deployment_steps(tech_stack)
        }

    def _determine_prerequisites(self, tech_stack: Dict[str, Any]) -> List[str]:
        """Determine deployment prerequisites."""
        
        prereqs = []
        
        if tech_stack.get("frontend"):
            prereqs.append("Node.js (version 18 or higher)")
            prereqs.append("npm or yarn package manager")
            
        if tech_stack.get("backend"):
            backend_tech = tech_stack["backend"][0] if tech_stack["backend"] else ""
            if "Python" in backend_tech:
                prereqs.append("Python 3.11 or higher")
                prereqs.append("pip package manager")
            elif "Node.js" in backend_tech:
                prereqs.append("Node.js runtime environment")
                
        if tech_stack.get("database"):
            db_type = tech_stack["database"][0] if tech_stack["database"] else ""
            if "PostgreSQL" in db_type:
                prereqs.append("PostgreSQL database server")
            elif "MongoDB" in db_type:
                prereqs.append("MongoDB database server")
                
        return prereqs

    def _generate_deployment_steps(self, tech_stack: Dict[str, Any]) -> List[str]:
        """Generate deployment steps."""
        
        steps = [
            "1. Clone the project repository",
            "2. Install dependencies"
        ]
        
        if tech_stack.get("frontend"):
            steps.append("3. Configure environment variables (.env)")
            steps.append("4. Build the project (npm run build)")
            steps.append("5. Deploy to hosting platform")
            
        if tech_stack.get("backend"):
            steps.extend([
                "6. Set up database connection",
                "7. Run database migrations",
                "8. Start the backend server"
            ])
            
        steps.append("9. Verify deployment and run tests")
        
        return steps

    def _create_quality_report(self, initial_review: Dict[str, Any], final_review: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive quality report."""
        
        return {
            "initial_assessment": {
                "overall_score": initial_review.get("overall_score", 0),
                "security_issues": len(initial_review.get("security_issues", [])),
                "performance_issues": len(initial_review.get("performance_issues", [])),
                "recommendations": len(initial_review.get("recommendations", []))
            },
            "final_assessment": {
                "overall_score": final_review.get("overall_score", 0),
                "security_issues": len(final_review.get("security_issues", [])),
                "performance_issues": len(final_review.get("performance_issues", [])),
                "production_ready": final_review.get("summary", {}).get("readiness_for_production", False)
            },
            "improvement_summary": {
                "score_improvement": final_review.get("overall_score", 0) - initial_review.get("overall_score", 0),
                "issues_resolved": len(initial_review.get("security_issues", [])) - len(final_review.get("security_issues", [])),
                "quality_trend": "improved" if final_review.get("overall_score", 0) > initial_review.get("overall_score", 0) else "stable"
            },
            "outstanding_issues": final_review.get("security_issues", [])[:5],  # Top 5 issues
            "recommendations": final_review.get("recommendations", [])[:3]  # Top 3 recommendations
        }

    def _create_setup_instructions(self, plan: Dict[str, Any], files: List[Dict]) -> List[str]:
        """Create step-by-step setup instructions."""
        
        tech_stack = plan.get("technology_stack", {})
        
        instructions = [
            "# Project Setup Instructions",
            "",
            "## Prerequisites"
        ]
        
        prereqs = self._determine_prerequisites(tech_stack)
        for prereq in prereqs:
            instructions.append(f"- {prereq}")
            
        instructions.extend([
            "",
            "## Installation Steps",
            "",
            "1. Extract project files to your desired directory",
            "2. Open terminal/command prompt in the project directory"
        ])
        
        # Add technology-specific setup
        if tech_stack.get("frontend"):
            instructions.extend([
                "3. Install frontend dependencies:",
                "   ```bash",
                "   npm install",
                "   ```"
            ])
            
        if tech_stack.get("backend"):
            backend_tech = tech_stack["backend"][0] if tech_stack["backend"] else ""
            if "Python" in backend_tech:
                instructions.extend([
                    "4. Install backend dependencies:",
                    "   ```bash", 
                    "   pip install -r requirements.txt",
                    "   ```"
                ])
                
        instructions.extend([
            "5. Configure environment variables:",
            "   - Copy .env.example to .env",
            "   - Update the values as needed",
            "",
            "6. Start the development server:",
            "   ```bash",
            "   npm run dev",
            "   ```",
            "",
            "7. Open your browser and navigate to http://localhost:3000"
        ])
        
        return instructions

    def _create_next_steps(self, review: Dict[str, Any], organization: Dict[str, Any]) -> List[str]:
        """Create recommended next steps for development."""
        
        next_steps = []
        
        # Based on quality score
        overall_score = review.get("overall_score", 0)
        
        if overall_score >= 90:
            next_steps.extend([
                "✅ Code quality is excellent - ready for production",
                "Consider adding advanced features or optimizations",
                "Set up CI/CD pipeline for automated deployment"
            ])
        elif overall_score >= 75:
            next_steps.extend([
                "✅ Code quality is good - minor improvements needed",
                "Address remaining recommendations before production",
                "Add comprehensive test coverage"
            ])
        else:
            next_steps.extend([
                "⚠️  Code quality needs improvement before production",
                "Address all high-priority recommendations",
                "Consider refactoring complex components"
            ])
            
        # Add specific recommendations from review
        recommendations = review.get("recommendations", [])
        high_priority_recs = [r for r in recommendations if r.get("priority") == "high"]
        
        if high_priority_recs:
            next_steps.append("High Priority Tasks:")
            for rec in high_priority_recs[:3]:
                next_steps.append(f"- {rec.get('title', 'Unknown')}")
                
        # Add organization recommendations
        org_recommendations = organization.get("recommendations", [])
        if org_recommendations:
            next_steps.append("Organization Improvements:")
            for rec in org_recommendations[:2]:
                next_steps.append(f"- {rec}")
                
        return next_steps

    def _create_quality_summary(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create quality summary across all stages."""
        
        quality_checks = workflow_state.get("quality_checks", {})
        stage_results = workflow_state.get("stage_results", {})
        
        summary = {
            "overall_workflow_quality": "unknown",
            "quality_gates_passed": 0,
            "quality_gates_failed": 0,
            "critical_issues": [],
            "quality_trend": "stable"
        }
        
        # Count quality gate results
        for gate_name, gate_result in quality_checks.items():
            if gate_result.get("passed", False):
                summary["quality_gates_passed"] += 1
            else:
                summary["quality_gates_failed"] += 1
                summary["critical_issues"].extend(gate_result.get("issues", []))
                
        # Determine overall quality
        if summary["quality_gates_failed"] == 0:
            summary["overall_workflow_quality"] = "excellent"
        elif summary["quality_gates_failed"] <= 1:
            summary["overall_workflow_quality"] = "good"
        else:
            summary["overall_workflow_quality"] = "needs_improvement"
            
        # Calculate quality trend
        initial_review = stage_results.get("review", {})
        final_review = stage_results.get("final_review", {})
        
        if initial_review and final_review:
            initial_score = initial_review.get("overall_score", 0)
            final_score = final_review.get("overall_score", 0)
            
            if final_score > initial_score + 5:
                summary["quality_trend"] = "improving"
            elif final_score < initial_score - 5:
                summary["quality_trend"] = "declining"
            else:
                summary["quality_trend"] = "stable"
                
        return summary

    def _calculate_performance_metrics(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for the workflow."""
        
        metrics = {
            "total_duration_seconds": workflow_state.get("total_duration", 0),
            "stages_completed": len(workflow_state.get("completed_stages", [])),
            "stages_failed": len(workflow_state.get("failed_stages", [])),
            "total_retries": sum(workflow_state.get("retry_counts", {}).values()),
            "efficiency_score": 0.0
        }
        
        # Calculate efficiency score
        total_stages = len(self.workflow_stages)
        completed_stages = metrics["stages_completed"]
        total_retries = metrics["total_retries"]
        
        completion_rate = completed_stages / total_stages if total_stages > 0 else 0
        retry_penalty = min(total_retries * 0.1, 0.3)  # Max 30% penalty
        
        metrics["efficiency_score"] = max(0, (completion_rate - retry_penalty) * 100)
        
        # Performance assessment
        if metrics["efficiency_score"] >= 90:
            metrics["performance_assessment"] = "excellent"
        elif metrics["efficiency_score"] >= 75:
            metrics["performance_assessment"] = "good"
        elif metrics["efficiency_score"] >= 60:
            metrics["performance_assessment"] = "fair"
        else:
            metrics["performance_assessment"] = "poor"
            
        return metrics

    async def process_task(self, task) -> Any:
        """Process a task (required by BaseAgent)."""
        # For vibe agents, we don't use the generic task processing
        return {"status": "task_not_supported", "message": "Use orchestrate_vibe_project instead"}

    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get custom metrics for the orchestrator agent."""
        return {
            "workflows_executed": 0.0,
            "successful_workflows": 0.0,
            "average_workflow_time": 0.0,
            "quality_gate_pass_rate": 0.0
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_orchestrator():
        orchestrator = VibeWorkflowOrchestratorAgent()
        
        # Test vibe request
        vibe_request = {
            "vibe_prompt": "Create a modern React dashboard for sales analytics with real-time charts, user authentication, and data export functionality",
            "project_type": "dashboard",
            "complexity": "moderate",
            "project_id": 12345
        }
        
        result = await orchestrator.orchestrate_vibe_project(vibe_request)
        
        print("=== VIBE WORKFLOW ORCHESTRATION RESULT ===")
        print(f"Workflow Status: {result['workflow_status']}")
        print(f"Files Generated: {result.get('files_generated', 0)}")
        print(f"Final Quality Score: {result.get('final_quality_score', 0):.1f}/100")
        print(f"Production Ready: {result.get('production_ready', False)}")
        print(f"Processing Time: {result.get('metadata', {}).get('total_processing_time', 0):.2f}s")
        
        if result["workflow_status"] == "success":
            print(f"Completed Stages: {result['workflow_state']['completed_stages']}")
            print(f"Quality Summary: {result['quality_summary']['overall_workflow_quality']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    # Run the test
    asyncio.run(test_orchestrator())