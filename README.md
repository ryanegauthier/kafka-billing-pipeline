# 🚢 Kafka Billing Pipeline - Real-Time Event Processing

A comprehensive real-time billing system built with Apache Kafka that demonstrates event-driven architecture for processing terminal operations and generating billing events.

## 🏗️ Architecture Overview

```
Terminal Events → Kafka → Real-time Processing → PostgreSQL → Analytics Dashboard
```

### Components:
- **Apache Kafka**: Message broker for event streaming
- **PostgreSQL**: Data warehouse for billing events
- **Python Producers/Consumers**: Event processing pipeline
- **Real-time Dashboard**: Live monitoring and analytics

## 🚀 Key Features

### Real-Time Event Processing
- **Event Types**: Container moves, truck entries, cargo loading, storage fees, customs checks
- **Multiple Terminals**: Seattle, Los Angeles, New York, Houston ports
- **Customer Management**: MAERSK, FEDEX, UPS, DHL, CMA_CGM, MSC
- **Business Rules**: Volume discounts, rush hour surcharges, validation

## ⚡ Quick Reference

### Start Everything
```bash
make setup          # First time setup
make docker-up      # Start containers
make start-pipeline # Start pipeline
make run-web-dashboard # Start web interface (optional)
```

### Stop Everything
```bash
make shutdown       # Complete shutdown
```

### Individual Commands
```bash
make start-pipeline # Start all components
make stop-pipeline  # Stop all components
make docker-up      # Start containers
make docker-down    # Stop containers
make run-web-dashboard # Start web interface
```

### Kafka Features Demonstrated
- **Partitioning**: Events partitioned by terminal ID for ordering
- **Consumer Groups**: Scalable event processing
- **Fault Tolerance**: Automatic offset management
- **High Throughput**: Configurable event rates

### Data Processing Pipeline
- **Event Validation**: Data quality checks and business rules
- **Real-time Transformations**: Dynamic pricing and discounts
- **Database Storage**: ACID-compliant event persistence
- **Analytics**: Real-time dashboards and reporting

## 📁 Project Structure

```
kafka-billing-pipeline/
├── kafka_billing_pipeline/     # Main package
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Configuration management
│   ├── producer.py            # Kafka event producer
│   ├── billing_processor.py   # Kafka event consumer
│   ├── analytics.py           # Analytics dashboard
│   ├── monitoring.py          # Real-time monitoring
│   ├── utils.py               # Utility functions
│   └── tests/                 # Test suite
│       ├── __init__.py
│       └── test_producer.py
├── docker-compose.yml          # Container orchestration
├── init.sql                    # Database schema and test data
├── pyproject.toml             # Modern Python packaging
├── Makefile                   # Development tasks
├── start_pipeline.py          # Pipeline process manager
├── test_connections.py         # Connection testing
└── README.md                   # This file
```

## 🛠️ Setup Instructions

### Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kafka-billing-pipeline
   ```

2. **Complete setup with one command**
   ```bash
   make setup
   ```

3. **Or for development environment**
   ```bash
   make dev-setup
   ```

### AWS Production Deployment

For production deployment on AWS with CI/CD:

1. **Follow the complete deployment guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Infrastructure as Code**: Terraform configuration included
3. **CI/CD Pipeline**: GitHub Actions for automated deployment
4. **Monitoring**: CloudWatch integration and health checks

**Cost-Effective Options**:
- **Free Tier**: $0/month for first 12 months (Perfect for learning!)
- **Minimal Production**: ~$20-30/month (Small projects)
- **Full Production**: ~$160/month (Enterprise workloads)

**Quick AWS Setup**:
```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
./deploy.sh deploy  # Choose your deployment tier
```

**📊 Cost Analysis**: See [COST_ANALYSIS.md](COST_ANALYSIS.md) for detailed pricing breakdown.

### Shutdown Instructions

#### Complete Shutdown
```bash
# Stop everything (pipeline + containers + cleanup)
make shutdown
```

#### Partial Shutdown
```bash
# Stop just the pipeline components
make stop-pipeline

# Stop just the Docker containers
make docker-down

# Stop individual components
# (Use Ctrl+C in the terminal where they're running)
```

### Manual Setup

#### 1. Start Infrastructure
```bash
# Start Kafka, Zookeeper, and PostgreSQL
docker-compose up -d

# Verify containers are running
docker ps
```

#### 2. Setup Python Environment
```bash
# Create virtual environment
python -m venv kafka-env
source kafka-env/bin/activate  # On Windows: kafka-env\Scripts\activate

# Install package in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

#### 3. Test Connections
```bash
python test_connections.py
```

## 🌐 Web Dashboard

The project includes a **real-time web dashboard** for monitoring your Kafka billing pipeline:

### Features
- **Live Statistics**: Total events, revenue, and activity metrics
- **Real-time Updates**: Auto-refreshes every 5 seconds
- **Event Analytics**: Breakdown by type, customer, and terminal
- **Recent Activity**: Latest billing events with timestamps
- **API Endpoints**: RESTful API for data access

### Access the Dashboard
```bash
# Start the web dashboard
make run-web-dashboard

# Or directly with Python
python web_dashboard.py
```

The dashboard will be available at: **http://localhost:5000**

### Prerequisites
Before starting the web dashboard, ensure:
1. **Docker containers are running**: `make docker-up`
2. **Pipeline is generating data**: `make start-pipeline` (optional, for live data)
3. **Flask is installed**: Included in project dependencies

## 🎯 Usage Examples

