"""
Kafka Billing Pipeline - Real-time event processing system for terminal operations.

A comprehensive real-time billing system built with Apache Kafka that demonstrates
event-driven architecture for processing terminal operations and generating billing events.
"""

__version__ = "1.0.0"
__author__ = "Ryan Gauthier"
__email__ = "ryan.gauthier@example.com"

# Remove imports to prevent circular import issues
# The modules should be imported directly when needed

__all__ = [
    "TerminalEventProducer",
    "BillingProcessor", 
    "BillingAnalytics",
    "BillingDashboard",
    "Config",
] 