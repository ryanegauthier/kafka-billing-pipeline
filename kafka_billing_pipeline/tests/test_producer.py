"""
Tests for the producer module.
"""

import pytest
from unittest.mock import Mock, patch
from kafka_billing_pipeline.producer import TerminalEventProducer
from kafka_billing_pipeline.config import config


class TestTerminalEventProducer:
    """Test cases for TerminalEventProducer."""
    
    def test_init(self):
        """Test producer initialization."""
        with patch('kafka.KafkaProducer'):
            producer = TerminalEventProducer()
            assert producer.customers == config.events.customers
            assert producer.trucking_companies == config.events.trucking_companies
            assert producer.terminals == config.events.terminals
    
    def test_generate_container_move_event(self):
        """Test container move event generation."""
        with patch('kafka.KafkaProducer'):
            producer = TerminalEventProducer()
            event = producer.generate_container_move_event()
            
            assert 'event_id' in event
            assert event['event_type'] == 'CONTAINER_MOVE'
            assert event['terminal_id'] in config.events.terminals
            assert event['customer_code'] in config.events.customers
            assert 'container_id' in event
            assert 'move_type' in event
            assert 'timestamp' in event
    
    def test_generate_truck_entry_event(self):
        """Test truck entry event generation."""
        with patch('kafka.KafkaProducer'):
            producer = TerminalEventProducer()
            event = producer.generate_truck_entry_event()
            
            assert 'event_id' in event
            assert event['event_type'] == 'TRUCK_ENTRY'
            assert event['terminal_id'] in config.events.terminals
            assert event['customer_code'] in config.events.trucking_companies
            assert 'truck_id' in event
            assert 'entry_type' in event
            assert 'timestamp' in event
    
    def test_generate_storage_event(self):
        """Test storage event generation."""
        with patch('kafka.KafkaProducer'):
            producer = TerminalEventProducer()
            event = producer.generate_storage_event()
            
            assert 'event_id' in event
            assert event['event_type'] == 'STORAGE_BILLING'
            assert event['terminal_id'] in config.events.terminals
            assert event['customer_code'] in config.events.customers
            assert 'container_id' in event
            assert 'storage_days' in event
            assert 'timestamp' in event 