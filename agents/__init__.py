"""
Vibe Agents Module

This module contains all the specialized vibe agents for the MultiAgent Vibe Coding Platform.
Each agent handles a specific aspect of the vibe project generation workflow.
"""

from .vibe_base_agent import VibeBaseAgent
from .vibe_planner_agent import VibePlannerAgent
from .vibe_coder_agent import VibeCoderAgent
from .vibe_critic_agent import VibeCriticAgent
from .vibe_file_manager_agent import VibeFileManagerAgent
from .vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent

__all__ = [
    'VibeBaseAgent',
    'VibePlannerAgent',
    'VibeCoderAgent', 
    'VibeCriticAgent',
    'VibeFileManagerAgent',
    'VibeWorkflowOrchestratorAgent'
]

# Agent registry for easy access
VIBE_AGENTS = {
    'planner': VibePlannerAgent,
    'coder': VibeCoderAgent,
    'critic': VibeCriticAgent,
    'file_manager': VibeFileManagerAgent,
    'orchestrator': VibeWorkflowOrchestratorAgent
}

def get_agent(agent_name: str):
    """Get an agent instance by name."""
    agent_class = VIBE_AGENTS.get(agent_name)
    if agent_class:
        return agent_class()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

def list_available_agents():
    """List all available vibe agents."""
    return list(VIBE_AGENTS.keys())

def test_all_agents():
    """Test that all vibe agents can be instantiated."""
    results = {}
    
    for agent_name, agent_class in VIBE_AGENTS.items():
        try:
            agent = agent_class()
            capabilities = agent.get_capabilities() if hasattr(agent, 'get_capabilities') else []
            results[agent_name] = {
                'status': 'success',
                'capabilities': capabilities,
                'class': agent_class.__name__
            }
        except Exception as e:
            results[agent_name] = {
                'status': 'error',
                'error': str(e),
                'class': agent_class.__name__
            }
    
    return results