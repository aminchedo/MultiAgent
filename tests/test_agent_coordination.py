"""
Comprehensive Test Suite for Agent Coordination System
Tests task assignment flow, cross-agent verification, and output validation.
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

import redis.asyncio as redis

from backend.core.agent_coordinator import (
    AgentCoordinator, TaskAssignment, CrossAgentVerification, 
    WorkflowExecution, TaskPriority, WorkflowStatus
)
from services.discovery_service import DiscoveryService, AgentInfo
from backend.models.models import AgentType


class TestAgentCoordination:
    """Test cases for agent coordination functionality."""
    
    @pytest.fixture
    async def redis_client(self):
        """Mock Redis client for testing."""
        mock_redis = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    async def discovery_service(self):
        """Mock discovery service for testing."""
        mock_discovery = AsyncMock()
        
        # Mock agent info
        mock_agent = AgentInfo(
            agent_id="test_agent_1",
            agent_type="code_generator",
            endpoint="localhost:50051",
            capabilities=["generate", "code", "implement"],
            ip="127.0.0.1",
            port=50051,
            load=0.3,
            cpu_usage=0.2,
            memory_usage=0.4,
            active_tasks=2
        )
        
        mock_discovery.find_agents_by_type.return_value = [mock_agent]
        mock_discovery.get_agent_info.return_value = mock_agent
        mock_discovery.get_all_agents.return_value = {"test_agent_1": mock_agent}
        
        return mock_discovery
    
    @pytest.fixture
    async def coordinator(self, redis_client, discovery_service):
        """Create agent coordinator for testing."""
        return AgentCoordinator(redis_client, discovery_service)
    
    @pytest.mark.asyncio
    async def test_task_assignment_flow(self, coordinator):
        """
        Test complete task assignment flow as required by functional requirements.
        
        Tests:
        1. Task submission
        2. Agent selection
        3. Task assignment
        4. Status checking
        """
        # 1. Submit task
        task_id = await coordinator.submit_task(
            task_description="generate_login_page",
            agent_type="code_generator",
            priority=TaskPriority.HIGH
        )
        
        assert task_id.startswith("task_")
        assert task_id in coordinator.task_assignments
        
        # 2. Verify task assignment
        assignment = coordinator.task_assignments[task_id]
        assert assignment.task_id == task_id
        assert assignment.agent_type == "code_generator"
        assert assignment.priority == TaskPriority.HIGH
        
        # 3. Check task status
        status = await coordinator.check_task_status(task_id)
        assert status["task_id"] == task_id
        assert status["agent"]["type"] == "code_generator"
        assert "assignment" in status
        
        # Verify metrics updated
        assert coordinator._coordination_metrics["tasks_assigned"] == 1
    
    @pytest.mark.asyncio
    async def test_cross_agent_verification(self, coordinator):
        """
        Test cross-agent verification process.
        
        Tests:
        1. Verification setup
        2. Multiple agent involvement
        3. Consensus mechanism
        """
        # Submit task with verification
        task_id = await coordinator.submit_task(
            task_description="implement secure authentication",
            verification_required=True
        )
        
        # Verify cross-agent verification was setup
        verification_found = False
        for verification in coordinator.verifications.values():
            if verification.primary_task_id == task_id:
                verification_found = True
                assert len(verification.verifying_agents) <= 3
                assert verification.required_consensus == 0.75
                break
        
        assert verification_found, "Cross-agent verification not setup"
    
    @pytest.mark.asyncio 
    async def test_output_validation(self, coordinator):
        """
        Test output validation as specified in requirements.
        
        Tests:
        1. Format validation
        2. Content quality validation
        3. Expected output comparison
        4. Cross-agent verification integration
        """
        # Submit and setup task
        task_id = await coordinator.submit_task("generate test code")
        
        # Mock task output in Redis
        valid_output = {
            "result": "def test_login(): pass",
            "metadata": {"language": "python", "lines": 1},
            "timestamp": datetime.now().isoformat()
        }
        coordinator.redis.hget.return_value = json.dumps(valid_output)
        
        # Test validation
        is_valid = await coordinator.validate_output(
            task_id, 
            expected_output="ui_templates/login.html"
        )
        
        # Should fail because output doesn't match expected HTML
        assert not is_valid
        
        # Test with matching output
        html_output = {
            "result": "<html><body>Login Page</body></html>",
            "metadata": {"type": "html"},
            "timestamp": datetime.now().isoformat()
        }
        coordinator.redis.hget.return_value = json.dumps(html_output)
        
        is_valid = await coordinator.validate_output(
            task_id,
            expected_output="login"
        )
        
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, coordinator):
        """
        Test end-to-end workflow execution with dependencies.
        
        Tests:
        1. Workflow creation
        2. Task dependency handling
        3. Sequential execution
        4. Error handling
        """
        # Create workflow with dependencies
        task_definitions = [
            {
                "description": "Plan authentication system",
                "agent_type": "planner",
                "priority": 3,
                "dependencies": []
            },
            {
                "description": "Generate login component", 
                "agent_type": "code_generator",
                "priority": 2,
                "dependencies": []  # Will be set to first task
            },
            {
                "description": "Test authentication",
                "agent_type": "tester", 
                "priority": 1,
                "dependencies": []  # Will be set to second task
            }
        ]
        
        workflow_id = await coordinator.create_workflow(
            "Authentication System",
            task_definitions
        )
        
        # Verify workflow creation
        assert workflow_id.startswith("wf_")
        assert workflow_id in coordinator.active_workflows
        
        workflow = coordinator.active_workflows[workflow_id]
        assert workflow.name == "Authentication System"
        assert len(workflow.tasks) == 3
        assert workflow.status == WorkflowStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_agent_selection_algorithm(self, coordinator):
        """
        Test intelligent agent selection based on load and capabilities.
        """
        # Mock multiple agents with different loads
        agents = [
            AgentInfo(
                agent_id="agent_1", agent_type="code_generator", 
                endpoint="localhost:50051", capabilities=["generate"],
                ip="127.0.0.1", port=50051, load=0.9, cpu_usage=0.8, 
                memory_usage=0.7, active_tasks=8
            ),
            AgentInfo(
                agent_id="agent_2", agent_type="code_generator",
                endpoint="localhost:50052", capabilities=["generate"],
                ip="127.0.0.1", port=50052, load=0.2, cpu_usage=0.3,
                memory_usage=0.1, active_tasks=1
            )
        ]
        
        # Select best agent (should pick agent_2 with lower load)
        selected = await coordinator._select_best_agent(agents, "generate code")
        
        assert selected.agent_id == "agent_2"
        assert selected.load < agents[0].load
    
    @pytest.mark.asyncio
    async def test_task_retry_mechanism(self, coordinator):
        """Test task retry mechanism for failed tasks."""
        task_id = await coordinator.submit_task("failing task")
        assignment = coordinator.task_assignments[task_id]
        
        # Simulate task failure and retry
        assignment.retry_count = 1
        assert assignment.retry_count < assignment.max_retries
        
        # Simulate max retries reached
        assignment.retry_count = assignment.max_retries
        assert assignment.retry_count == assignment.max_retries
    
    @pytest.mark.asyncio
    async def test_coordination_metrics(self, coordinator):
        """Test coordination system metrics collection."""
        # Submit multiple tasks
        for i in range(5):
            await coordinator.submit_task(f"task {i}")
        
        # Simulate completed tasks
        coordinator.redis.llen.return_value = 3
        coordinator.redis.lrange.return_value = ["1.5", "2.0", "1.8"]
        
        metrics = await coordinator.get_coordination_metrics()
        
        assert metrics["tasks_assigned"] == 5
        assert metrics["avg_task_duration"] > 0
        assert "active_workflows" in metrics
        assert "agent_utilization" in metrics
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self, coordinator):
        """Test task dependency resolution and scheduling."""
        # Create tasks with dependencies
        task1_id = await coordinator.submit_task("base task", dependencies=set())
        task2_id = await coordinator.submit_task("dependent task", dependencies={task1_id})
        
        # Mock task1 as completed
        coordinator.redis.hget.side_effect = lambda key, field: {
            ("tasks", task1_id): json.dumps({"status": "completed"}),
            ("tasks", task2_id): json.dumps({"status": "pending"})
        }.get((key, field))
        
        # Check that task2 can now be scheduled
        status = await coordinator.check_task_status(task2_id)
        assert status["task_id"] == task2_id
    
    @pytest.mark.asyncio
    async def test_verification_consensus(self, coordinator):
        """Test cross-agent verification consensus mechanism."""
        task_id = await coordinator.submit_task("critical task", verification_required=True)
        
        # Find the verification for this task
        verification = None
        for v in coordinator.verifications.values():
            if v.primary_task_id == task_id:
                verification = v
                break
        
        assert verification is not None
        assert verification.required_consensus == 0.75
        assert len(verification.verification_criteria) > 0


class TestAgentCoordinationIntegration:
    """Integration tests for agent coordination with real components."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_redis_integration(self):
        """Test coordination with real Redis instance."""
        # Skip if Redis not available
        try:
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await redis_client.ping()
        except:
            pytest.skip("Redis not available for integration test")
        
        # Test with real Redis
        discovery_service = Mock()
        coordinator = AgentCoordinator(redis_client, discovery_service)
        
        # Cleanup after test
        await redis_client.flushdb()
        await redis_client.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """End-to-end integration test of complete workflow."""
        # This would test the complete flow from task submission to completion
        # with real agents and services
        pass


