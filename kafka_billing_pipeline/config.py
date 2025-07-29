"""
Configuration management for the Kafka Billing Pipeline.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class KafkaConfig:
    """Kafka connection and topic configuration."""
    bootstrap_servers: List[str] = None
    topic_name: str = "terminal-events"
    group_id: str = "billing-processor-v2"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 1000
    
    def __post_init__(self):
        if self.bootstrap_servers is None:
            self.bootstrap_servers = ["localhost:9092"]


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str = "localhost"
    database: str = "billing"
    user: str = "admin"
    password: str = "password"
    port: int = 5432


@dataclass
class PricingConfig:
    """Pricing rules and business logic configuration."""
    
    # Container move pricing
    container_move_pricing: Dict[str, float] = None
    
    # Truck entry pricing
    truck_entry_pricing: Dict[str, float] = None
    
    # Storage billing pricing
    storage_pricing: Dict[str, float] = None
    
    # Type multipliers
    type_multipliers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.container_move_pricing is None:
            self.container_move_pricing = {
                'LOAD': 285.00,
                'DISCHARGE': 255.00,
                'SHIFT': 95.00,
                'RESTOW': 125.00
            }
        
        if self.truck_entry_pricing is None:
            self.truck_entry_pricing = {
                'PICKUP': 55.00,
                'DELIVERY': 45.00,
                'EMPTY_RETURN': 25.00
            }
        
        if self.storage_pricing is None:
            self.storage_pricing = {
                '20FT': 8.50,
                '40FT': 12.75,
                '45FT': 15.25
            }
        
        if self.type_multipliers is None:
            self.type_multipliers = {
                'STANDARD': 1.0,
                'REEFER': 1.5,
                'HAZMAT': 2.0
            }


@dataclass
class EventConfig:
    """Event generation and processing configuration."""
    
    # Event generation settings
    events_per_minute: int = 30
    event_distribution: Dict[str, float] = None
    
    # Customer and terminal data
    customers: List[str] = None
    trucking_companies: List[str] = None
    terminals: List[str] = None
    
    def __post_init__(self):
        if self.event_distribution is None:
            self.event_distribution = {
                'CONTAINER_MOVE': 0.5,
                'TRUCK_ENTRY': 0.3,
                'STORAGE_BILLING': 0.2
            }
        
        if self.customers is None:
            self.customers = ['MAERSK', 'COSCO', 'EVERGREEN', 'MSC', 'CMA-CGM']
        
        if self.trucking_companies is None:
            self.trucking_companies = ['FEDEX', 'UPS', 'DHL', 'SCHNEIDER', 'JB_HUNT']
        
        if self.terminals is None:
            self.terminals = ['SEA001', 'LAX002', 'NYC003']


@dataclass
class MonitoringConfig:
    """Monitoring and analytics configuration."""
    refresh_interval: int = 5
    recent_events_limit: int = 200
    dashboard_events_limit: int = 10


class Config:
    """Main configuration class that combines all configuration sections."""
    
    def __init__(self):
        self.kafka = KafkaConfig()
        self.database = DatabaseConfig()
        self.pricing = PricingConfig()
        self.events = EventConfig()
        self.monitoring = MonitoringConfig()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if os.getenv('KAFKA_BOOTSTRAP_SERVERS'):
            config.kafka.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS').split(',')
        
        if os.getenv('DB_HOST'):
            config.database.host = os.getenv('DB_HOST')
        
        if os.getenv('DB_NAME'):
            config.database.database = os.getenv('DB_NAME')
        
        if os.getenv('DB_USER'):
            config.database.user = os.getenv('DB_USER')
        
        if os.getenv('DB_PASSWORD'):
            config.database.password = os.getenv('DB_PASSWORD')
        
        if os.getenv('EVENTS_PER_MINUTE'):
            config.events.events_per_minute = int(os.getenv('EVENTS_PER_MINUTE'))
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            'kafka': {
                'bootstrap_servers': self.kafka.bootstrap_servers,
                'topic_name': self.kafka.topic_name,
                'group_id': self.kafka.group_id,
            },
            'database': {
                'host': self.database.host,
                'database': self.database.database,
                'user': self.database.user,
                'port': self.database.port,
            },
            'events': {
                'events_per_minute': self.events.events_per_minute,
                'terminals': self.events.terminals,
                'customers': self.events.customers,
            }
        }


# Global configuration instance
config = Config() 