# Kubernetes provider for EKS (assumes kubeconfig is set up)
provider "kubernetes" {
  host                   = var.kube_host
  cluster_ca_certificate = base64decode(var.kube_ca)
  token                  = var.kube_token
}

# Example HPA for etl-consumer deployment (custom metric)
resource "kubernetes_horizontal_pod_autoscaler_v2" "etl_consumer" {
  metadata {
    name      = "etl-consumer-hpa"
    namespace = "default"
  }
  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = "etl-consumer"
    }
    min_replicas = 2
    max_replicas = 20
    metric {
      type = "External"
      external {
        metric {
          name = "queue_length"
          selector {
            match_labels = {
              queue = "my-kafka-topic"
            }
          }
        }
        target {
          type  = "Value"
          value = "100"
        }
      }
    }
  }
}
