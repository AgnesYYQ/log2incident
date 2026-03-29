# Kubernetes provider for AKS (assumes kubeconfig is set up)
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

# Example VPA for etl-consumer deployment
# Note: VPA is not a built-in Kubernetes resource; you must install the VPA CRDs and controller first.
resource "kubernetes_manifest" "etl_consumer_vpa" {
  manifest = {
    "apiVersion" = "autoscaling.k8s.io/v1"
    "kind" = "VerticalPodAutoscaler"
    "metadata" = {
      "name" = "etl-consumer-vpa"
      "namespace" = "default"
    }
    "spec" = {
      "targetRef" = {
        "apiVersion" = "apps/v1"
        "kind" = "Deployment"
        "name" = "etl-consumer"
      }
      "updatePolicy" = {
        "updateMode" = "Auto"
      }
      "resourcePolicy" = {
        "containerPolicies" = [
          {
            "containerName" = "*"
            "minAllowed" = {
              "cpu" = "100m"
              "memory" = "256Mi"
            }
            "maxAllowed" = {
              "cpu" = "2"
              "memory" = "4Gi"
            }
          }
        ]
      }
    }
  }
}
