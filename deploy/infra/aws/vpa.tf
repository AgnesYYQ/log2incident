# Example VPA for etl-consumer deployment
# Note: VPA is not a built-in Kubernetes resource; you must install the VPA CRDs and controller first.
# This resource uses the kubernetes_manifest resource (Terraform >= 1.13.0 required)

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
