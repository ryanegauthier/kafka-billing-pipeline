# 🚀 AWS Deployment Guide for Kafka Billing Pipeline

This guide will help you deploy the Kafka Billing Pipeline to AWS using CI/CD with GitHub Actions and Terraform.

## 📋 Prerequisites

Before starting, ensure you have the following installed:

- **AWS CLI** - [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** - [Install Guide](https://developer.hashicorp.com/terraform/downloads)
- **Docker** - [Install Guide](https://docs.docker.com/get-docker/)
- **Git** - [Install Guide](https://git-scm.com/downloads)

## 🔐 AWS Setup

### 1. Configure AWS Credentials

```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (`json`)

### 2. Create IAM User for CI/CD

Create an IAM user with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:*",
                "ecs:*",
                "iam:PassRole",
                "logs:*",
                "secretsmanager:*",
                "s3:*",
                "rds:*",
                "msk:*",
                "elasticloadbalancing:*",
                "ec2:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🏗️ Infrastructure Deployment

### 1. Configure Terraform Variables

Copy the example configuration:

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region = "us-east-1"
db_password = "your-secure-password-here"

common_tags = {
  Project     = "kafka-billing-pipeline"
  Environment = "production"
  ManagedBy   = "terraform"
  Owner       = "your-team"
}
```

### 2. Deploy Infrastructure

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy the infrastructure
./deploy.sh deploy
```

This will create:
- **VPC** with public and private subnets
- **RDS PostgreSQL** database
- **MSK Kafka** cluster
- **ECS Fargate** cluster
- **Application Load Balancer**
- **ECR** repository
- **CloudWatch** log groups
- **Secrets Manager** for database password

### 3. Verify Deployment

After deployment, you'll see output like:

```
📊 Application Load Balancer: http://kafka-billing-alb-123456789.us-east-1.elb.amazonaws.com
🗄️  RDS PostgreSQL: kafka-billing-postgres.abc123.us-east-1.rds.amazonaws.com:5432
📨 MSK Kafka Brokers: b-1.kafka-billing-cluster.abc123.kafka.us-east-1.amazonaws.com:9092
🐳 ECR Repository: 123456789.dkr.ecr.us-east-1.amazonaws.com/kafka-billing-pipeline
```

## 🔄 CI/CD Setup

### 1. GitHub Repository Setup

1. Push your code to GitHub
2. Go to your repository settings
3. Add the following secrets:
   - `AWS_ACCESS_KEY_ID` - Your AWS access key
   - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

### 2. GitHub Actions Workflow

The CI/CD pipeline is defined in `.github/workflows/deploy.yml` and includes:

1. **Test Stage**: Runs unit tests and coverage
2. **Build Stage**: Builds and pushes Docker image to ECR
3. **Deploy Stage**: Updates ECS service with new image

### 3. Trigger Deployment

The pipeline automatically triggers on:
- Push to `main` branch
- Pull requests to `main` branch

## 🐳 Docker Image

### Build Locally

```bash
# Build the image
docker build -t kafka-billing-pipeline .

# Test locally
docker run -p 5000:5000 kafka-billing-pipeline
```

### Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag kafka-billing-pipeline:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/kafka-billing-pipeline:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/kafka-billing-pipeline:latest
```

## 🌐 Accessing the Application

### Web Dashboard

Once deployed, access your application at:
```
http://your-alb-dns-name
```

### Health Check

Check if the application is healthy:
```bash
curl http://your-alb-dns-name/api/stats
```

## 📊 Monitoring and Logs

### CloudWatch Logs

View application logs:
```bash
aws logs tail /ecs/kafka-billing-pipeline --follow
```

### ECS Service Status

Check service status:
```bash
aws ecs describe-services --cluster kafka-billing-cluster --services kafka-billing-service
```

### Database Connection

Connect to the database:
```bash
psql -h your-rds-endpoint -U admin -d billing
```

## 🔧 Configuration

### Environment Variables

The application uses these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | RDS endpoint | Auto-configured |
| `DB_NAME` | Database name | `billing` |
| `DB_USER` | Database user | `admin` |
| `DB_PASSWORD` | Database password | From Secrets Manager |
| `KAFKA_BOOTSTRAP_SERVERS` | MSK brokers | Auto-configured |

### Scaling

To scale the application:

```bash
# Scale ECS service
aws ecs update-service --cluster kafka-billing-cluster --service kafka-billing-service --desired-count 3
```

## 🛠️ Troubleshooting

### Common Issues

1. **ECS Tasks Not Starting**
   ```bash
   # Check task definition
   aws ecs describe-task-definition --task-definition kafka-billing-task
   
   # Check service events
   aws ecs describe-services --cluster kafka-billing-cluster --services kafka-billing-service
   ```

2. **Database Connection Issues**
   ```bash
   # Check RDS status
   aws rds describe-db-instances --db-instance-identifier kafka-billing-postgres
   
   # Check security groups
   aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
   ```

3. **Kafka Connection Issues**
   ```bash
   # Check MSK cluster status
   aws kafka list-clusters
   
   # Get bootstrap brokers
   aws kafka get-bootstrap-brokers --cluster-arn your-cluster-arn
   ```

### Logs

View logs for debugging:
```bash
# ECS logs
aws logs describe-log-streams --log-group-name /ecs/kafka-billing-pipeline

# Application logs
aws logs filter-log-events --log-group-name /ecs/kafka-billing-pipeline --start-time $(date -d '1 hour ago' +%s)000
```

## 🧹 Cleanup

To destroy all resources:

```bash
cd infrastructure
./deploy.sh destroy
```

**⚠️ Warning**: This will permanently delete all AWS resources and data.

## 📈 Cost Optimization

### Estimated Monthly Costs (us-east-1)

| Service | Instance Type | Monthly Cost |
|---------|---------------|--------------|
| RDS PostgreSQL | db.t3.micro | ~$15 |
| MSK Kafka | kafka.t3.small (3 nodes) | ~$90 |
| ECS Fargate | 1 vCPU, 2GB RAM | ~$30 |
| ALB | Standard | ~$20 |
| ECR | Storage + Transfer | ~$5 |
| **Total** | | **~$160** |

### Cost Optimization Tips

1. **Use Spot Instances** for non-critical workloads
2. **Schedule scaling** during off-hours
3. **Monitor unused resources** with AWS Cost Explorer
4. **Use Reserved Instances** for predictable workloads

## 🔒 Security

### Security Features

- **VPC Isolation**: All resources in private subnets
- **Security Groups**: Restrictive access rules
- **Encryption**: TLS for Kafka, encryption for RDS
- **Secrets Manager**: Secure password storage
- **IAM Roles**: Least privilege access

### Security Best Practices

1. **Rotate credentials** regularly
2. **Monitor CloudTrail** logs
3. **Use AWS Config** for compliance
4. **Enable GuardDuty** for threat detection
5. **Regular security updates**

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review CloudWatch logs
3. Check AWS Service Health Dashboard
4. Open an issue in the GitHub repository

---

**Happy Deploying! 🚀** 