"""
Utility functions for the Kafka Billing Pipeline.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('kafka_billing_pipeline.log')
        ]
    )


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"${amount:,.2f}"


def validate_event(event: Dict[str, Any]) -> bool:
    """Validate that an event has all required fields."""
    required_fields = ['event_id', 'event_type', 'customer_code']
    return all(field in event for field in required_fields)


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError) as e:
        logging.warning(f"Failed to serialize object to JSON: {e}")
        return json.dumps({"error": "Serialization failed", "data": str(obj)})


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logging.warning(f"Could not parse timestamp: {timestamp_str}")
            return None


def calculate_processing_rate(events: int, duration_seconds: float) -> float:
    """Calculate events per second processing rate."""
    if duration_seconds <= 0:
        return 0.0
    return events / duration_seconds


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_event_summary(event: Dict[str, Any]) -> str:
    """Get a summary string for an event."""
    event_type = event.get('event_type', 'UNKNOWN')
    customer = event.get('customer_code', 'UNKNOWN')
    terminal = event.get('terminal_id', 'UNKNOWN')
    event_id = event.get('event_id', 'UNKNOWN')[:8]
    
    return f"{event_type} | {customer} | {terminal} | {event_id}..."


def create_error_event(original_event: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Create an error event for failed processing."""
    return {
        'event_id': generate_event_id(),
        'event_type': 'ERROR',
        'original_event_id': original_event.get('event_id'),
        'error_message': error,
        'timestamp': datetime.now().isoformat(),
        'terminal_id': original_event.get('terminal_id'),
        'customer_code': original_event.get('customer_code'),
        'amount': 0.0
    } 