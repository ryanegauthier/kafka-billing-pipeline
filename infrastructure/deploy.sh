#!/bin/bash

# AWS Infrastructure Deployment Script for Kafka Billing Pipeline
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    print_status "All requirements met!"
}

# Check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "AWS credentials verified!"
}

# Create S3 bucket for Terraform state
create_terraform_backend() {
    print_status "Setting up Terraform backend..."
    
    BUCKET_NAME="kafka-billing-pipeline-terraform-state"
    REGION="us-east-1"
    
    if ! aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
        print_status "Creating S3 bucket for Terraform state..."
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
        aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" --versioning-configuration Status=Enabled
        aws s3api put-bucket-encryption --bucket "$BUCKET_NAME" --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
        print_status "S3 bucket created successfully!"
    else
        print_status "S3 bucket already exists!"
    fi
}

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    terraform init
    print_status "Terraform initialized!"
}

# Plan Terraform changes
plan_terraform() {
    print_status "Planning Terraform changes..."
    terraform plan -out=tfplan
    print_status "Terraform plan created!"
}

# Apply Terraform changes
apply_terraform() {
    print_status "Applying Terraform changes..."
    terraform apply tfplan
    print_status "Terraform changes applied!"
}

# Get outputs
get_outputs() {
    print_status "Getting infrastructure outputs..."
    
    ALB_DNS=$(terraform output -raw alb_dns_name)
    RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
    MSK_BROKERS=$(terraform output -raw msk_bootstrap_brokers)
    ECR_REPO=$(terraform output -raw ecr_repository_url)
    
    echo ""
    print_status "Infrastructure deployed successfully!"
    echo ""
    echo "📊 Application Load Balancer: http://$ALB_DNS"
    echo "🗄️  RDS PostgreSQL: $RDS_ENDPOINT"
    echo "📨 MSK Kafka Brokers: $MSK_BROKERS"
    echo "🐳 ECR Repository: $ECR_REPO"
    echo ""
    print_warning "Note: It may take 10-15 minutes for all services to be fully ready."
    echo ""
}

# Main deployment function
deploy() {
    print_status "Starting AWS infrastructure deployment..."
    
    # Ask user which deployment type they want
    echo ""
    echo "Choose deployment type:"
    echo "1) Free Tier (First 12 months - $0/month)"
    echo "2) Minimal Production (~$20-30/month)"
    echo "3) Full Production (~$160/month)"
    echo ""
    read -p "Enter your choice (1-3): " deployment_choice
    
    case $deployment_choice in
        1)
            print_status "Using Free Tier configuration..."
            if [[ -f "free-tier.tf" ]]; then
                cp free-tier.tf main.tf.backup
                cp free-tier.tf main.tf
            else
                print_error "Free tier configuration not found!"
                exit 1
            fi
            ;;
        2)
            print_status "Using Minimal Production configuration..."
            if [[ -f "main.tf.backup" ]]; then
                cp main.tf.backup main.tf
            fi
            ;;
        3)
            print_status "Using Full Production configuration..."
            if [[ -f "main.tf.backup" ]]; then
                cp main.tf.backup main.tf
            fi
            ;;
        *)
            print_error "Invalid choice. Using default configuration."
            ;;
    esac
    
    check_requirements
    check_aws_credentials
    create_terraform_backend
    init_terraform
    plan_terraform
    
    echo ""
    print_warning "Review the plan above. Do you want to proceed with deployment? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        apply_terraform
        get_outputs
    else
        print_status "Deployment cancelled."
        exit 0
    fi
}

# Destroy infrastructure
destroy() {
    print_warning "This will destroy all AWS resources. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Destroying infrastructure..."
        terraform destroy -auto-approve
        print_status "Infrastructure destroyed!"
    else
        print_status "Destroy cancelled."
    fi
}

# Show usage
usage() {
    echo "Usage: $0 {deploy|destroy|plan|outputs}"
    echo ""
    echo "Commands:"
    echo "  deploy   - Deploy the complete infrastructure"
    echo "  destroy  - Destroy all infrastructure"
    echo "  plan     - Show Terraform plan"
    echo "  outputs  - Show infrastructure outputs"
    echo ""
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    destroy)
        destroy
        ;;
    plan)
        init_terraform
        terraform plan
        ;;
    outputs)
        get_outputs
        ;;
    *)
        usage
        exit 1
        ;;
esac 