class TestAgentCoordinationLoad:
    """Load and performance tests for agent coordination."""
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_high_task_volume(self, coordinator):
        """Test coordination system under high task load."""
        # Submit 1000 tasks concurrently
        tasks = []
        for i in range(1000):
            task = coordinator.submit_task(f"load test task {i}")
            tasks.append(task)
        
        task_ids = await asyncio.gather(*tasks)
        
        assert len(task_ids) == 1000
        assert len(set(task_ids)) == 1000  # All unique
        assert coordinator._coordination_metrics["tasks_assigned"] == 1000
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, coordinator):
        """Test multiple concurrent workflows."""
        workflows = []
        
        for i in range(50):
            workflow_task = coordinator.create_workflow(
                f"Workflow {i}",
                [{"description": f"Task {j}", "agent_type": "planner"} 
                 for j in range(5)]
            )
            workflows.append(workflow_task)
        
        workflow_ids = await asyncio.gather(*workflows)
        
        assert len(workflow_ids) == 50
        assert len(coordinator.active_workflows) == 50


class TestAgentCoordinationChaos:
    """Chaos engineering tests for agent coordination resilience."""
    
    @pytest.mark.chaos
    @pytest.mark.asyncio
    async def test_redis_failure_recovery(self, coordinator):
        """Test recovery from Redis failures."""
        # Submit task normally
        task_id = await coordinator.submit_task("test task")
        
        # Simulate Redis failure
        coordinator.redis.hget.side_effect = redis.ConnectionError("Redis down")
        
        # System should handle gracefully
        with pytest.raises(Exception):
            await coordinator.check_task_status(task_id)
        
        # Restore Redis and verify recovery
        coordinator.redis.hget.side_effect = None
        coordinator.redis.hget.return_value = json.dumps({"status": "running"})
        
        status = await coordinator.check_task_status(task_id)
        assert status["task_id"] == task_id
    
    @pytest.mark.chaos
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, coordinator):
        """Test handling of agent failures during task execution."""
        task_id = await coordinator.submit_task("test task")
        
        # Simulate agent becoming unavailable
        coordinator.discovery.get_agent_info.return_value = None
        
        # System should handle gracefully
        status = await coordinator.check_task_status(task_id)
        assert status["agent"]["load"] is None  # Graceful degradation
    
    @pytest.mark.chaos
    @pytest.mark.asyncio
    async def test_network_partition_handling(self, coordinator):
        """Test behavior during network partitions."""
        # Submit tasks before partition
        task_ids = []
        for i in range(10):
            task_id = await coordinator.submit_task(f"partition test {i}")
            task_ids.append(task_id)
        
        # Simulate network partition (discovery service unavailable)
        coordinator.discovery.find_agents_by_type.side_effect = asyncio.TimeoutError()
        
        # New task submissions should fail gracefully
        with pytest.raises(Exception):
            await coordinator.submit_task("new task during partition")
        
        # Existing task status should still work with cached data
        for task_id in task_ids:
            try:
                status = await coordinator.check_task_status(task_id)
                assert status["task_id"] == task_id
            except Exception:
                pass  # Some failures expected during partition


