#!/usr/bin/env python3
"""
Setup Log Monitoring System

This script installs dependencies and sets up the log monitoring system
for processing container stderr logs and storing them in Chroma.
"""

import os
import sys
import subprocess
import platform
import time

def run_command(command, check=True):
    """Run a shell command and return its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, 
                           capture_output=True, check=check)
    return result.stdout

def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    # Create necessary directories
    os.makedirs("logs/processed", exist_ok=True)
    os.makedirs("logs/memory", exist_ok=True)
    
    # Check and install dependencies
    if not check_python_package("chromadb"):
        print("Installing chromadb...")
        run_command("pip install chromadb")
    
    # Make log processor executable
    if platform.system() != "Windows":
        run_command("chmod +x logs/log_processor.py")
    
    # Start log processor in background
    if platform.system() == "Windows":
        command = "start /B python logs/log_processor.py --both"
        run_command(command, check=False)
    else:
        command = "nohup python logs/log_processor.py --both > logs/log_processor.log 2>&1 &"
        run_command(command, check=False)
    
    print("\nLog monitoring system started!")
    print("- stderr logs from containers are being captured in logs/[container]-stderr.log")
    print("- Logs are automatically processed and stored in logs/memory/*.jsonl")
    print("- Every 5 minutes, logs are imported into Chroma vector database")
    print("\nTo query logs, use the Chroma client:")
    print("""
    import chromadb
    client = chromadb.PersistentClient(path="logs/memory/chroma_db")
    collection = client.get_collection("container_logs")
    
    # Search for errors
    results = collection.query(
        query_texts=["error"],
        n_results=5,
        where={"level": "ERROR"}
    )
    
    # Get logs from specific container
    results = collection.query(
        query_texts=["important message"],
        where={"container": "chroma-mcp"}
    )
    """)

if __name__ == "__main__":
    main()