### Using Make Commands (Recommended)
```bash
# Start individual components
make run-producer      # Start event producer
make run-consumer      # Start billing processor  
make run-analytics     # Start analytics dashboard
make run-dashboard     # Start monitoring dashboard
make run-web-dashboard # Start web interface

# Start complete pipeline (with proper process management)
make start-pipeline    # Start all components together
make stop-pipeline     # Stop all components
make pipeline-status   # Check pipeline status

# Infrastructure management
make docker-up         # Start Docker containers
make docker-down       # Stop Docker containers

# Check system status
make check-status      # Check all components

# Complete shutdown
make shutdown          # Stop pipeline + containers + cleanup
```

### Using Python Modules
```bash
# Start Event Producer (Simulate Terminal Events)
python -m kafka_billing_pipeline.producer

# Start Event Consumer (Process Events)
python -m kafka_billing_pipeline.billing_processor

# Monitor Real-Time Analytics
python -m kafka_billing_pipeline.analytics

# Start Monitoring Dashboard
python -m kafka_billing_pipeline.monitoring

# Start Web Dashboard
python web_dashboard.py

# Or use the pipeline manager for complete control
python start_pipeline.py start    # Start all components
python start_pipeline.py stop     # Stop all components
python start_pipeline.py status   # Check status
```

### Using Console Scripts (After Installation)
```bash
# Install with console scripts
pip install -e .

# Use command-line tools
kafka-producer
kafka-consumer
kafka-analytics
kafka-dashboard
kafka-web-dashboard
```

## 📊 Business Logic Examples

### Volume Discounts
- **MAERSK & MSC**: 5% discount on transactions > $300
- **Automatic Application**: Applied during event processing

### Rush Hour Surcharges
- **Time-based**: 7-9 AM and 5-7 PM
- **Event Types**: Container moves and cargo loading
- **Surcharge**: 10% additional fee

### Event Validation
- **Amount Ranges**: Validated per event type
- **Required Fields**: Complete data validation
- **Duplicate Prevention**: Event ID uniqueness

## 🔧 Configuration

### Event Types and Pricing
```python
amount_ranges = {
    'CONTAINER_MOVE': (150, 500),
    'TRUCK_ENTRY': (25, 75),
    'CARGO_LOAD': (200, 800),
    'STORAGE_FEE': (50, 200),
    'CUSTOMS_CHECK': (100, 300)
}
```

### Terminal Configuration
```python
terminals = {
    'SEA001': {'location': 'Seattle Port', 'type': 'Container Terminal'},
    'LAX002': {'location': 'Los Angeles Port', 'type': 'Cargo Terminal'},
    'NYC003': {'location': 'New York Port', 'type': 'Mixed Terminal'},
    'HOU004': {'location': 'Houston Port', 'type': 'Oil Terminal'}
}
```

## 📈 Performance Metrics

### Typical Performance
- **Event Processing Rate**: 100+ events/second
- **Latency**: < 100ms end-to-end
- **Throughput**: Scalable based on partitions
- **Reliability**: 99.9%+ event delivery

### Scaling Considerations
- **Partitions**: 3 partitions for parallel processing
- **Consumer Groups**: Multiple consumers for load balancing
- **Database**: Indexed for fast queries
- **Monitoring**: Real-time performance tracking

## 🎓 Learning Outcomes

This project demonstrates:

### Kafka Concepts
- **Event Streaming**: Real-time data flow
- **Producer/Consumer Pattern**: Decoupled processing
- **Partitioning**: Scalable message distribution
- **Consumer Groups**: Load balancing and fault tolerance

### Real-Time Processing
- **Event Validation**: Data quality assurance
- **Business Rules**: Dynamic pricing and discounts
- **State Management**: Event persistence and analytics
- **Monitoring**: Live system observability

### System Design
- **Microservices**: Decoupled event processing
- **Event-Driven Architecture**: Asynchronous communication
- **Data Pipeline**: End-to-end event flow
- **Operational Excellence**: Monitoring and alerting

## 🔍 Troubleshooting

### Common Issues
1. **Connection Errors**: Ensure Docker containers are running
2. **Missing Dependencies**: Run `pip install -e .`
3. **Database Errors**: Check PostgreSQL connection settings
4. **Kafka Errors**: Verify topic creation and broker connectivity
5. **Process Won't Stop**: Use `make shutdown` for complete cleanup

### Debug Commands
```bash
# Check container status
docker ps

# View Kafka logs
docker logs kafka

# Test database connection
python test_connections.py

# Monitor Kafka topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Check pipeline status
make pipeline-status

# Force cleanup if processes are stuck
make stop-pipeline
make docker-down
```

### Shutdown Issues
If components won't stop properly:
```bash
# Complete shutdown with cleanup
make shutdown

# If that doesn't work, force kill all Python processes
# (Windows)
taskkill /f /im python.exe

# (Linux/Mac)
pkill -f "kafka_billing_pipeline"
```

## 🚀 Next Steps

### Potential Enhancements
- **Web Dashboard**: Flask/FastAPI web interface
- **Alerting**: Slack/email notifications for anomalies
- **Data Lake**: Integration with big data platforms
- **Machine Learning**: Predictive pricing models
- **API Gateway**: RESTful event ingestion
- **Multi-region**: Geographic event distribution

### Production Considerations
- **Security**: Authentication and encryption
- **Monitoring**: Prometheus/Grafana integration
- **Logging**: Structured logging with ELK stack
- **Testing**: Unit and integration tests
- **CI/CD**: Automated deployment pipeline

---

**Built with ❤️ using Apache Kafka, PostgreSQL, and Python**

*This project demonstrates real-time event processing capabilities suitable for production billing systems.* 