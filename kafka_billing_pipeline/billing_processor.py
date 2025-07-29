"""
Billing processor for the Kafka Billing Pipeline.
"""

from kafka import KafkaConsumer
import json
import psycopg2
from datetime import datetime
import logging

from .config import config

logger = logging.getLogger(__name__)


class BillingProcessor:
    """Processes billing events from Kafka and stores them in PostgreSQL."""
    
    def __init__(self):
        # Kafka consumer setup
        self.consumer = KafkaConsumer(
            config.kafka.topic_name,
            bootstrap_servers=config.kafka.bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id=config.kafka.group_id,
            auto_offset_reset=config.kafka.auto_offset_reset,
            enable_auto_commit=config.kafka.enable_auto_commit,
            auto_commit_interval_ms=config.kafka.auto_commit_interval_ms
        )
        
        # Database connection
        self.db_conn = psycopg2.connect(
            host=config.database.host,
            database=config.database.database,
            user=config.database.user,
            password=config.database.password,
            port=config.database.port
        )
        
        # Use configuration for pricing rules
        self.pricing_rules = {
            'CONTAINER_MOVE': config.pricing.container_move_pricing,
            'TRUCK_ENTRY': config.pricing.truck_entry_pricing,
            'STORAGE_BILLING': config.pricing.storage_pricing
        }
        
        # Use configuration for type multipliers
        self.type_multipliers = config.pricing.type_multipliers
        
        self.processed_count = 0
        
    def calculate_billing_amount(self, event):
        """Calculate billing amount based on event type and details"""
        event_type = event['event_type']
        amount = 0.0
        
        if event_type == 'CONTAINER_MOVE':
            move_type = event.get('move_type', 'SHIFT')
            amount = self.pricing_rules['CONTAINER_MOVE'].get(move_type, 0.0)
            
            # Size adjustment for container moves
            if event.get('size') == '45FT':
                amount *= 1.2  # 45ft containers cost 20% more
                
        elif event_type == 'TRUCK_ENTRY':
            entry_type = event.get('entry_type', 'PICKUP')
            amount = self.pricing_rules['TRUCK_ENTRY'].get(entry_type, 0.0)
            
        elif event_type == 'STORAGE_BILLING':
            container_size = event.get('container_size', '20FT')
            storage_days = event.get('storage_days', 1)
            daily_rate = self.pricing_rules['STORAGE_BILLING'].get(container_size, 8.50)
            
            # Apply type multiplier
            storage_type = event.get('storage_type', 'STANDARD')
            multiplier = self.type_multipliers.get(storage_type, 1.0)
            
            amount = daily_rate * storage_days * multiplier
            
        return round(amount, 2)
    
    def process_billing_event(self, event):
        """Process a single billing event and store in database"""
        try:
            amount = self.calculate_billing_amount(event)
            
            if amount > 0:
                cursor = self.db_conn.cursor()
                
                # Insert billing record
                cursor.execute("""
                    INSERT INTO billing_events 
                    (event_id, terminal_id, event_type, container_id, customer_code, 
                     amount, event_data, processed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                """, (
                    event['event_id'],
                    event['terminal_id'],
                    event['event_type'],
                    event.get('container_id') or event.get('truck_id'),
                    event['customer_code'],
                    amount,
                    json.dumps(event),  # Store full event data as JSON
                    datetime.now()
                ))
                
                # Check if record was actually inserted (not a duplicate)
                if cursor.rowcount > 0:
                    self.db_conn.commit()
                    self.processed_count += 1
                    
                    logger.info(f"💰 [{self.processed_count:4d}] {event['event_type']:15} | "
                              f"{event['customer_code']:10} | ${amount:8.2f} | "
                              f"{event['event_id'][:8]}...")
                else:
                    logger.warning(f"⚠️  Duplicate event ignored: {event['event_id'][:8]}...")
                    
                cursor.close()
                
            else:
                logger.warning(f"⚠️  No billing rule for event: {event['event_type']}")
                
        except Exception as e:
            logger.error(f"❌ Database error processing {event['event_id'][:8]}: {e}")
            self.db_conn.rollback()
    
    def start_processing(self):
        """Start consuming and processing billing events"""
        logger.info("🏭 Starting billing processor...")
        logger.info(f"Waiting for events from Kafka topic '{config.kafka.topic_name}'...")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            for message in self.consumer:
                try:
                    event = message.value
                    # Validate event has required fields
                    if not all(key in event for key in ['event_id', 'event_type', 'customer_code']):
                        logger.warning(f"⚠️  Skipping malformed event: {event}")
                        continue
                        
                    self.process_billing_event(event)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to decode message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    continue
                
        except KeyboardInterrupt:
            logger.info(f"\n🛑 Stopping billing processor... Processed {self.processed_count} events total")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            self.consumer.close()
            self.db_conn.close()
            logger.info("✅ Billing processor shutdown complete")


def main():
    """Main entry point for the billing processor."""
    processor = BillingProcessor()
    processor.start_processing()


if __name__ == "__main__":
    main()