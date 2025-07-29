variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "kafka-billing-pipeline"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

variable "use_rds_serverless" {
  description = "Use RDS Serverless instead of standard RDS (lower cost but less predictable)"
  type        = bool
  default     = false
} 