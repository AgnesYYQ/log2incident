# AWS Infrastructure (Terraform example)
provider "aws" {
  region = var.region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
  tags = {
    Name = "log2incident-vpc"
  }
}

# Subnets
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true
  tags = {
    Name = "log2incident-public-a"
  }
}
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.region}b"
  map_public_ip_on_launch = true
  tags = {
    Name = "log2incident-public-b"
  }
}

# IAM Role for EKS
resource "aws_iam_role" "eks_cluster" {
  name = "log2incident-eks-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.eks_assume_role.json
}

data "aws_iam_policy_document" "eks_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

# Attach EKS policies to role
resource "aws_iam_role_policy_attachment" "eks_cluster_AmazonEKSClusterPolicy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}
resource "aws_iam_role_policy_attachment" "eks_cluster_AmazonEKSServicePolicy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
}

# S3 Bucket
resource "aws_s3_bucket" "logs" {
  bucket = "log2incident-logs-${random_id.bucket_id.hex}"
  force_destroy = true
  tags = {
    Name = "log2incident-logs"
  }
}
resource "random_id" "bucket_id" {
  byte_length = 4
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "log2incident-eks"
  role_arn = aws_iam_role.eks_cluster.arn
  vpc_config {
    subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  }
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_AmazonEKSClusterPolicy, aws_iam_role_policy_attachment.eks_cluster_AmazonEKSServicePolicy]
}

# EKS Node Group
resource "aws_iam_role" "eks_node" {
  name = "log2incident-eks-node-role"
  assume_role_policy = data.aws_iam_policy_document.eks_node_assume_role.json
}

data "aws_iam_policy_document" "eks_node_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKSWorkerNodePolicy" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}
resource "aws_iam_role_policy_attachment" "eks_node_AmazonEC2ContainerRegistryReadOnly" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKS_CNI_Policy" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "log2incident-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }
  depends_on = [aws_iam_role_policy_attachment.eks_node_AmazonEKSWorkerNodePolicy, aws_iam_role_policy_attachment.eks_node_AmazonEC2ContainerRegistryReadOnly, aws_iam_role_policy_attachment.eks_node_AmazonEKS_CNI_Policy]
}

# Kinesis Stream
resource "aws_kinesis_stream" "log_stream" {
  name             = "log2incident-stream"
  shard_count      = 1
  retention_period = 24
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "log2incident" {
  name              = "/log2incident/app"
  retention_in_days = 14
}

# DynamoDB Table for Events/Incidents
resource "aws_dynamodb_table" "events" {
  name           = "log2incident-events"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "event_id"
  attribute {
    name = "event_id"
    type = "S"
  }
}
resource "aws_dynamodb_table" "incidents" {
  name           = "log2incident-incidents"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "incident_id"
  attribute {
    name = "incident_id"
    type = "S"
  }
}

# Managed Streaming for Kafka (MSK)
resource "aws_msk_cluster" "main" {
  cluster_name           = "log2incident-msk"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 2
  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups = []
  }
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}
output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}
output "eks_node_group_name" {
  value = aws_eks_node_group.main.node_group_name
}
output "s3_bucket_name" {
  value = aws_s3_bucket.logs.bucket
}
output "kinesis_stream_name" {
  value = aws_kinesis_stream.log_stream.name
}
output "cloudwatch_log_group_name" {
  value = aws_cloudwatch_log_group.log2incident.name
}
output "dynamodb_events_table" {
  value = aws_dynamodb_table.events.name
}
output "dynamodb_incidents_table" {
  value = aws_dynamodb_table.incidents.name
}
output "msk_cluster_name" {
  value = aws_msk_cluster.main.cluster_name
}
