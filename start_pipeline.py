#!/usr/bin/env python3
"""
Pipeline manager for the Kafka Billing Pipeline.
Handles starting and stopping all components.
"""

import subprocess
import signal
import sys
import time
import os
import psutil
from typing import List, Optional

class PipelineManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        # Use sys.executable to ensure we use the same Python interpreter
        python_executable = sys.executable
        self.components = [
            ('producer', f'{python_executable} -m kafka_billing_pipeline.producer'),
            ('consumer', f'{python_executable} -m kafka_billing_pipeline.billing_processor'),
            ('analytics', f'{python_executable} -m kafka_billing_pipeline.analytics')
        ]
    
    def start_component(self, name: str, command: str) -> Optional[subprocess.Popen]:
        """Start a single component."""
        try:
            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered output
                universal_newlines=True
            )
            self.processes.append(process)
            print(f"✅ {name} started (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def start_pipeline(self):
        """Start all pipeline components."""
        print("🚢 Starting Kafka Billing Pipeline...")
        print("=" * 50)
        
        for name, command in self.components:
            process = self.start_component(name, command)
            if process is None:
                self.stop_pipeline()
                sys.exit(1)
            time.sleep(2)  # Increased delay to allow components to initialize
        
        print("\n" + "=" * 50)
        print("🎉 Pipeline started successfully!")
        print("Press Ctrl+C to stop all components.")
        print("=" * 50)
        
        try:
            # Keep the main process running
            while True:
                time.sleep(1)
                # Check if any process has died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        name = self.components[i][0]
                        print(f"⚠️  {name} process has stopped unexpectedly")
                        
                        # Try to get error output
                        try:
                            stderr_output = process.stderr.read()
                            if stderr_output:
                                print(f"Error output from {name}:")
                                print(stderr_output)
                        except:
                            pass
                        
                        self.stop_pipeline()
                        sys.exit(1)
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal...")
            self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop all pipeline components."""
        print("\n🛑 Stopping Kafka Billing Pipeline...")
        
        for i, process in enumerate(self.processes):
            name = self.components[i][0]
            try:
                print(f"Stopping {name} (PID: {process.pid})...")
                
                # Try graceful shutdown first
                if sys.platform == "win32":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                
                # Wait a bit for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    print(f"⚠️  {name} didn't stop gracefully, forcing...")
                    if sys.platform == "win32":
                        process.kill()
                    else:
                        process.send_signal(signal.SIGKILL)
                    process.wait()
                    print(f"✅ {name} force stopped")
                
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        # Also kill any remaining Python processes that might be running our modules
        self.kill_orphaned_processes()
        
        print("✅ All pipeline components stopped.")
        self.processes.clear()
    
    def kill_orphaned_processes(self):
        """Kill any orphaned Python processes running our modules."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('kafka_billing_pipeline' in arg for arg in cmdline):
                        if proc.pid != os.getpid():  # Don't kill ourselves
                            print(f"Killing orphaned process: {proc.pid}")
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"Warning: Could not clean up orphaned processes: {e}")
    
    def status(self):
        """Show status of all components."""
        print("📊 Pipeline Status:")
        print("=" * 30)
        
        for i, process in enumerate(self.processes):
            name = self.components[i][0]
            if process.poll() is None:
                print(f"✅ {name}: Running (PID: {process.pid})")
            else:
                print(f"❌ {name}: Stopped (Exit code: {process.returncode})")

def main():
    """Main entry point."""
    manager = PipelineManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.start_pipeline()
        elif command == "stop":
            manager.stop_pipeline()
        elif command == "status":
            manager.status()
        else:
            print("Usage: python start_pipeline.py [start|stop|status]")
            print("  start  - Start all pipeline components")
            print("  stop   - Stop all pipeline components")
            print("  status - Show status of components")
    else:
        # Default: start the pipeline
        manager.start_pipeline()

if __name__ == "__main__":
    main() 