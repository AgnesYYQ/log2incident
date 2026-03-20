# AWS Infrastructure (Terraform example)
provider "aws" {
  region = var.region
}

resource "aws_eks_cluster" "main" {
  name     = "log2incident-eks"
  role_arn = var.eks_role_arn
  vpc_config {
    subnet_ids = var.subnet_ids
  }
}

resource "aws_kinesis_stream" "log_stream" {
  name             = "log2incident-stream"
  shard_count      = 1
  retention_period = 24
}

# Add S3, IAM, and other resources as needed
