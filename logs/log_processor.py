#!/usr/bin/env python3
"""
Container Log Processor

This script monitors container stderr log files and stores entries in a structured format
that can be easily imported into Chroma or other vector databases for analysis.

Usage:
    python log_processor.py [--watch] [--import]

Options:
    --watch    Continuously watch log files for changes
    --import   Import existing logs into Chroma database
"""

import os
import sys
import time
import json
import re
import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import signal
import threading
import queue

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("Warning: chromadb not installed. Import functionality disabled.")

# Configuration
LOG_DIR = Path("logs")
PROCESSED_DIR = LOG_DIR / "processed"
MEMORY_DIR = LOG_DIR / "memory"
COLLECTION_NAME = "container_logs"

# Ensure directories exist
PROCESSED_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

def parse_log_line(line, container_name):
    """Parse a log line and extract metadata."""
    # Default structure if parsing fails
    log_entry = {
        "raw": line.strip(),
        "container": container_name,
        "timestamp": datetime.now().isoformat(),
        "level": "UNKNOWN",
        "message": line.strip(),
    }
    
    # Try to parse timestamp and log level
    timestamp_match = re.match(r'^\[?(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\]?\s+(\w+)\s+(.+)$', line)
    if timestamp_match:
        log_entry["timestamp"] = timestamp_match.group(1)
        log_entry["level"] = timestamp_match.group(2)
        log_entry["message"] = timestamp_match.group(3).strip()
    
    return log_entry

def process_log_file(log_path):
    """Process a log file and store structured data for each line."""
    container_name = log_path.stem.replace('-stderr', '')
    memory_file = MEMORY_DIR / f"{container_name}-{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    print(f"Processing log file: {log_path}")
    
    # Track file position
    position_file = PROCESSED_DIR / f"{log_path.name}.pos"
    position = 0
    
    if position_file.exists():
        with open(position_file, 'r') as f:
            try:
                position = int(f.read().strip())
            except ValueError:
                position = 0
    
    # Open log file and move to last position
    with open(log_path, 'r') as f:
        f.seek(position)
        
        # Process new lines
        new_entries = []
        for line in f:
            if line.strip():
                log_entry = parse_log_line(line, container_name)
                new_entries.append(log_entry)
        
        # Save entries to memory file
        if new_entries:
            with open(memory_file, 'a') as mf:
                for entry in new_entries:
                    mf.write(json.dumps(entry) + '\n')
            
            print(f"Added {len(new_entries)} entries from {container_name}")
        
        # Update position
        position = f.tell()
    
    # Save position
    with open(position_file, 'w') as f:
        f.write(str(position))
    
    return len(new_entries)

def watch_log_files():
    """Watch log directory for changes and process new entries."""
    print("Watching for log changes...")
    last_modified = {}
    
    try:
        while True:
            log_files = [f for f in LOG_DIR.glob('*-stderr.log')]
            
            for log_path in log_files:
                mtime = log_path.stat().st_mtime
                
                # If file is new or modified, process it
                if log_path not in last_modified or mtime > last_modified[log_path]:
                    num_processed = process_log_file(log_path)
                    if num_processed > 0:
                        print(f"Processed {num_processed} new log entries from {log_path.name}")
                    last_modified[log_path] = mtime
            
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        print("\nStopping log watcher...")

def import_to_chroma():
    """Import log data from memory files into Chroma database."""
    if not HAS_CHROMA:
        print("Error: chromadb not installed. Cannot import logs.")
        return False
    
    try:
        print("Initializing Chroma client...")
        client = chromadb.PersistentClient(path=str(MEMORY_DIR / "chroma_db"))
        
        # Get or create collection
        collection = client.get_or_create_collection(COLLECTION_NAME)
        print(f"Using collection: {COLLECTION_NAME}")
        
        # Process all memory files
        memory_files = list(MEMORY_DIR.glob('*.jsonl'))
        if not memory_files:
            print("No memory files found to import.")
            return False
        
        for memory_file in memory_files:
            print(f"Importing: {memory_file}")
            entries = []
            
            with open(memory_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse line in {memory_file}")
            
            if not entries:
                print(f"No valid entries found in {memory_file}")
                continue
            
            # Prepare data for Chroma
            documents = [entry["message"] for entry in entries]
            metadatas = [{
                "container": entry["container"],
                "timestamp": entry["timestamp"],
                "level": entry["level"]
            } for entry in entries]
            ids = [hashlib.md5(f"{entry['container']}:{entry['timestamp']}:{entry['message']}".encode()).hexdigest() for entry in entries]
            
            # Add to collection in batches of 100
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end = min(i + batch_size, len(documents))
                collection.add(
                    documents=documents[i:end],
                    metadatas=metadatas[i:end],
                    ids=ids[i:end]
                )
                print(f"Added batch {i//batch_size + 1} ({i}-{end})")
            
            # Rename processed file
            processed_path = PROCESSED_DIR / f"{memory_file.name}.imported"
            memory_file.rename(processed_path)
            print(f"Moved {memory_file} to {processed_path}")
        
        print("Import complete!")
        return True
    
    except Exception as e:
        print(f"Error importing to Chroma: {e}")
        return False

def setup_scheduled_import(interval=300):
    """Set up a scheduled import every interval seconds."""
    def scheduled_task():
        while True:
            time.sleep(interval)
            print(f"\n--- Scheduled import at {datetime.now().isoformat()} ---")
            import_to_chroma()
    
    thread = threading.Thread(target=scheduled_task, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Container Log Processor")
    parser.add_argument("--watch", action="store_true", help="Watch log files continuously")
    parser.add_argument("--import-logs", action="store_true", help="Import logs to Chroma")
    parser.add_argument("--both", action="store_true", help="Watch and import periodically")
    args = parser.parse_args()
    
    # Process existing logs first
    log_files = list(LOG_DIR.glob('*-stderr.log'))
    for log_path in log_files:
        process_log_file(log_path)
    
    if args.both:
        if HAS_CHROMA:
            print("Setting up watching and periodic importing...")
            import_thread = setup_scheduled_import()
            watch_log_files()  # This will run until Ctrl+C
        else:
            print("Chroma not available. Falling back to watch-only mode.")
            watch_log_files()
    elif args.import_logs:
        import_to_chroma()
    elif args.watch:
        watch_log_files()
    else:
        print("No action specified. Use --watch, --import-logs, or --both")
        print(f"Processed {len(log_files)} log files.")
