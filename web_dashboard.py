#!/usr/bin/env python3
"""
Web Dashboard for Kafka Billing Pipeline
A Flask-based web interface for real-time monitoring.
"""

from flask import Flask, render_template, jsonify
import psycopg2
import json
from datetime import datetime, timedelta
from kafka_billing_pipeline.config import config

app = Flask(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=config.database.host,
        database=config.database.database,
        user=config.database.user,
        password=config.database.password,
        port=config.database.port
    )

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get real-time statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Overall stats
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM billing_events;")
        total_events, total_revenue = cursor.fetchone()
        
        # Last hour stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM billing_events 
            WHERE processed_at >= NOW() - INTERVAL '1 hour';
        """)
        last_hour_events, last_hour_revenue = cursor.fetchone()
        
        # Last 5 minutes stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM billing_events 
            WHERE processed_at >= NOW() - INTERVAL '5 minutes';
        """)
        last_5min_events, last_5min_revenue = cursor.fetchone()
        
        # Events by type
        cursor.execute("""
            SELECT event_type, COUNT(*), SUM(amount)
            FROM billing_events 
            GROUP BY event_type 
            ORDER BY COUNT(*) DESC;
        """)
        events_by_type = [{'type': row[0], 'count': row[1], 'amount': row[2]} for row in cursor.fetchall()]
        
        # Top customers
        cursor.execute("""
            SELECT customer_code, COUNT(*), SUM(amount)
            FROM billing_events 
            GROUP BY customer_code 
            ORDER BY SUM(amount) DESC 
            LIMIT 5;
        """)
        top_customers = [{'customer': row[0], 'count': row[1], 'amount': row[2]} for row in cursor.fetchall()]
        
        # Recent events
        cursor.execute("""
            SELECT event_type, customer_code, amount, terminal_id, processed_at
            FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT 10;
        """)
        recent_events = [{
            'event_type': row[0],
            'customer': row[1], 
            'amount': row[2],
            'terminal': row[3],
            'time': row[4].strftime('%H:%M:%S')
        } for row in cursor.fetchall()]
        
        return jsonify({
            'total_events': total_events,
            'total_revenue': total_revenue,
            'last_hour_events': last_hour_events,
            'last_hour_revenue': last_hour_revenue,
            'last_5min_events': last_5min_events,
            'last_5min_revenue': last_5min_revenue,
            'events_by_type': events_by_type,
            'top_customers': top_customers,
            'recent_events': recent_events,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/events')
def get_events():
    """Get recent events for the events table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT event_id, event_type, customer_code, amount, terminal_id, processed_at
            FROM billing_events 
            ORDER BY processed_at DESC 
            LIMIT 50;
        """)
        
        events = [{
            'event_id': row[0][:8] + '...',
            'event_type': row[1],
            'customer': row[2],
            'amount': row[3],
            'terminal': row[4],
            'time': row[5].strftime('%Y-%m-%d %H:%M:%S')
        } for row in cursor.fetchall()]
        
        return jsonify(events)
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🌐 Starting Kafka Billing Pipeline Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Auto-refresh every 5 seconds")
    app.run(debug=True, host='0.0.0.0', port=5000) 