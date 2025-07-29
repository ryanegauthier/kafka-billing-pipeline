"""
Analytics module for the Kafka Billing Pipeline.
"""

import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import logging

from .config import config

logger = logging.getLogger(__name__)


class BillingAnalytics:
    """Provides analytics and reporting for billing events."""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.database.host,
            database=config.database.database,
            user=config.database.user,
            password=config.database.password,
            port=config.database.port
        )
    
    def get_real_time_stats(self):
        """Get current billing statistics - recent records to avoid timezone issues"""
        query = """
        SELECT 
            COUNT(*) as total_events,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_amount,
            MIN(processed_at) as first_event,
            MAX(processed_at) as latest_event
        FROM (
            SELECT * FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT %s
        ) recent_events;
        """
        return pd.read_sql(query, self.conn, params=(config.monitoring.recent_events_limit,))
    
    def get_revenue_by_event_type(self):
        """Revenue breakdown by event type - recent records"""
        query = """
        SELECT 
            event_type,
            COUNT(*) as event_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_revenue
        FROM (
            SELECT * FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT %s
        ) recent_events
        GROUP BY event_type
        ORDER BY total_revenue DESC;
        """
        return pd.read_sql(query, self.conn, params=(config.monitoring.recent_events_limit,))
    
    def get_top_customers(self):
        """Top customers by revenue - recent records"""
        query = """
        SELECT 
            customer_code,
            COUNT(*) as total_events,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_per_event
        FROM (
            SELECT * FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT %s
        ) recent_events
        GROUP BY customer_code
        ORDER BY total_revenue DESC
        LIMIT 10;
        """
        return pd.read_sql(query, self.conn, params=(config.monitoring.recent_events_limit,))
    
    def get_terminal_performance(self):
        """Performance by terminal - recent records"""
        query = """
        SELECT 
            terminal_id,
            COUNT(*) as total_events,
            SUM(amount) as total_revenue,
            COUNT(DISTINCT customer_code) as unique_customers
        FROM (
            SELECT * FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT %s
        ) recent_events
        GROUP BY terminal_id
        ORDER BY total_revenue DESC;
        """
        return pd.read_sql(query, self.conn, params=(config.monitoring.recent_events_limit,))
    
    def get_recent_events(self, limit=None):
        """Get most recent billing events"""
        if limit is None:
            limit = config.monitoring.dashboard_events_limit
            
        query = """
        SELECT 
            event_type,
            customer_code,
            amount,
            terminal_id,
            processed_at,
            event_id
        FROM billing_events 
        ORDER BY processed_at DESC
        LIMIT %s;
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_dashboard(self):
        """Print a live dashboard"""
        self.clear_screen()
        
        print("=" * 80)
        print("🏢 TERMINAL BILLING DASHBOARD - LIVE DATA")
        print("=" * 80)
        print(f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Overall stats
            stats = self.get_real_time_stats()
            if not stats.empty and stats.iloc[0]['total_events'] > 0:
                row = stats.iloc[0]
                print("📊 OVERVIEW (Recent Events)")
                print("-" * 40)
                print(f"Total Events:     {row['total_events']:,}")
                print(f"Total Revenue:    ${row['total_revenue']:,.2f}")
                print(f"Average Amount:   ${row['avg_amount']:,.2f}")
                print()
                
                # Revenue by event type
                event_revenue = self.get_revenue_by_event_type()
                if not event_revenue.empty:
                    print("💰 REVENUE BY EVENT TYPE")
                    print("-" * 50)
                    for _, row in event_revenue.iterrows():
                        print(f"{row['event_type']:15} | {row['event_count']:4d} events | ${row['total_revenue']:8,.2f}")
                    print()
                
                # Top customers
                customers = self.get_top_customers()
                if not customers.empty:
                    print("🏆 TOP CUSTOMERS (Revenue)")
                    print("-" * 50)
                    for _, row in customers.iterrows():
                        print(f"{row['customer_code']:12} | {row['total_events']:4d} events | ${row['total_revenue']:8,.2f}")
                    print()
                
                # Terminal performance
                terminals = self.get_terminal_performance()
                if not terminals.empty:
                    print("🚢 TERMINAL PERFORMANCE")
                    print("-" * 50)
                    for _, row in terminals.iterrows():
                        print(f"{row['terminal_id']:8} | {row['total_events']:4d} events | ${row['total_revenue']:8,.2f} | {row['unique_customers']:2d} customers")
                    print()
                
                # Recent events
                recent = self.get_recent_events(8)
                if recent:
                    print("🕐 RECENT EVENTS (Last 8)")
                    print("-" * 75)
                    print("Event Type      | Customer   | Amount   | Terminal | Time")
                    print("-" * 75)
                    for event in recent:
                        event_type, customer, amount, terminal, timestamp, event_id = event
                        time_str = timestamp.strftime('%H:%M:%S')
                        print(f"{event_type:15} | {customer:10} | ${amount:6.2f} | {terminal:8} | {time_str}")
                
            else:
                print("⏳ Waiting for billing events...")
                print("💡 Make sure the producer and billing processor are running!")
                
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
        
        print()
        print("=" * 80)
        print("🔄 Refreshing every 5 seconds... Press Ctrl+C to stop")
        print("=" * 80)
    
    def start_live_dashboard(self, refresh_seconds=None):
        """Start the live dashboard with auto-refresh"""
        if refresh_seconds is None:
            refresh_seconds = config.monitoring.refresh_interval
            
        print("🚀 Starting live billing dashboard...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.print_dashboard()
                time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")
        finally:
            self.conn.close()


def main():
    """Main entry point for the analytics dashboard."""
    dashboard = BillingAnalytics()
    dashboard.start_live_dashboard()


if __name__ == "__main__":
    main()