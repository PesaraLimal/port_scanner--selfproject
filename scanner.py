"""
SecurePort Scanner - Multi-Threaded TCP Scanning Engine
File: scanner.py

This module implements the port scanning mechanics. It demonstrates the use of
Python threads, synchronized queues, and raw TCP socket calls to build a high-performance,
educational network scanner.

Key Educational Concepts Explained:
1. TCP Handshake and socket.connect_ex(): 
   A TCP connection starts with a three-way handshake (SYN, SYN-ACK, ACK).
   Instead of using s.connect(), which throws an exception if the port is closed, 
   we use s.connect_ex(). It returns 0 if the connection succeeded (port is open)
   and a system error code (like 10061 on Windows for Connection Refused) if closed.
2. Multi-Threading with queue.Queue:
   A single-threaded scanner checking 1000 ports with a 0.5-second timeout could take 
   up to 500 seconds. By dividing the workload among N threads, we check N ports 
   simultaneously. A thread-safe Queue guarantees that no two threads scan the same port.
3. Thread-Safe GUI Communication:
   Tkinter GUI widgets are not thread-safe. They must only be modified from the main 
   application thread. This engine solves that by writing all scanner updates to a 
   thread-safe queue.Queue. The Tkinter GUI repeatedly polls this queue and updates itself.
"""

import socket
import threading
import queue
import time
from banner import grab_banner
import utils

# Fallback service mapping dictionary for modern services that might not be registered
# in the local operating system's services database.
COMMON_SERVICES = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    115: "SFTP",
    123: "NTP",
    143: "IMAP",
    161: "SNMP",
    443: "HTTPS",
    445: "Microsoft-DS",
    1433: "MSSQL",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    6379: "Redis",
    8080: "HTTP-ALT",
    8443: "HTTPS-ALT"
}

