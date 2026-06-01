"""
SecurePort Scanner - Educational Network Utility Helpers
File: utils.py

This module contains inputs validation logic, hostname resolution, and historical
scan log persistence. It is designed to be highly readable for university students
learning Python validation and basic I/O persistence.

Key Educational Concepts Explained:
1. DNS Resolution: Converts user-friendly hostnames (e.g., 'scanme.nmap.org') 
   into machine-routable IP addresses (e.g., '45.33.32.156') using the socket.gethostbyname() API.
2. File IO and JSON Serialization: Uses Python's standard 'json' library to read/write 
   structured history logs safely.
"""

import socket
import re
import os
import json
from datetime import datetime

# Path to save scan history. Placed in local workspace for easy student review.
HISTORY_FILE = "scan_history.json"

def validate_host(host_str):
    """
    Validates a target host string which can be an IPv4 address or a domain name.
    Attempts DNS resolution to confirm the host is reachable/resolvable.
    
    Returns:
        (resolved_ip, error_message): If successful, error_message is None.
                                      If invalid, resolved_ip is None and error_message describes the problem.
    """
    host_str = host_str.strip()
    if not host_str:
        return None, "Target host cannot be empty."

    # Regular expression for simple domain / IP check (alphanumeric, dots, dashes)
    # This prevents injection attacks and command execution in potential sub-processes.
    if not re.match(r"^[a-zA-Z0-9.-]+$", host_str):
        return None, "Invalid characters in target host. Use a domain or an IP address."

    try:
        # socket.gethostbyname() is a standard system API.
        # It queries the local DNS resolver to map the hostname to an IP address.
        # This will resolve "localhost" -> "127.0.0.1", "scanme.nmap.org" -> "45.33.32.156", etc.
        resolved_ip = socket.gethostbyname(host_str)
        return resolved_ip, None
    except socket.gaierror:
        # gaierror = GetAddressInfo Error. Occurs when DNS resolution fails or host is unknown.
        return None, f"Could not resolve host '{host_str}'. Check network connection or typo."
    except Exception as e:
        return None, f"Error resolving host: {str(e)}"

def validate_ports(start_str, end_str):
    """
    Validates port inputs to make sure they are integers, within valid range (1 - 65535),
    and that the start port is less than or equal to the end port.
    
    Returns:
        (start_port, end_port, error_message): Validated integer ports or error message if invalid.
    """
    start_str = start_str.strip()
    end_str = end_str.strip()

    if not start_str or not end_str:
        return None, None, "Start Port and End Port must not be empty."

    if not start_str.isdigit() or not end_str.isdigit():
        return None, None, "Ports must be positive whole numbers only."

    start_port = int(start_str)
    end_port = int(end_str)

    if start_port < 1 or start_port > 65535:
        return None, None, f"Start Port {start_port} is out of bounds (valid range: 1 - 65535)."
        
    if end_port < 1 or end_port > 65535:
        return None, None, f"End Port {end_port} is out of bounds (valid range: 1 - 65535)."

    if start_port > end_port:
        return None, None, f"Start Port ({start_port}) cannot be greater than End Port ({end_port})."

    return start_port, end_port, None

def validate_threads(threads_str):
    """
    Validates thread count. Employs security limits to prevent system overloading.
    
    Returns:
        (thread_count, error_message)
    """
    threads_str = threads_str.strip()
    if not threads_str:
        return 50, None  # Fallback to default safely

    if not threads_str.isdigit():
        return None, "Thread count must be a positive integer."

    val = int(threads_str)
    if val < 1:
        return None, "Thread count must be at least 1."
    
    # Restrict thread count to 250 for standard lab environments
    # Very high threads in Python standard thread library (on Windows especially) 
    # can trigger high memory overhead or OS socket exhaustion limits.
    if val > 250:
        return None, "Thread count capped at 250 for stability and safety."

    return val, None

def load_history():
    """
    Loads historical scan entries from scan_history.json.
    Returns:
        list of scan history records (dict).
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def save_history(host, start_port, end_port, open_ports_count, duration):
    """
    Saves a completed scan summary to the local JSON file.
    
    Parameters:
        host: Target domain/IP scanned
        start_port: Lower port bound
        end_port: Upper port bound
        open_ports_count: Number of ports discovered to be open
        duration: Elapsed time in seconds
    """
    history = load_history()
    
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": host,
        "ports": f"{start_port}-{end_port}",
        "open_count": open_ports_count,
        "duration": f"{duration:.2f}s"
    }
    
    # Prepend to keep newest scans first, keep max 50 scans to save space
    history.insert(0, record)
    history = history[:50]
    
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception:
        pass
