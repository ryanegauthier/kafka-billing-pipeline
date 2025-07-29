terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "kafka-billing-pipeline-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking (Free Tier)
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "kafka-billing-vpc-free"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]  # Only 2 AZs to save costs
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true  # Use single NAT gateway to save costs
  enable_vpn_gateway = false

  tags = var.common_tags
}

# Security Groups
resource "aws_security_group" "ecs_sg" {
  name        = "kafka-billing-ecs-sg-free"
  description = "Security group for ECS tasks"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.common_tags
}

resource "aws_security_group" "rds_sg" {
  name        = "kafka-billing-rds-sg-free"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }

  tags = var.common_tags
}

# RDS PostgreSQL - Free Tier (db.t3.micro for 12 months)
resource "aws_db_subnet_group" "postgres" {
  name       = "kafka-billing-postgres-subnet-group-free"
  subnet_ids = module.vpc.private_subnets

  tags = var.common_tags
}

resource "aws_db_instance" "postgres" {
  identifier = "kafka-billing-postgres-free"

  engine         = "postgres"
  engine_version = "13.12"
  instance_class = "db.t3.micro"  # Free tier eligible

  allocated_storage     = 20
  max_allocated_storage = 20  # Keep it small
  storage_encrypted     = false  # Free tier doesn't include encryption

  db_name  = "billing"
  username = "admin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name

  backup_retention_period = 0  # No backups to save costs
  skip_final_snapshot = true
  deletion_protection = false

  tags = var.common_tags
}

# Alternative: Use RDS Serverless for even lower costs
resource "aws_db_subnet_group" "postgres_serverless" {
  count      = var.use_rds_serverless ? 1 : 0
  name       = "kafka-billing-postgres-serverless-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = var.common_tags
}

resource "aws_rds_cluster" "postgres_serverless" {
  count = var.use_rds_serverless ? 1 : 0

  cluster_identifier = "kafka-billing-postgres-serverless"
  engine             = "aurora-postgresql"
  engine_version     = "13.9"
  database_name      = "billing"
  master_username    = "admin"
  master_password    = var.db_password

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres_serverless[0].name

  skip_final_snapshot = true
  deletion_protection = false

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 1.0
  }

  tags = var.common_tags
}

resource "aws_rds_cluster_instance" "postgres_serverless" {
  count = var.use_rds_serverless ? 1 : 0

  identifier         = "kafka-billing-postgres-serverless-instance"
  cluster_identifier = aws_rds_cluster.postgres_serverless[0].id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.postgres_serverless[0].engine
  engine_version     = aws_rds_cluster.postgres_serverless[0].engine_version

  tags = var.common_tags
}

# ECR Repository (Free tier: 500MB storage, 0.5GB transfer)
resource "aws_ecr_repository" "app" {
  name                 = "kafka-billing-pipeline-free"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false  # Disable to save costs
  }

  tags = var.common_tags
}

# ECS Cluster (Free tier: 2 Fargate tasks)
resource "aws_ecs_cluster" "main" {
  name = "kafka-billing-cluster-free"

  setting {
    name  = "containerInsights"
    value = "disabled"  # Disable to save costs
  }

  tags = var.common_tags
}

# ECS Task Definition - Smaller resources
resource "aws_ecs_task_definition" "app" {
  family                   = "kafka-billing-task-free"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256   # 0.25 vCPU (Free tier)
  memory                   = 512   # 0.5 GB RAM (Free tier)
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "kafka-billing-pipeline"
      image = "${aws_ecr_repository.app.repository_url}:latest"

      portMappings = [
        {
          containerPort = 5000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DB_HOST"
          value = var.use_rds_serverless ? aws_rds_cluster.postgres_serverless[0].endpoint : aws_db_instance.postgres.endpoint
        },
        {
          name  = "DB_NAME"
          value = "billing"
        },
        {
          name  = "DB_USER"
          value = "admin"
        },
        {
          name  = "KAFKA_BOOTSTRAP_SERVERS"
          value = "localhost:9092"  # We'll use a simpler approach
        }
      ]

      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import requests; requests.get('http://localhost:5000/api/stats')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.common_tags
}

# ECS Service - Single instance
resource "aws_ecs_service" "app" {
  name            = "kafka-billing-service-free"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "kafka-billing-pipeline"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.app]

  tags = var.common_tags
}

# Application Load Balancer (Free tier: 15 GB data processing)
resource "aws_lb" "app" {
  name               = "kafka-billing-alb-free"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets

  tags = var.common_tags
}

resource "aws_security_group" "alb_sg" {
  name        = "kafka-billing-alb-sg-free"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.common_tags
}

resource "aws_lb_target_group" "app" {
  name        = "kafka-billing-tg-free"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/api/stats"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = var.common_tags
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# CloudWatch Log Group (Free tier: 5 GB storage, 5 GB ingestion)
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/kafka-billing-pipeline-free"
  retention_in_days = 1  # Keep logs for only 1 day to save costs

  tags = var.common_tags
}

# Secrets Manager (Free tier: 30 days)
resource "aws_secretsmanager_secret" "db_password" {
  name = "kafka-billing/db-password-free"

  tags = var.common_tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

# IAM Roles
resource "aws_iam_role" "ecs_execution_role" {
  name = "kafka-billing-ecs-execution-role-free"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_role_secrets" {
  name = "kafka-billing-ecs-execution-secrets-free"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.db_password.arn
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "kafka-billing-ecs-task-role-free"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.app.dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = var.use_rds_serverless ? aws_rds_cluster.postgres_serverless[0].endpoint : aws_db_instance.postgres.endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost"
  value       = var.use_rds_serverless ? "~$15-25" : "~$20-30 (Free tier eligible for first 12 months)"
} 