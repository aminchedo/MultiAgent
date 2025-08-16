# Coordinator and Discovery Services
# This configuration deploys the core coordinator and discovery services
# that manage the agent network

# Discovery Service Deployment
resource "kubernetes_deployment" "discovery_service" {
  metadata {
    name      = "discovery-service"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app     = "discovery-service"
      service = "core"
    }
  }

  spec {
    replicas = 3  # HA configuration

    selector {
      match_labels = {
        app = "discovery-service"
      }
    }

    template {
      metadata {
        labels = {
          app     = "discovery-service"
          service = "core"
        }
        
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {
                  match_expressions {
                    key      = "app"
                    operator = "In"
                    values   = ["discovery-service"]
                  }
                }
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }

        container {
          name  = "discovery"
          image = "agent-network/discovery-service:latest"
          
          env {
            name  = "REDIS_URL"
            value = "redis://redis-master.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:6379"
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
          
          env {
            name  = "HEALTH_CHECK_INTERVAL"
            value = "2"
          }
          
          env {
            name  = "STALE_AGENT_TIMEOUT"
            value = "30"
          }

          port {
            name           = "grpc"
            container_port = 50051
            protocol       = "TCP"
          }
          
          port {
            name           = "metrics"
            container_port = 9090
            protocol       = "TCP"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "2Gi"
            }
          }
          
          liveness_probe {
            grpc {
              port = 50051
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
          
          readiness_probe {
            grpc {
              port = 50051
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
          
          volume_mount {
            name       = "tls-certs"
            mount_path = "/etc/tls"
            read_only  = true
          }
        }
        
        volume {
          name = "tls-certs"
          secret {
            secret_name = "discovery-tls-certs"
          }
        }
      }
    }
  }
}

# Discovery Service
resource "kubernetes_service" "discovery_service" {
  metadata {
    name      = "discovery-service"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app     = "discovery-service"
      service = "core"
    }
    
    annotations = {
      "service.beta.kubernetes.io/aws-load-balancer-type" = "nlb"
    }
  }

  spec {
    selector = {
      app = "discovery-service"
    }

    port {
      name        = "grpc"
      port        = 50051
      target_port = 50051
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

# Coordinator Service Deployment
resource "kubernetes_deployment" "coordinator_service" {
  metadata {
    name      = "coordinator-service"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app     = "coordinator-service"
      service = "core"
    }
  }

  spec {
    replicas = 3  # HA configuration

    selector {
      match_labels = {
        app = "coordinator-service"
      }
    }

    template {
      metadata {
        labels = {
          app     = "coordinator-service"
          service = "core"
        }
        
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {
                  match_expressions {
                    key      = "app"
                    operator = "In"
                    values   = ["coordinator-service"]
                  }
                }
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }

        container {
          name  = "coordinator"
          image = "agent-network/coordinator-service:latest"
          
          env {
            name  = "REDIS_URL"
            value = "redis://redis-master.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:6379"
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
          
          env {
            name  = "DISCOVERY_URL"
            value = "discovery-service.${kubernetes_namespace.agent_network.metadata[0].name}.svc.cluster.local:50051"
          }
          
          env {
            name  = "MAX_MESSAGE_SIZE"
            value = "10485760"  # 10MB
          }
          
          env {
            name  = "STREAM_BUFFER_SIZE"
            value = "1000"
          }

          port {
            name           = "grpc"
            container_port = 50052
            protocol       = "TCP"
          }
          
          port {
            name           = "metrics"
            container_port = 9090
            protocol       = "TCP"
          }

          resources {
            requests = {
              cpu    = "500m"
              memory = "1Gi"
            }
            limits = {
              cpu    = "2000m"
              memory = "4Gi"
            }
          }
          
          liveness_probe {
            grpc {
              port = 50052
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
          
          readiness_probe {
            grpc {
              port = 50052
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
          
          volume_mount {
            name       = "tls-certs"
            mount_path = "/etc/tls"
            read_only  = true
          }
          
          volume_mount {
            name       = "jwt-keys"
            mount_path = "/etc/jwt"
            read_only  = true
          }
        }
        
        volume {
          name = "tls-certs"
          secret {
            secret_name = "coordinator-tls-certs"
          }
        }
        
        volume {
          name = "jwt-keys"
          secret {
            secret_name = "jwt-keys"
          }
        }
      }
    }
  }
}

# Coordinator Service
resource "kubernetes_service" "coordinator_service" {
  metadata {
    name      = "coordinator-service"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
    
    labels = {
      app     = "coordinator-service"
      service = "core"
    }
  }

  spec {
    selector = {
      app = "coordinator-service"
    }

    port {
      name        = "grpc"
      port        = 50052
      target_port = 50052
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

# Create TLS certificates for services
resource "kubernetes_secret" "discovery_tls" {
  metadata {
    name      = "discovery-tls-certs"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  type = "kubernetes.io/tls"

  data = {
    "tls.crt" = file("${path.module}/certs/discovery.crt")
    "tls.key" = file("${path.module}/certs/discovery.key")
    "ca.crt"  = file("${path.module}/certs/ca.crt")
  }
}

resource "kubernetes_secret" "coordinator_tls" {
  metadata {
    name      = "coordinator-tls-certs"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  type = "kubernetes.io/tls"

  data = {
    "tls.crt" = file("${path.module}/certs/coordinator.crt")
    "tls.key" = file("${path.module}/certs/coordinator.key")
    "ca.crt"  = file("${path.module}/certs/ca.crt")
  }
}

resource "kubernetes_secret" "agent_tls" {
  metadata {
    name      = "agent-tls-certs"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  type = "kubernetes.io/tls"

  data = {
    "tls.crt" = file("${path.module}/certs/agent.crt")
    "tls.key" = file("${path.module}/certs/agent.key")
    "ca.crt"  = file("${path.module}/certs/ca.crt")
  }
}

# Create JWT keys for authentication
resource "kubernetes_secret" "jwt_keys" {
  metadata {
    name      = "jwt-keys"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  type = "Opaque"

  data = {
    "private_key.pem" = file("${path.module}/jwt/private_key.pem")
    "public_key.pem"  = file("${path.module}/jwt/public_key.pem")
  }
}

# Create PodDisruptionBudgets for high availability
resource "kubernetes_pod_disruption_budget_v1" "discovery_pdb" {
  metadata {
    name      = "discovery-service-pdb"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  spec {
    min_available = 2
    
    selector {
      match_labels = {
        app = "discovery-service"
      }
    }
  }
}

resource "kubernetes_pod_disruption_budget_v1" "coordinator_pdb" {
  metadata {
    name      = "coordinator-service-pdb"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  spec {
    min_available = 2
    
    selector {
      match_labels = {
        app = "coordinator-service"
      }
    }
  }
}

# Create ServiceMonitors for Prometheus scraping
resource "kubernetes_manifest" "discovery_service_monitor" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    
    metadata = {
      name      = "discovery-service-monitor"
      namespace = kubernetes_namespace.agent_network.metadata[0].name
      labels = {
        app = "discovery-service"
      }
    }
    
    spec = {
      selector = {
        matchLabels = {
          app = "discovery-service"
        }
      }
      
      endpoints = [{
        port     = "metrics"
        interval = "30s"
        path     = "/metrics"
      }]
    }
  }
}

resource "kubernetes_manifest" "coordinator_service_monitor" {
  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    
    metadata = {
      name      = "coordinator-service-monitor"
      namespace = kubernetes_namespace.agent_network.metadata[0].name
      labels = {
        app = "coordinator-service"
      }
    }
    
    spec = {
      selector = {
        matchLabels = {
          app = "coordinator-service"
        }
      }
      
      endpoints = [{
        port     = "metrics"
        interval = "30s"
        path     = "/metrics"
      }]
    }
  }
}

# Create NetworkPolicies for security
resource "kubernetes_network_policy" "agent_network_policy" {
  metadata {
    name      = "agent-network-policy"
    namespace = kubernetes_namespace.agent_network.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {}  # Apply to all pods in namespace
    }

    policy_types = ["Ingress", "Egress"]

    # Allow ingress from agents and services
    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = kubernetes_namespace.agent_network.metadata[0].name
          }
        }
      }
      
      from {
        namespace_selector {
          match_labels = {
            name = kubernetes_namespace.monitoring.metadata[0].name
          }
        }
      }
    }

    # Allow egress to Redis, services, and external
    egress {
      # Allow DNS
      to {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
      }
      ports {
        port     = "53"
        protocol = "UDP"
      }
    }
    
    egress {
      # Allow internal communication
      to {
        namespace_selector {
          match_labels = {
            name = kubernetes_namespace.agent_network.metadata[0].name
          }
        }
      }
    }
    
    egress {
      # Allow external HTTPS for package downloads, etc.
      ports {
        port     = "443"
        protocol = "TCP"
      }
    }
  }
}