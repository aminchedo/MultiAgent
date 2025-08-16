# Agent Network Infrastructure
# This configuration sets up the complete agent network infrastructure
# with autoscaling groups, load balancing, and service discovery

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "agent-network"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# Agent configuration
variable "agent_configs" {
  description = "Configuration for different agent types"
  type = map(object({
    min_replicas     = number
    max_replicas     = number
    cpu_request      = string
    memory_request   = string
    cpu_limit        = string
    memory_limit     = string
    capabilities     = list(string)
    environment_vars = map(string)
  }))
  default = {
    planner = {
      min_replicas   = 2
      max_replicas   = 10
      cpu_request    = "500m"
      memory_request = "1Gi"
      cpu_limit      = "2000m"
      memory_limit   = "4Gi"
      capabilities   = ["planning", "scheduling", "optimization"]
      environment_vars = {
        PLANNER_MODE = "distributed"
      }
    }
    coder = {
      min_replicas   = 5
      max_replicas   = 50
      cpu_request    = "1000m"
      memory_request = "2Gi"
      cpu_limit      = "4000m"
      memory_limit   = "8Gi"
      capabilities   = ["code_generation", "refactoring", "analysis"]
      environment_vars = {
        CODE_CACHE_SIZE = "1000"
      }
    }
    tester = {
      min_replicas   = 3
      max_replicas   = 30
      cpu_request    = "500m"
      memory_request = "1Gi"
      cpu_limit      = "2000m"
      memory_limit   = "4Gi"
      capabilities   = ["unit_testing", "integration_testing", "load_testing"]
      environment_vars = {
        TEST_PARALLELISM = "10"
      }
    }
    reviewer = {
      min_replicas   = 2
      max_replicas   = 20
      cpu_request    = "500m"
      memory_request = "1Gi"
      cpu_limit      = "2000m"
      memory_limit   = "4Gi"
      capabilities   = ["code_review", "security_review", "performance_review"]
      environment_vars = {
        REVIEW_DEPTH = "comprehensive"
      }
    }
    security = {
      min_replicas   = 2
      max_replicas   = 10
      cpu_request    = "1000m"
      memory_request = "2Gi"
      cpu_limit      = "3000m"
      memory_limit   = "6Gi"
      capabilities   = ["vulnerability_scanning", "code_analysis", "dependency_check"]
      environment_vars = {
        SCAN_LEVEL = "paranoid"
      }
    }
    cost_optimizer = {
      min_replicas   = 1
      max_replicas   = 5
      cpu_request    = "250m"
      memory_request = "512Mi"
      cpu_limit      = "1000m"
      memory_limit   = "2Gi"
      capabilities   = ["resource_analysis", "cost_calculation", "optimization"]
      environment_vars = {
        OPTIMIZATION_INTERVAL = "300"
      }
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = data.aws_availability_zones.available.names
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Terraform   = "true"
    Project     = "agent-network"
  }
}

# EKS Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Enable IRSA
  enable_irsa = true

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # Node groups for different agent types
  eks_managed_node_groups = {
    # General purpose node group
    general = {
      min_size     = 3
      max_size     = 10
      desired_size = 5

      instance_types = ["t3.large"]
      
      labels = {
        Environment = var.environment
        NodeType    = "general"
      }

      taints = []
    }

    # High CPU node group for compute-intensive agents
    cpu_optimized = {
      min_size     = 2
      max_size     = 20
      desired_size = 5

      instance_types = ["c5.2xlarge"]
      
      labels = {
        Environment = var.environment
        NodeType    = "cpu-optimized"
      }

      taints = [{
        key    = "workload"
        value  = "cpu-intensive"
        effect = "NO_SCHEDULE"
      }]
    }

    # Memory optimized node group
    memory_optimized = {
      min_size     = 1
      max_size     = 10
      desired_size = 3

      instance_types = ["r5.xlarge"]
      
      labels = {
        Environment = var.environment
        NodeType    = "memory-optimized"
      }

      taints = [{
        key    = "workload"
        value  = "memory-intensive"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  tags = {
    Environment = var.environment
    Terraform   = "true"
    Project     = "agent-network"
  }
}

# Kubernetes provider configuration
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# Create namespaces
resource "kubernetes_namespace" "agent_network" {
  metadata {
    name = "agent-network"
    
    labels = {
      environment = var.environment
      managed-by  = "terraform"
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    
    labels = {
      environment = var.environment
      managed-by  = "terraform"
    }
  }
}

# Deploy Redis for service discovery and shared context
resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  version    = "18.1.0"
  namespace  = kubernetes_namespace.agent_network.metadata[0].name

  values = [
    <<-EOT
    architecture: standalone
    auth:
      enabled: true
      sentinel: false
    master:
      persistence:
        enabled: true
        size: 10Gi
      resources:
        requests:
          cpu: 500m
          memory: 1Gi
        limits:
          cpu: 2000m
          memory: 4Gi
    metrics:
      enabled: true
      serviceMonitor:
        enabled: true
    EOT
  ]
}

# Deploy NATS for high-performance messaging (alternative to gRPC for some use cases)
resource "helm_release" "nats" {
  name       = "nats"
  repository = "https://nats-io.github.io/k8s/helm/charts/"
  chart      = "nats"
  version    = "1.1.0"
  namespace  = kubernetes_namespace.agent_network.metadata[0].name

  values = [
    <<-EOT
    nats:
      jetstream:
        enabled: true
        memStorage:
          enabled: true
          size: 2Gi
        fileStorage:
          enabled: true
          size: 10Gi
    cluster:
      enabled: true
      replicas: 3
    natsbox:
      enabled: true
    EOT
  ]
}

# Create service accounts for agents
resource "kubernetes_service_account" "agent_service_accounts" {
  for_each = var.agent_configs

  metadata {
    name      = "${each.key}-agent"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      agent-type = each.key
    }
  }
}

# Create ConfigMaps for agent configurations
resource "kubernetes_config_map" "agent_configs" {
  for_each = var.agent_configs

  metadata {
    name      = "${each.key}-config"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  data = {
    "agent.yaml" = yamlencode({
      agent_type = each.key
      capabilities = each.value.capabilities
      redis_url = "redis://redis-master.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:6379"
      discovery_url = "discovery-service.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:50051"
      coordinator_url = "coordinator-service.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:50052"
      heartbeat_interval = each.key == "planner" ? 2 : 5  # Faster heartbeat for critical agents
      max_queue_size = each.key == "coder" ? 2000 : 1000
      environment = var.environment
    })
  }
}

# Create Deployments for each agent type
resource "kubernetes_deployment" "agents" {
  for_each = var.agent_configs

  metadata {
    name      = "${each.key}-agent"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app        = "${each.key}-agent"
      agent-type = each.key
    }
  }

  spec {
    replicas = each.value.min_replicas

    selector {
      match_labels = {
        app = "${each.key}-agent"
      }
    }

    template {
      metadata {
        labels = {
          app        = "${each.key}-agent"
          agent-type = each.key
        }
        
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.agent_service_accounts[each.key].metadata[0].name
        
        # Node selector based on agent requirements
        dynamic "node_selector" {
          for_each = each.key == "coder" || each.key == "security" ? [1] : []
          content {
            NodeType = "cpu-optimized"
          }
        }
        
        # Tolerations for node taints
        dynamic "toleration" {
          for_each = each.key == "coder" || each.key == "security" ? [1] : []
          content {
            key      = "workload"
            operator = "Equal"
            value    = "cpu-intensive"
            effect   = "NoSchedule"
          }
        }

        container {
          name  = "agent"
          image = "agent-network/${each.key}-agent:latest"
          
          env {
            name  = "AGENT_TYPE"
            value = each.key
          }
          
          env {
            name = "AGENT_ID"
            value_from {
              field_ref {
                field_path = "metadata.name"
              }
            }
          }
          
          env {
            name = "REDIS_PASSWORD"
            value_from {
              secret_key_ref {
                name = "redis"
                key  = "redis-password"
              }
            }
          }
          
          # Add custom environment variables
          dynamic "env" {
            for_each = each.value.environment_vars
            content {
              name  = env.key
              value = env.value
            }
          }
          
          # Mount configuration
          volume_mount {
            name       = "config"
            mount_path = "/etc/agent"
            read_only  = true
          }
          
          # Mount TLS certificates
          volume_mount {
            name       = "tls-certs"
            mount_path = "/etc/tls"
            read_only  = true
          }
          
          resources {
            requests = {
              cpu    = each.value.cpu_request
              memory = each.value.memory_request
            }
            limits = {
              cpu    = each.value.cpu_limit
              memory = each.value.memory_limit
            }
          }
          
          # Health checks
          liveness_probe {
            grpc {
              port = 50100
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
          
          readiness_probe {
            grpc {
              port = 50100
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
        
        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.agent_configs[each.key].metadata[0].name
          }
        }
        
        volume {
          name = "tls-certs"
          secret {
            secret_name = "agent-tls-certs"
          }
        }
      }
    }
  }
}

# Create HorizontalPodAutoscaler for each agent type
resource "kubernetes_horizontal_pod_autoscaler_v2" "agents" {
  for_each = var.agent_configs

  metadata {
    name      = "${each.key}-agent-hpa"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.agents[each.key].metadata[0].name
    }

    min_replicas = each.value.min_replicas
    max_replicas = each.value.max_replicas

    # CPU-based scaling
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }

    # Memory-based scaling
    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type                = "Utilization"
          average_utilization = 80
        }
      }
    }

    # Custom metric: Queue depth
    metric {
      type = "External"
      external {
        metric {
          name = "agent_queue_depth"
          selector {
            match_labels = {
              agent_type = each.key
            }
          }
        }
        target {
          type  = "AverageValue"
          average_value = "100"
        }
      }
    }

    behavior {
      scale_up {
        stabilization_window_seconds = 60
        select_policy               = "Max"
        
        policy {
          type          = "Percent"
          value         = 100
          period_seconds = 15
        }
        
        policy {
          type          = "Pods"
          value         = 4
          period_seconds = 15
        }
      }
      
      scale_down {
        stabilization_window_seconds = 300
        select_policy               = "Min"
        
        policy {
          type          = "Percent"
          value         = 10
          period_seconds = 60
        }
        
        policy {
          type          = "Pods"
          value         = 1
          period_seconds = 60
        }
      }
    }
  }
}

# Create Services for agent discovery
resource "kubernetes_service" "agent_services" {
  for_each = var.agent_configs

  metadata {
    name      = "${each.key}-agent-service"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app        = "${each.key}-agent"
      agent-type = each.key
    }
  }

  spec {
    selector = {
      app = "${each.key}-agent"
    }

    port {
      name        = "grpc"
      port        = 50100
      target_port = 50100
      protocol    = "TCP"
    }
    
    port {
      name        = "metrics"
      port        = 9090
      target_port = 9090
      protocol    = "TCP"
    }

    type = "ClusterIP"
  }
}

# Deploy Prometheus for metrics collection
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "51.3.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    <<-EOT
    prometheus:
      prometheusSpec:
        serviceMonitorSelectorNilUsesHelmValues: false
        serviceMonitorSelector: {}
        retention: 30d
        storageSpec:
          volumeClaimTemplate:
            spec:
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 50Gi
    grafana:
      adminPassword: ${random_password.grafana_password.result}
      persistence:
        enabled: true
        size: 10Gi
    EOT
  ]
}

# Generate random password for Grafana
resource "random_password" "grafana_password" {
  length  = 16
  special = true
}

# Output important values
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "grafana_password" {
  description = "Grafana admin password"
  value       = random_password.grafana_password.result
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint for agent network"
  value       = "redis-master.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:6379"
}

output "agent_endpoints" {
  description = "Service endpoints for each agent type"
  value = {
    for k, v in kubernetes_service.agent_services : 
    k => "${v.metadata[0].name}.${v.metadata[0].namespace}.svc.cluster.local:50100"
  }
}