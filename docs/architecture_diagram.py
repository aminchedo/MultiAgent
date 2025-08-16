"""
Generate architecture diagrams for the Multi-Agent System
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.network import Nginx
from diagrams.onprem.queue import Kafka
from diagrams.generic.device import Mobile
from diagrams.generic.blank import Blank
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service
from diagrams.aws.compute import Lambda


def create_system_architecture():
    """Create the main system architecture diagram"""
    
    with Diagram("Multi-Agent System Architecture", filename="system_architecture", show=False, direction="TB"):
        
        # User Interface
        with Cluster("Client Layer"):
            web = Mobile("Web UI")
            api_client = Mobile("API Client")
        
        # Load Balancer
        lb = Nginx("Load Balancer")
        
        # API Gateway
        with Cluster("API Layer"):
            api = FastAPI("REST API")
            grpc = Python("gRPC Server")
        
        # Core Services
        with Cluster("Orchestration Layer"):
            agent_manager = Python("Agent Manager")
            dag_scheduler = Python("DAG Scheduler")
            nlp_processor = Python("NLP Processor")
        
        # Agent Microservices
        with Cluster("Agent Services"):
            with Cluster("Planning"):
                planner = Pod("Planner Agent")
            
            with Cluster("Development"):
                code_gen = Pod("Code Generator")
                frontend_dev = Pod("Frontend Agent")
                backend_dev = Pod("Backend Agent")
            
            with Cluster("Quality"):
                reviewer = Pod("Reviewer Agent")
                tester = Pod("Tester Agent")
                security = Pod("Security Agent")
            
            with Cluster("Documentation"):
                doc_gen = Pod("Doc Generator")
        
        # Data Layer
        with Cluster("Data & Memory"):
            postgres = PostgreSQL("PostgreSQL\n(State)")
            redis = Redis("Redis\n(Shared Memory)")
            vector_db = PostgreSQL("Vector DB\n(Cache)")
        
        # Monitoring
        with Cluster("Observability"):
            prometheus = Prometheus("Prometheus")
            grafana = Grafana("Grafana")
        
        # Connections
        web >> lb >> api
        api_client >> lb >> api
        
        api >> agent_manager
        api >> Edge(label="gRPC") >> grpc
        
        agent_manager >> dag_scheduler
        agent_manager >> nlp_processor
        
        dag_scheduler >> [planner, code_gen, reviewer, tester]
        
        planner >> Edge(label="context") >> redis
        code_gen >> Edge(label="artifacts") >> postgres
        reviewer >> Edge(label="feedback") >> redis
        
        [frontend_dev, backend_dev] >> redis
        
        agent_manager >> postgres
        nlp_processor >> vector_db
        
        # Monitoring connections
        [agent_manager, dag_scheduler, planner, code_gen] >> Edge(style="dotted") >> prometheus
        prometheus >> grafana


def create_agent_collaboration_flow():
    """Create agent collaboration flow diagram"""
    
    with Diagram("Agent Collaboration Flow", filename="collaboration_flow", show=False, direction="LR"):
        
        # Input
        user_input = Mobile("User Request")
        
        # NLP Processing
        with Cluster("NLP Processing"):
            nlp = Python("Intent Processor")
            analyzer = Python("Requirement Analyzer")
        
        # Planning Phase
        with Cluster("Planning Phase"):
            planner = Lambda("Planner Agent")
            task_gen = Python("Task Generator")
        
        # Parallel Execution
        with Cluster("Development Phase"):
            frontend = Lambda("Frontend Agent")
            backend = Lambda("Backend Agent")
            database = Lambda("Database Agent")
        
        # Quality Phase
        with Cluster("Quality Assurance"):
            reviewer = Lambda("Code Reviewer")
            tester = Lambda("Test Agent")
            security = Lambda("Security Scanner")
        
        # Output
        with Cluster("Outputs"):
            code = Blank("Generated Code")
            tests = Blank("Test Suite")
            docs = Blank("Documentation")
        
        # Shared Context
        context = Redis("Shared Context")
        
        # Flow
        user_input >> nlp >> analyzer >> planner
        planner >> task_gen
        
        task_gen >> Edge(label="parallel") >> [frontend, backend, database]
        
        frontend >> reviewer
        backend >> reviewer
        database >> reviewer
        
        reviewer >> Edge(label="if passed") >> tester
        reviewer >> Edge(label="if failed", style="dashed") >> [frontend, backend]
        
        tester >> security
        
        security >> [code, tests, docs]
        
        # Context connections
        [planner, frontend, backend, reviewer] >> Edge(style="dotted") >> context
        context >> Edge(style="dotted") >> [frontend, backend, reviewer, tester]


def create_data_flow_diagram():
    """Create data flow diagram"""
    
    with Diagram("Data Flow Architecture", filename="data_flow", show=False):
        
        # Input Sources
        with Cluster("Input"):
            api_req = Mobile("API Request")
            nlp_input = Blank("NLP Input")
        
        # Processing Layer
        with Cluster("Processing"):
            orchestrator = Python("Orchestrator")
            agents = [
                Python("Agent 1"),
                Python("Agent 2"),
                Python("Agent 3")
            ]
        
        # Storage Systems
        with Cluster("Storage"):
            with Cluster("Operational"):
                postgres = PostgreSQL("Task State")
                redis = Redis("Context")
            
            with Cluster("Analytics"):
                metrics = PostgreSQL("Metrics DB")
                logs = Kafka("Log Stream")
        
        # Output
        with Cluster("Output"):
            artifacts = Blank("Artifacts")
            monitoring = Grafana("Dashboards")
        
        # Flow
        api_req >> orchestrator
        nlp_input >> orchestrator
        
        orchestrator >> agents
        
        agents >> postgres
        agents >> redis
        agents >> metrics
        agents >> logs
        
        postgres >> artifacts
        redis >> agents  # Bidirectional
        
        [metrics, logs] >> monitoring


def create_deployment_architecture():
    """Create Kubernetes deployment architecture"""
    
    with Diagram("Kubernetes Deployment", filename="k8s_deployment", show=False):
        
        # Ingress
        ingress = Service("Ingress")
        
        # Services
        with Cluster("Services"):
            api_svc = Service("API Service")
            grpc_svc = Service("gRPC Service")
        
        # Deployments
        with Cluster("Core Deployments"):
            with Cluster("Orchestrator"):
                orch_pods = [Pod(f"orchestrator-{i}") for i in range(3)]
            
            with Cluster("API"):
                api_pods = [Pod(f"api-{i}") for i in range(2)]
        
        # Agent Deployments
        with Cluster("Agent Deployments"):
            with Cluster("Planner Agents"):
                planner_pods = [Pod(f"planner-{i}") for i in range(2)]
            
            with Cluster("Code Agents"):
                code_pods = [Pod(f"code-gen-{i}") for i in range(4)]
            
            with Cluster("Review Agents"):
                review_pods = [Pod(f"reviewer-{i}") for i in range(2)]
        
        # StatefulSets
        with Cluster("StatefulSets"):
            postgres_sts = PostgreSQL("PostgreSQL")
            redis_sts = Redis("Redis Cluster")
        
        # Connections
        ingress >> api_svc >> api_pods >> orch_pods
        ingress >> grpc_svc >> orch_pods
        
        orch_pods >> planner_pods
        orch_pods >> code_pods
        orch_pods >> review_pods
        
        [orch_pods, planner_pods, code_pods] >> postgres_sts
        [orch_pods, planner_pods, code_pods] >> redis_sts


if __name__ == "__main__":
    # Generate all diagrams
    print("Generating architecture diagrams...")
    
    create_system_architecture()
    print("✓ System architecture diagram created")
    
    create_agent_collaboration_flow()
    print("✓ Agent collaboration flow diagram created")
    
    create_data_flow_diagram()
    print("✓ Data flow diagram created")
    
    create_deployment_architecture()
    print("✓ Kubernetes deployment diagram created")
    
    print("\nAll diagrams generated successfully!")
    print("Check the current directory for PNG files.")