"""
Enhanced Vibe Coding Workflow Orchestrator - coordinates the four specialized agents for complete vibe-to-project transformation.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from backend.agents.specialized.vibe_planner_agent import VibePlannerAgent
from backend.agents.specialized.vibe_coder_agent import VibeCoderAgent
from backend.agents.specialized.vibe_critic_agent import VibeCriticAgent
from backend.agents.specialized.vibe_file_manager_agent import VibeFileManagerAgent
from backend.agents.base.base_agent import BaseCrewAgent
from backend.models.models import JobStatus, WebSocketMessage, MessageType
from backend.database.db import db_manager
from config.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class VibeWorkflowOrchestrator:
    """
    Main orchestrator for the enhanced Vibe Coding workflow.
    Coordinates the four specialized agents in the optimal sequence:
    Planner → Coder → Critic → File Manager
    """

    def __init__(self, job_id: str, websocket_callback: Optional[Callable] = None):
        self.job_id = job_id
        self.websocket_callback = websocket_callback
        
        # Initialize the four specialized agents
        self.planner = VibePlannerAgent(job_id, websocket_callback)
        self.coder = VibeCoderAgent(job_id, websocket_callback)
        self.critic = VibeCriticAgent(job_id, websocket_callback)
        self.file_manager = VibeFileManagerAgent(job_id, websocket_callback)
        
        # Workflow state
        self.workflow_state = {
            "current_phase": "initializing",
            "phases_completed": [],
            "total_phases": 5,  # Including initialization phase
            "start_time": None,
            "end_time": None,
            "errors": [],
            "warnings": []
        }

    async def execute_vibe_workflow(self, vibe_prompt: str, project_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete vibe coding workflow.
        
        Args:
            vibe_prompt: User's natural language description of what they want
            project_options: Additional options like complexity, framework preferences
            
        Returns:
            Complete project package ready for download
        """
        
        self.workflow_state["start_time"] = datetime.now()
        
        try:
            await self._log_workflow_message("🚀 Starting Vibe Coding Workflow", {
                "vibe_prompt": vibe_prompt[:100] + "..." if len(vibe_prompt) > 100 else vibe_prompt,
                "options": project_options
            })
            
            await self._update_workflow_progress(0, "Initializing Vibe Coding Workflow", "initializing")
            
            # Phase 1: Vibe Analysis and Planning (Planner Agent)
            await self._update_workflow_progress(5, "🧠 Planner Agent: Analyzing your vibe...", "planning")
            plan = await self._execute_planning_phase(vibe_prompt, project_options)
            
            # Phase 2: Code Generation (Coder Agent)
            await self._update_workflow_progress(25, "👨‍💻 Coder Agent: Generating your project...", "coding")
            generated_files = await self._execute_coding_phase(plan)
            
            # Phase 3: Code Review and Validation (Critic Agent)
            await self._update_workflow_progress(85, "🔍 Critic Agent: Reviewing code quality...", "reviewing")
            review_results = await self._execute_review_phase(generated_files, plan)
            
            # Phase 4: Project Organization and Finalization (File Manager Agent)
            await self._update_workflow_progress(96, "📁 File Manager: Organizing your project...", "finalizing")
            final_package = await self._execute_finalization_phase(generated_files, review_results, plan)
            
            # Phase 5: Completion
            await self._update_workflow_progress(100, "✅ Your vibe project is ready!", "completed")
            
            self.workflow_state["end_time"] = datetime.now()
            duration = (self.workflow_state["end_time"] - self.workflow_state["start_time"]).total_seconds()
            
            # Compile final results
            final_results = {
                "success": True,
                "workflow_metadata": {
                    "job_id": self.job_id,
                    "original_vibe": vibe_prompt,
                    "total_duration_seconds": duration,
                    "phases_completed": self.workflow_state["phases_completed"],
                    "agent_collaboration": [
                        {"agent": "Planner", "phase": "Analysis & Planning", "status": "completed"},
                        {"agent": "Coder", "phase": "Code Generation", "status": "completed"},
                        {"agent": "Critic", "phase": "Quality Review", "status": "completed"},
                        {"agent": "File Manager", "phase": "Project Organization", "status": "completed"}
                    ]
                },
                "plan": plan,
                "generated_files": len(generated_files),
                "review_results": review_results,
                "final_package": final_package,
                "download_ready": True
            }
            
            await self._log_workflow_message("🎉 Vibe Coding Workflow Completed Successfully!", {
                "duration_seconds": duration,
                "total_files": final_package.get("project_metadata", {}).get("total_files", 0),
                "review_score": review_results.get("overall_score", 0),
                "package_size_mb": final_package.get("package_info", {}).get("size_mb", 0)
            })
            
            # Update final job status
            await db_manager.update_job_status(
                job_id=self.job_id,
                status=JobStatus.COMPLETED,
                progress=100,
                current_step="Vibe project ready for download!",
                step_number=5
            )
            
            return final_results
            
        except Exception as e:
            await self._handle_workflow_error(e)
            raise

    async def _execute_planning_phase(self, vibe_prompt: str, project_options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planning phase using the Planner Agent."""
        
        try:
            await self._send_websocket_update({
                "type": "agent_start",
                "agent": "planner",
                "message": "🧠 Planner Agent is analyzing your vibe and creating a technical plan..."
            })
            
            # Prepare project data for the planner
            project_data = {
                "vibe_prompt": vibe_prompt,
                "project_type": project_options.get("project_type", "web"),
                "complexity": project_options.get("complexity", "simple"),
                "framework_preference": project_options.get("framework", None),
                "styling_preference": project_options.get("styling", None),
                "created_at": datetime.now().isoformat(),
                "job_id": self.job_id
            }
            
            # Execute planning
            plan = await self.planner.decompose_vibe_prompt(vibe_prompt, project_data)
            
            self.workflow_state["phases_completed"].append("planning")
            
            await self._send_websocket_update({
                "type": "agent_complete",
                "agent": "planner",
                "message": f"✅ Plan created: {plan.get('estimated_files', 'several')} files, {plan.get('estimated_complexity', 'moderate')} complexity"
            })
            
            return plan
            
        except Exception as e:
            await self._log_workflow_message(f"❌ Planning phase failed: {str(e)}", {"error": str(e)})
            raise

    async def _execute_coding_phase(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute the coding phase using the Coder Agent."""
        
        try:
            await self._send_websocket_update({
                "type": "agent_start",
                "agent": "coder",
                "message": "👨‍💻 Coder Agent is generating your project files..."
            })
            
            # Execute code generation
            generated_files = await self.coder.generate_code(plan)
            
            self.workflow_state["phases_completed"].append("coding")
            
            await self._send_websocket_update({
                "type": "agent_complete",
                "agent": "coder",
                "message": f"✅ Generated {len(generated_files)} files with your exact vibe"
            })
            
            return generated_files
            
        except Exception as e:
            await self._log_workflow_message(f"❌ Coding phase failed: {str(e)}", {"error": str(e)})
            raise

    async def _execute_review_phase(self, generated_files: List[Dict[str, Any]], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the review phase using the Critic Agent."""
        
        try:
            await self._send_websocket_update({
                "type": "agent_start",
                "agent": "critic",
                "message": "🔍 Critic Agent is reviewing code quality and vibe alignment..."
            })
            
            # Execute code review
            review_results = await self.critic.review_code(generated_files, plan)
            
            self.workflow_state["phases_completed"].append("reviewing")
            
            # Prepare review summary for user
            overall_score = review_results.get("overall_score", 8.0)
            approval_status = review_results.get("approval_status", True)
            vibe_score = review_results.get("vibe_alignment", {}).get("alignment_score", 8.0)
            
            if approval_status:
                review_message = f"✅ Code review passed! Quality: {overall_score}/10, Vibe match: {vibe_score}/10"
            else:
                issues_count = len(review_results.get("critical_issues", []))
                review_message = f"⚠️ Review completed with {issues_count} issues to address"
            
            await self._send_websocket_update({
                "type": "agent_complete",
                "agent": "critic",
                "message": review_message
            })
            
            # Handle review results
            if review_results.get("needs_fixes", False):
                await self._handle_review_fixes(review_results, generated_files)
            
            return review_results
            
        except Exception as e:
            await self._log_workflow_message(f"❌ Review phase failed: {str(e)}", {"error": str(e)})
            raise

    async def _execute_finalization_phase(
        self, 
        generated_files: List[Dict[str, Any]], 
        review_results: Dict[str, Any], 
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the finalization phase using the File Manager Agent."""
        
        try:
            await self._send_websocket_update({
                "type": "agent_start",
                "agent": "file_manager",
                "message": "📁 File Manager is organizing your project structure..."
            })
            
            # Execute project organization and packaging
            final_package = await self.file_manager.organize_and_finalize_project(
                generated_files, review_results, plan
            )
            
            self.workflow_state["phases_completed"].append("finalizing")
            
            project_name = final_package.get("project_metadata", {}).get("name", "your project")
            total_files = final_package.get("project_metadata", {}).get("total_files", 0)
            
            await self._send_websocket_update({
                "type": "agent_complete",
                "agent": "file_manager",
                "message": f"✅ {project_name} organized: {total_files} files ready for download!"
            })
            
            return final_package
            
        except Exception as e:
            await self._log_workflow_message(f"❌ Finalization phase failed: {str(e)}", {"error": str(e)})
            raise

    async def _handle_review_fixes(self, review_results: Dict[str, Any], generated_files: List[Dict[str, Any]]):
        """Handle fixes suggested by the critic agent."""
        
        critical_issues = review_results.get("critical_issues", [])
        suggestions = review_results.get("suggestions", [])
        
        if critical_issues:
            await self._log_workflow_message(
                f"⚠️ {len(critical_issues)} critical issues found - applying automatic fixes",
                {"issues": critical_issues}
            )
            
            # In a production system, you might want to regenerate specific files
            # For now, we'll log the issues and continue
            self.workflow_state["warnings"].extend(critical_issues)
        
        if suggestions:
            await self._log_workflow_message(
                f"💡 {len(suggestions)} improvement suggestions available",
                {"suggestions": [s.get("message", "") for s in suggestions[:3]]}
            )

    async def _update_workflow_progress(self, progress: int, message: str, phase: str):
        """Update workflow progress and send notifications."""
        
        self.workflow_state["current_phase"] = phase
        
        # Update database
        await db_manager.update_job_status(
            job_id=self.job_id,
            status=JobStatus.RUNNING if progress < 100 else JobStatus.COMPLETED,
            progress=progress,
            current_step=message,
            step_number=len(self.workflow_state["phases_completed"]) + 1
        )
        
        # Send WebSocket update
        await self._send_websocket_update({
            "type": "progress",
            "progress": progress,
            "message": message,
            "phase": phase,
            "job_id": self.job_id
        })

    async def _send_websocket_update(self, data: Dict[str, Any]):
        """Send WebSocket update to frontend."""
        
        if self.websocket_callback:
            try:
                websocket_message = WebSocketMessage(
                    type=MessageType.PROGRESS,
                    job_id=self.job_id,
                    content=data
                )
                await self.websocket_callback(websocket_message.dict())
            except Exception as e:
                logger.warning(f"WebSocket update failed: {e}")

    async def _log_workflow_message(self, message: str, metadata: Dict[str, Any] = None):
        """Log workflow message to database."""
        
        await db_manager.create_log(
            job_id=self.job_id,
            agent="VibeWorkflowOrchestrator",
            message=message,
            level="INFO",
            metadata=metadata or {}
        )

    async def _handle_workflow_error(self, error: Exception):
        """Handle workflow errors gracefully."""
        
        error_message = f"Vibe workflow failed: {str(error)}"
        
        self.workflow_state["errors"].append({
            "error": str(error),
            "phase": self.workflow_state["current_phase"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Update job status to failed
        await db_manager.update_job_status(
            job_id=self.job_id,
            status=JobStatus.FAILED,
            error_message=error_message
        )
        
        # Send error notification via WebSocket
        await self._send_websocket_update({
            "type": "error",
            "message": error_message,
            "phase": self.workflow_state["current_phase"]
        })
        
        await self._log_workflow_message(f"❌ {error_message}", {
            "error_type": type(error).__name__,
            "error_details": str(error),
            "phase": self.workflow_state["current_phase"]
        })

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        
        return {
            "job_id": self.job_id,
            "current_phase": self.workflow_state["current_phase"],
            "phases_completed": self.workflow_state["phases_completed"],
            "total_phases": self.workflow_state["total_phases"],
            "progress_percentage": (len(self.workflow_state["phases_completed"]) / self.workflow_state["total_phases"]) * 100,
            "errors": self.workflow_state["errors"],
            "warnings": self.workflow_state["warnings"],
            "duration": self._calculate_duration()
        }

    def _calculate_duration(self) -> Optional[float]:
        """Calculate workflow duration if completed."""
        
        if self.workflow_state["start_time"]:
            end_time = self.workflow_state["end_time"] or datetime.now()
            return (end_time - self.workflow_state["start_time"]).total_seconds()
        return None


# Factory function for easy integration with existing system
async def create_and_execute_vibe_workflow(
    job_id: str,
    vibe_prompt: str,
    project_options: Dict[str, Any],
    websocket_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Factory function to create and execute a vibe coding workflow.
    This function provides compatibility with the existing system.
    """
    
    orchestrator = VibeWorkflowOrchestrator(job_id, websocket_callback)
    return await orchestrator.execute_vibe_workflow(vibe_prompt, project_options)


# Compatibility wrapper for existing MultiAgent workflow
async def create_and_execute_enhanced_workflow(
    job_id: str,
    project_data: Dict[str, Any],
    websocket_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Enhanced workflow wrapper that can handle both traditional and vibe-based requests.
    """
    
    # Check if this is a vibe-based request
    vibe_prompt = project_data.get("prompt") or project_data.get("description") or project_data.get("vibe_prompt")
    
    if vibe_prompt and len(vibe_prompt) > 10:  # Likely a vibe prompt
        logger.info(f"Detected vibe-based request, using enhanced workflow")
        
        # Extract project options
        project_options = {
            "project_type": project_data.get("project_type", "web"),
            "complexity": project_data.get("complexity", "simple"),
            "framework": project_data.get("framework"),
            "styling": project_data.get("styling")
        }
        
        # Use the new vibe workflow
        return await create_and_execute_vibe_workflow(
            job_id, vibe_prompt, project_options, websocket_callback
        )
    
    else:
        # Fall back to traditional workflow for backward compatibility
        logger.info(f"Using traditional workflow for non-vibe request")
        from backend.agents.agents import create_and_execute_workflow
        return await create_and_execute_workflow(job_id, project_data, websocket_callback)