# ArgoCD Setup for log2incident

This directory contains ArgoCD manifests to deploy and manage the log2incident applications and infrastructure on Kubernetes.

## Files
- `namespace.yaml`: Creates the `argocd` namespace for ArgoCD resources.
- `application-helm.yaml`: ArgoCD Application for the main log2incident Helm chart.
- `application-infra.yaml`: ArgoCD Application for infrastructure components (YAML manifests).

## Usage
1. Install ArgoCD in your cluster (see https://argo-cd.readthedocs.io/en/stable/getting_started/).
2. Apply the namespace and application manifests:
   ```sh
   kubectl apply -f deploy/argocd/namespace.yaml
   kubectl apply -f deploy/argocd/application-helm.yaml
   kubectl apply -f deploy/argocd/application-infra.yaml
   ```
3. Access the ArgoCD UI to monitor and manage deployments.

## Notes
- Update `repoURL` in the Application manifests to your actual repository URL if different.
- The sync policy is set to automated for continuous delivery.
