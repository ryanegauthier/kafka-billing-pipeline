"""
Terminal event producer for the Kafka Billing Pipeline.
"""

from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime
import uuid
import logging
import sys

from .config import config

logger = logging.getLogger(__name__)


class TerminalEventProducer:
    """Produces terminal events to Kafka for billing processing."""
    
    def __init__(self, bootstrap_servers=None):
        if bootstrap_servers is None:
            bootstrap_servers = config.kafka.bootstrap_servers
            
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            acks='all',  # Wait for all replicas to acknowledge
            retries=3    # Retry failed sends
        )
        
        # Use configuration for event data
        self.customers = config.events.customers
        self.trucking_companies = config.events.trucking_companies
        self.terminals = config.events.terminals
        
    def generate_container_move_event(self):
        """Generate a container movement event"""
        return {
            'event_id': str(uuid.uuid4()),
            'event_type': 'CONTAINER_MOVE',
            'terminal_id': random.choice(self.terminals),
            'container_id': f'CONT{random.randint(100000, 999999)}',
            'customer_code': random.choice(self.customers),
            'move_type': random.choice(['LOAD', 'DISCHARGE', 'SHIFT', 'RESTOW']),
            'timestamp': datetime.now().isoformat(),
            'equipment_used': random.choice(['CRANE_01', 'CRANE_02', 'RTG_03', 'RTG_04']),
            'yard_location': f'Y{random.randint(1,20)}-{random.randint(1,50)}-{random.randint(1,6)}',
            'vessel_name': random.choice(['EVER_GIVEN', 'MSC_GULSUN', 'MADRID_MAERSK']),
            'size': random.choice(['20FT', '40FT', '45FT'])
        }
    
    def generate_truck_entry_event(self):
        """Generate a truck gate entry event"""
        return {
            'event_id': str(uuid.uuid4()),
            'event_type': 'TRUCK_ENTRY',
            'terminal_id': random.choice(self.terminals),
            'truck_id': f'TRK{random.randint(1000, 9999)}',
            'driver_license': f'DL{random.randint(100000, 999999)}',
            'customer_code': random.choice(self.trucking_companies),
            'entry_type': random.choice(['PICKUP', 'DELIVERY', 'EMPTY_RETURN']),
            'timestamp': datetime.now().isoformat(),
            'gate_used': random.choice(['GATE_A', 'GATE_B', 'GATE_C']),
            'container_id': f'CONT{random.randint(100000, 999999)}' if random.random() > 0.3 else None,
            'appointment_time': datetime.now().isoformat(),
            'chassis_number': f'CHS{random.randint(10000, 99999)}'
        }
    
    def generate_storage_event(self):
        """Generate a container storage billing event"""
        return {
            'event_id': str(uuid.uuid4()),
            'event_type': 'STORAGE_BILLING',
            'terminal_id': random.choice(self.terminals),
            'container_id': f'CONT{random.randint(100000, 999999)}',
            'customer_code': random.choice(self.customers),
            'storage_days': random.randint(1, 30),
            'timestamp': datetime.now().isoformat(),
            'container_size': random.choice(['20FT', '40FT', '45FT']),
            'storage_type': random.choice(['STANDARD', 'REEFER', 'HAZMAT']),
            'yard_location': f'Y{random.randint(1,20)}-{random.randint(1,50)}-{random.randint(1,6)}'
        }
    
    def start_producing(self, events_per_minute=None):
        """Start producing events at specified rate"""
        if events_per_minute is None:
            events_per_minute = config.events.events_per_minute
            
        print(f"🚢 Starting terminal event production ({events_per_minute} events/min)...")
        print("Press Ctrl+C to stop\n")
        
        event_count = 0
        
        try:
            while True:
                # Generate different types of events with realistic distribution
                event_type_rand = random.random()
                distribution = config.events.event_distribution
                
                if event_type_rand < distribution['CONTAINER_MOVE']:
                    event = self.generate_container_move_event()
                elif event_type_rand < distribution['CONTAINER_MOVE'] + distribution['TRUCK_ENTRY']:
                    event = self.generate_truck_entry_event()
                else:
                    event = self.generate_storage_event()
                
                # Send to Kafka
                self.producer.send(config.kafka.topic_name, value=event)
                
                event_count += 1
                logger.info(f"📦 [{event_count:4d}] {event['event_type']:15} | {event['customer_code']:10} | {event['event_id'][:8]}...")
                
                # Wait based on desired events per minute
                sleep_time = 60.0 / events_per_minute
                time.sleep(sleep_time + random.uniform(-0.2, 0.2))  # Add some jitter
                
        except KeyboardInterrupt:
            logger.info(f"\n🛑 Stopping producer... Sent {event_count} events total")
            self.producer.flush()  # Make sure all messages are sent
            self.producer.close()
            logger.info("✅ Producer shutdown complete")

def main():
    """Main entry point for the producer."""
    try:
        print("Initializing producer...")
        producer = TerminalEventProducer()
        print("Producer initialized successfully")
        producer.start_producing()
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()