"""
SecurePort Scanner - Safe Banner Grabbing Utility
File: banner.py

This module contains the logic for banner grabbing. Banner grabbing is an
information gathering technique used to identify the software, version, and OS
running on a remote system by examining greeting messages or service responses.

Key Educational Concepts Explained:
1. Server-Speaks-First Protocols: Services like FTP (21), SSH (22), SMTP (25), 
   POP3 (110), and IMAP (143) send a welcoming banner text as soon as a TCP
   handshake completes. The client simply needs to connect and wait (receive).
2. Client-Speaks-First Protocols: Services like HTTP (80/8080) wait for the 
   client to send a request (e.g., 'GET / HTTP/1.1...') before sending any 
   response. We must send a small safe probe to receive their banner.
3. Socket Timeouts: We must enforce strict timeouts (e.g., 0.5 - 1.0s) so our
   scanner does not hang indefinitely waiting for slow or silent sockets.
"""

import socket

def grab_banner(ip, port, timeout=0.8):
    """
    Attempts to safely grab a service banner from the target host on the specified port.
    It handles server-speaks-first protocols, HTTP client-speaks-first probes,
    and returns a clean, sanitized text string.
    
    Parameters:
        ip (str): Resolved IP address of the target.
        port (int): Port number to query.
        timeout (float): The maximum time in seconds to wait for socket communication.
        
    Returns:
        str: The retrieved banner or None if no banner could be grabbed.
    """
    # Define common HTTP-like ports
    http_ports = {80, 443, 8080, 8081, 8888, 3000, 5000}
    
    # Establish a fresh TCP socket connection for banner grabbing
    # Using AF_INET for IPv4 and SOCK_STREAM for TCP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            
            # Connect to the target
            s.connect((ip, port))
            
            # --- Scenario A: Client-Speaks-First (HTTP/HTTPS) ---
            if port in http_ports:
                # Send a minimal, compliant HTTP GET request probe
                probe = (
                    f"GET / HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: SecurePortScanner/1.0 (Educational)\r\n"
                    f"Connection: close\r\n\r\n"
                )
                s.sendall(probe.encode('utf-8'))
                
                # Receive response headers (limit to 1024 bytes for safety)
                response = s.recv(1024)
                if response:
                    # Decode with utf-8, replacing unrecognized characters with a placeholder
                    decoded = response.decode('utf-8', errors='replace').strip()
                    
                    # Extract the Server header or the first line of the HTTP response
                    lines = decoded.split('\r\n')
                    first_line = lines[0] if lines else ""
                    server_header = ""
                    for line in lines:
                        if line.lower().startswith("server:"):
                            server_header = line
                            break
                    
                    if server_header:
                        return f"{first_line} | {server_header}"
                    elif first_line:
                        return first_line
                    return decoded[:100]  # Return fallback snippet

            # --- Scenario B: Server-Speaks-First (SSH, FTP, SMTP, POP3, IMAP) ---
            else:
                # The server is expected to push a greeting banner immediately upon connection.
                # We read up to 1024 bytes.
                banner = s.recv(1024)
                if banner:
                    return banner.decode('utf-8', errors='replace').strip()

            # --- Scenario C: General fallback probe for unknown services ---
            # Send a carriage return to trigger a default server error/greeting response
            s.sendall(b"\r\n")
            banner = s.recv(1024)
            if banner:
                return banner.decode('utf-8', errors='replace').strip()

    except socket.timeout:
        # Expected behavior for secure ports that don't speak first or drop silent packets
        return None
    except Exception:
        # Handle closed, firewall-blocked, or reset socket exceptions gracefully
        return None
        
    return None
