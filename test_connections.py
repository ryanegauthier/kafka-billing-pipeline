# test_connections.py
import psycopg2
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
import json
import time

# Import configuration
try:
    from kafka_billing_pipeline.config import config
except ImportError:
    # Fallback for when package is not installed
    class Config:
        kafka = type('obj', (object,), {
            'bootstrap_servers': ['localhost:9092'],
            'topic_name': 'terminal-events'
        })()
        database = type('obj', (object,), {
            'host': 'localhost',
            'database': 'billing',
            'user': 'admin',
            'password': 'password'
        })()
    
    config = Config()

def test_postgres():
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=config.database.host,
            database=config.database.database,
            user=config.database.user,
            password=config.database.password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM billing_events;")
        count = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected! Found {count} test records.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_kafka():
    """Test Kafka connection and create topic"""
    try:
        # Test producer connection
        producer = KafkaProducer(
            bootstrap_servers=config.kafka.bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Create topic if it doesn't exist
        admin_client = KafkaAdminClient(bootstrap_servers=config.kafka.bootstrap_servers)
        
        topic_list = [NewTopic(name=config.kafka.topic_name, num_partitions=3, replication_factor=1)]
        try:
            admin_client.create_topics(new_topics=topic_list, validate_only=False)
            print(f"✅ Created '{config.kafka.topic_name}' topic")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"✅ '{config.kafka.topic_name}' topic already exists")
            else:
                print(f"⚠️  Topic creation issue: {e}")
        
        # Test sending a message
        test_message = {"test": "connection", "timestamp": time.time()}
        producer.send(config.kafka.topic_name, value=test_message)
        producer.flush()
        producer.close()
        
        print("✅ Kafka producer working!")
        return True
        
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

def main():
    print("🧪 Testing connections...\n")
    
    postgres_ok = test_postgres()
    kafka_ok = test_kafka()
    
    if postgres_ok and kafka_ok:
        print("\n🎉 All systems ready! You can start building the pipeline.")
    else:
        print("\n⚠️  Some connections failed. Check Docker containers with 'docker ps'")

if __name__ == "__main__":
    main()