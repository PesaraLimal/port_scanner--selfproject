from flask import Flask, jsonify, request
from flask_cors import CORS
import socket
import concurrent.futures
import time
import os

# Get the absolute path to the parent directory of this file (root workspace)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(__name__, static_folder=parent_dir, static_url_path='')
# Enable CORS for all routes so the frontend can easily communicate with it
CORS(app)

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

def get_service_name(port):
    try:
        return socket.getservbyport(port, "tcp").upper()
    except OSError:
        pass
    return COMMON_SERVICES.get(port, "Unknown")

def grab_banner(ip, port, timeout=0.8):
    http_ports = {80, 443, 8080, 8081, 8888, 3000, 5000}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
            
            # Client-Speaks-First (HTTP/HTTPS)
            if port in http_ports:
                probe = (
                    f"GET / HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: pesz_ara_PortScannerLive/1.0 (Web)\r\n"
                    f"Connection: close\r\n\r\n"
                )
                s.sendall(probe.encode('utf-8'))
                response = s.recv(1024)
                if response:
                    decoded = response.decode('utf-8', errors='replace').strip()
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
                    return decoded[:100]
            # Server-Speaks-First
            else:
                banner = s.recv(1024)
                if banner:
                    return banner.decode('utf-8', errors='replace').strip()
            
            # General fallback probe
            s.sendall(b"\r\n")
            banner = s.recv(1024)
            if banner:
                return banner.decode('utf-8', errors='replace').strip()
    except Exception:
        return None
    return None

def scan_port(ip, port, timeout=0.5):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            if result == 0:
                service = get_service_name(port)
                # Attempt to grab service banner
                banner = grab_banner(ip, port, timeout=timeout)
                return {
                    "port": port,
                    "status": "Open",
                    "service": service,
                    "banner": banner or "No banner response (Active connection)"
                }
    except Exception:
        pass
    
    return {
        "port": port,
        "status": "Closed",
        "service": "Closed",
        "banner": ""
    }

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "service": "pesz_ara_ ports scanner API",
        "version": "1.0.0"
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.get_json() or {}
    target = data.get('target', '')
    ports = data.get('ports', [])
    timeout = float(data.get('timeout', 0.5))
    
    if not target:
        return jsonify({"error": "Target host is required."}), 400
    if not ports:
        return jsonify({"error": "No ports provided to scan."}), 400
    if len(ports) > 100:
        return jsonify({"error": "Maximum of 100 ports per batch allowed."}), 400
        
    try:
        target_ip = socket.gethostbyname(target)
    except Exception as e:
        return jsonify({"error": f"Failed to resolve target host '{target}': {str(e)}"}), 400

    results = []
    # Scan batch ports concurrently using a ThreadPoolExecutor
    max_workers = min(len(ports), 30)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, target_ip, port, timeout): port for port in ports}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            
    # Sort results by port number
    results = sorted(results, key=lambda x: x['port'])
    
    return jsonify({
        "target": target,
        "target_ip": target_ip,
        "results": results
    })

# If running locally, start development server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