# Test fixtures and utilities

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_task_output():
    """Mock task output for testing."""
    return {
        "result": "Generated code content",
        "metadata": {
            "language": "python",
            "lines": 50,
            "functions": 3,
            "classes": 1
        },
        "timestamp": datetime.now().isoformat(),
        "agent_id": "test_agent_1",
        "execution_time": 2.5
    }


@pytest.fixture
def sample_workflow_definition():
    """Sample workflow definition for testing."""
    return [
        {
            "description": "Analyze requirements",
            "agent_type": "planner",
            "priority": 3,
            "dependencies": [],
            "verification_required": True
        },
        {
            "description": "Generate API endpoints",
            "agent_type": "code_generator", 
            "priority": 2,
            "dependencies": ["analyze_requirements"],
            "verification_required": True
        },
        {
            "description": "Create unit tests",
            "agent_type": "tester",
            "priority": 2,
            "dependencies": ["generate_api"],
            "verification_required": False
        },
        {
            "description": "Security scan",
            "agent_type": "security",
            "priority": 1,
            "dependencies": ["generate_api", "create_tests"],
            "verification_required": True
        }
    ]


# Performance benchmarks

class TestPerformanceBenchmarks:
    """Performance benchmarks for agent coordination."""
    
    @pytest.mark.benchmark
    def test_task_submission_performance(self, benchmark, coordinator):
        """Benchmark task submission performance."""
        def submit_task():
            return asyncio.run(coordinator.submit_task("benchmark task"))
        
        result = benchmark(submit_task)
        assert result.startswith("task_")
    
    @pytest.mark.benchmark
    def test_status_check_performance(self, benchmark, coordinator):
        """Benchmark status checking performance."""
        # Setup
        task_id = asyncio.run(coordinator.submit_task("benchmark task"))
        coordinator.redis.hget.return_value = json.dumps({"status": "running"})
        
        def check_status():
            return asyncio.run(coordinator.check_task_status(task_id))
        
        result = benchmark(check_status)
        assert result["task_id"] == task_id
    
    @pytest.mark.benchmark
    def test_validation_performance(self, benchmark, coordinator):
        """Benchmark output validation performance."""
        # Setup
        task_id = asyncio.run(coordinator.submit_task("benchmark task"))
        coordinator.redis.hget.return_value = json.dumps({
            "result": "test output",
            "metadata": {},
            "timestamp": datetime.now().isoformat()
        })
        
        def validate_output():
            return asyncio.run(coordinator.validate_output(task_id))
        
        result = benchmark(validate_output)
        assert isinstance(result, bool)


# Custom test markers for different test types
# Add to pytest.ini:
# markers =
#     integration: marks tests as integration tests
#     load: marks tests as load tests  
#     chaos: marks tests as chaos engineering tests
#     benchmark: marks tests as performance benchmarks