class PortScannerEngine:
    def __init__(self, target_ip, start_port, end_port, thread_count=50, timeout=0.5, ui_queue=None):
        """
        Initializes the scanning engine.
        
        Parameters:
            target_ip (str): Resolved destination IP.
            start_port (int): Minimum port to scan.
            end_port (int): Maximum port to scan.
            thread_count (int): Number of concurrent scanning threads.
            timeout (float): Connection timeout for each port.
            ui_queue (queue.Queue): Thread-safe queue used to send status back to UI.
        """
        self.target_ip = target_ip
        self.start_port = start_port
        self.end_port = end_port
        self.thread_count = thread_count
        self.timeout = timeout
        self.ui_queue = ui_queue if ui_queue else queue.Queue()
        
        # State variables
        self.stop_requested = False
        self.ports_scanned_count = 0
        self.open_ports_count = 0
        
        # Lock for thread-safe increments
        self.counter_lock = threading.Lock()
        
        # Port work queue (each thread pulls ports from here)
        self.port_queue = queue.Queue()
        
        # List of worker threads
        self.workers = []
        
        # Main manager thread
        self.manager_thread = None

    def start(self):
        """
        Launches the scan. To prevent freezing the GUI, this starts a background
        manager thread, which in turn orchestrates the worker threads.
        """
        self.stop_requested = False
        self.ports_scanned_count = 0
        self.open_ports_count = 0
        
        # Fill port queue
        for port in range(self.start_port, self.end_port + 1):
            self.port_queue.put(port)
            
        # Start manager thread
        self.manager_thread = threading.Thread(target=self._run_manager)
        self.manager_thread.daemon = True
        self.manager_thread.start()

    def stop(self):
        """
        Signals all active worker threads to terminate their loops.
        Clears the port queue to ensure threads exit immediately.
        """
        self.stop_requested = True
        
        # Drain the port queue so workers find it empty immediately
        while not self.port_queue.empty():
            try:
                self.port_queue.get_nowait()
                self.port_queue.task_done()
            except queue.Empty:
                break
                
        self._send_to_ui({"type": "log", "text": "[SYSTEM] Cancellation requested. Shutting down worker threads..."})

    def _send_to_ui(self, msg):
        """Helper to safely enqueue events for the GUI thread."""
        self.ui_queue.put(msg)

    def _get_service_name(self, port):
        """
        Tries to resolve the service name for a given port.
        Uses system services db first, falls back to common definitions dictionary.
        """
        # Method 1: Check standard OS definitions list
        try:
            return socket.getservbyport(port, "tcp").upper()
        except OSError:
            pass

        # Method 2: Fall back to our local dictionary
        return COMMON_SERVICES.get(port, "Unknown")

    def _run_manager(self):
        """
        Runs on a background manager thread. Spawns threads, waits for completion,
        calculates metrics, and handles logging.
        """
        total_ports = (self.end_port - self.start_port) + 1
        self._send_to_ui({"type": "log", "text": f"[SYSTEM] Starting scan against target {self.target_ip}"})
        self._send_to_ui({"type": "log", "text": f"[SYSTEM] Range: {self.start_port} - {self.end_port} | Threads: {self.thread_count}"})
        self._send_to_ui({"type": "status", "text": "Scanning target..."})
        
        start_time = time.time()
        
        # Spawn worker threads
        actual_thread_count = min(self.thread_count, total_ports)
        for i in range(actual_thread_count):
            t = threading.Thread(target=self._worker_scan, args=(i+1,))
            t.daemon = True
            t.start()
            self.workers.append(t)
            
        # Wait for all worker threads to exit
        for t in self.workers:
            t.join()
            
        elapsed_time = time.time() - start_time
        
        # Scan completed or was cancelled
        if self.stop_requested:
            self._send_to_ui({"type": "log", "text": f"[SYSTEM] Scan stopped by user after {elapsed_time:.2f} seconds."})
            self._send_to_ui({"type": "status", "text": "Scan stopped."})
        else:
            self._send_to_ui({"type": "log", "text": f"[SYSTEM] Scan completed successfully in {elapsed_time:.2f} seconds."})
            self._send_to_ui({"type": "log", "text": f"[SYSTEM] Discovered {self.open_ports_count} open ports."})
            self._send_to_ui({"type": "status", "text": "Scan completed."})
            
            # Save to history file
            utils.save_history(self.target_ip, self.start_port, self.end_port, self.open_ports_count, elapsed_time)
            
        self._send_to_ui({
            "type": "finished",
            "open_count": self.open_ports_count,
            "duration": elapsed_time,
            "cancelled": self.stop_requested
        })

    def _worker_scan(self, thread_id):
        """
        Core worker logic executed in parallel threads.
        Pulls a port from the queue, executes socket checks, retrieves banners, 
        and updates the progress counters thread-safely.
        """
        total_ports = (self.end_port - self.start_port) + 1
        
        while not self.stop_requested:
            try:
                # Retrieve the next port to scan
                port = self.port_queue.get_nowait()
            except queue.Empty:
                break  # No more work remaining!
                
            # Log active scan to log panel
            self._send_to_ui({
                "type": "active_port",
                "port": port,
                "thread": thread_id
            })
            
            # TCP Socket scanning attempt
            is_open = False
            service = "Unknown"
            banner = ""
            
            try:
                # socket.socket parameters:
                # - AF_INET specifies IPv4 addressing
                # - SOCK_STREAM specifies TCP virtual circuit connection
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.timeout)
                    
                    # connect_ex() returns 0 on successful TCP handshake (SYN, SYN-ACK, ACK)
                    result = s.connect_ex((self.target_ip, port))
                    
                    if result == 0:
                        is_open = True
                        service = self._get_service_name(port)
            except Exception as e:
                # Handle unexpected system errors (e.g. temporary network interface resets)
                self._send_to_ui({
                    "type": "log", 
                    "text": f"[WARNING] Thread-{thread_id} got error scanning Port {port}: {str(e)}"
                })
                
            # If port is open, attempt banner grabbing
            if is_open:
                # Safely grab server details
                grabbed = grab_banner(self.target_ip, port, timeout=self.timeout)
                if grabbed:
                    banner = grabbed
                else:
                    banner = "No banner response (Active connection)"
                    
                # Increment open ports count
                with self.counter_lock:
                    self.open_ports_count += 1
                    
                # Dispatch open port result to UI
                self._send_to_ui({
                    "type": "result",
                    "port": port,
                    "status": "Open",
                    "service": service,
                    "banner": banner
                })
                self._send_to_ui({
                    "type": "log",
                    "text": f"[DISCOVERY] Found Port {port} OPEN ({service}) | Banner: {banner}"
                })
            else:
                # Dispatch closed port result to UI (useful for real-time progress and stats)
                self._send_to_ui({
                    "type": "result",
                    "port": port,
                    "status": "Closed",
                    "service": "Closed",
                    "banner": ""
                })

            # Increment scanned count and update progress metrics
            with self.counter_lock:
                self.ports_scanned_count += 1
                current_scanned = self.ports_scanned_count
                
            percent_complete = (current_scanned / total_ports) * 100
            
            # Periodically report numerical progress to GUI
            self._send_to_ui({
                "type": "progress",
                "scanned": current_scanned,
                "percent": percent_complete,
                "open_count": self.open_ports_count
            })
            
            # Complete the task queue entry
            self.port_queue.task_done()
            
            # Short sleep to prevent CPU starvation on extremely fast localhost scans
            time.sleep(0.001)
