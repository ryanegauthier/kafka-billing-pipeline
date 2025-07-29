"""
Real-time monitoring and analytics for the Kafka Billing Pipeline.
"""

import psycopg2
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
import logging

from .config import config

logger = logging.getLogger(__name__)


class BillingDashboard:
    """Real-time monitoring dashboard for billing events."""
    
    def __init__(self):
        """Initialize dashboard with database connection."""
        self.db_config = {
            'host': config.database.host,
            'database': config.database.database,
            'user': config.database.user,
            'password': config.database.password,
            'port': config.database.port
        }
    
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time processing statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Total events processed
            cursor.execute("SELECT COUNT(*) FROM billing_events;")
            total_events = cursor.fetchone()[0]
            
            # Total amount billed
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM billing_events;")
            total_amount = cursor.fetchone()[0]
            
            # Events in last hour
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM billing_events 
                WHERE created_at >= NOW() - INTERVAL '1 hour';
            """)
            last_hour_events, last_hour_amount = cursor.fetchone()
            
            # Events in last 5 minutes
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM billing_events 
                WHERE created_at >= NOW() - INTERVAL '5 minutes';
            """)
            last_5min_events, last_5min_amount = cursor.fetchone()
            
            return {
                'total_events': total_events,
                'total_amount': total_amount,
                'last_hour_events': last_hour_events,
                'last_hour_amount': last_hour_amount,
                'last_5min_events': last_5min_events,
                'last_5min_amount': last_5min_amount
            }
        finally:
            cursor.close()
            conn.close()
    
    def get_events_by_type(self) -> List[Dict[str, Any]]:
        """Get event counts by type."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT event_type, COUNT(*), SUM(amount)
                FROM billing_events 
                GROUP BY event_type 
                ORDER BY COUNT(*) DESC;
            """)
            
            results = cursor.fetchall()
            return [{'type': row[0], 'count': row[1], 'amount': row[2]} for row in results]
        finally:
            cursor.close()
            conn.close()
    
    def get_events_by_customer(self) -> List[Dict[str, Any]]:
        """Get event counts by customer."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT customer_code, COUNT(*), SUM(amount)
                FROM billing_events 
                GROUP BY customer_code 
                ORDER BY SUM(amount) DESC;
            """)
            
            results = cursor.fetchall()
            return [{'customer': row[0], 'count': row[1], 'amount': row[2]} for row in results]
        finally:
            cursor.close()
            conn.close()
    
    def get_events_by_terminal(self) -> List[Dict[str, Any]]:
        """Get event counts by terminal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT terminal_id, COUNT(*), SUM(amount)
                FROM billing_events 
                GROUP BY terminal_id 
                ORDER BY COUNT(*) DESC;
            """)
            
            results = cursor.fetchall()
            return [{'terminal': row[0], 'count': row[1], 'amount': row[2]} for row in results]
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent events."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT event_id, terminal_id, event_type, customer_code, amount, created_at
                FROM billing_events 
                ORDER BY created_at DESC 
                LIMIT %s;
            """, (limit,))
            
            results = cursor.fetchall()
            return [{
                'event_id': row[0],
                'terminal_id': row[1],
                'event_type': row[2],
                'customer_code': row[3],
                'amount': row[4],
                'created_at': row[5]
            } for row in results]
        finally:
            cursor.close()
            conn.close()
    
    def get_hourly_trends(self) -> List[Dict[str, Any]]:
        """Get hourly event trends for the last 24 hours."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as event_count,
                    SUM(amount) as total_amount
                FROM billing_events 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour;
            """)
            
            results = cursor.fetchall()
            return [{
                'hour': row[0].strftime('%H:00'),
                'event_count': row[1],
                'total_amount': row[2]
            } for row in results]
        finally:
            cursor.close()
            conn.close()
    
    def print_dashboard(self):
        """Print the monitoring dashboard."""
        print("\n" + "="*80)
        print("🚢 KAFKA BILLING PIPELINE - REAL-TIME MONITORING DASHBOARD")
        print("="*80)
        print(f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*80)
        
        try:
            # Real-time stats
            stats = self.get_realtime_stats()
            print("📊 REAL-TIME STATISTICS")
            print(f"   Total Events Processed: {stats['total_events']:,}")
            print(f"   Total Amount Billed: ${stats['total_amount']:,.2f}")
            print(f"   Events (Last Hour): {stats['last_hour_events']:,} (${stats['last_hour_amount']:,.2f})")
            print(f"   Events (Last 5 Min): {stats['last_5min_events']:,} (${stats['last_5min_amount']:,.2f})")
            
            # Processing rate
            if stats['last_5min_events'] > 0:
                rate_per_min = stats['last_5min_events'] / 5
                print(f"   Current Processing Rate: {rate_per_min:.1f} events/minute")
            
            print("\n" + "-"*80)
            
            # Events by type
            print("📋 EVENTS BY TYPE")
            events_by_type = self.get_events_by_type()
            for event in events_by_type:
                print(f"   {event['type']:<15} {event['count']:>6} events  ${event['amount']:>10,.2f}")
            
            print("\n" + "-"*80)
            
            # Top customers
            print("👥 TOP CUSTOMERS BY REVENUE")
            customers = self.get_events_by_customer()
            for customer in customers[:5]:  # Top 5
                print(f"   {customer['customer']:<10} {customer['count']:>6} events  ${customer['amount']:>10,.2f}")
            
            print("\n" + "-"*80)
            
            # Terminal activity
            print("🏭 TERMINAL ACTIVITY")
            terminals = self.get_events_by_terminal()
            for terminal in terminals:
                print(f"   {terminal['terminal']:<8} {terminal['count']:>6} events  ${terminal['amount']:>10,.2f}")
            
            print("\n" + "-"*80)
            
            # Recent events
            print("🕒 RECENT EVENTS")
            recent_events = self.get_recent_events(5)
            for event in recent_events:
                time_str = event['created_at'].strftime('%H:%M:%S')
                print(f"   {time_str} | {event['terminal_id']} | {event['event_type']:<15} | {event['customer_code']:<8} | ${event['amount']:>8,.2f}")
            
            print("\n" + "-"*80)
            
            # Hourly trends
            print("📈 HOURLY TRENDS (Last 24 Hours)")
            hourly_trends = self.get_hourly_trends()
            for trend in hourly_trends[-6:]:  # Last 6 hours
                print(f"   {trend['hour']:<6} {trend['event_count']:>4} events  ${trend['total_amount']:>8,.2f}")
            
            print("="*80)
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            print(f"❌ Dashboard error: {e}")
    
    def run_monitoring(self, refresh_interval: int = None):
        """Run continuous monitoring with refresh."""
        if refresh_interval is None:
            refresh_interval = config.monitoring.refresh_interval
            
        print("🚀 Starting real-time monitoring dashboard...")
        print(f"   Refresh interval: {refresh_interval} seconds")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                self.print_dashboard()
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")


def main():
    """Main entry point for the monitoring dashboard."""
    dashboard = BillingDashboard()
    dashboard.run_monitoring()


if __name__ == "__main__":
    main() 