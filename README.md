# ⚡ SecurePort Scanner

SecurePort Scanner is a professional, beginner-friendly, educational cybersecurity auditing tool written in Python. It features a high-fidelity visual dashboard designed with modern dark themes (and a soft light mode), a responsive real-time logs debugger console, search filters, historical logging, and native CSV/JSON exporters.

Developed specifically for **university labs**, **academic portfolios**, and **self-taught network security enthusiasts**, this utility demonstrates core concepts of low-level networking socket programming, multithreading control, thread-safe GUI synchronization, and safe information-gathering practices.

---

## 🧭 Educational Focus & Core Networking Concepts

This tool is structured to serve as a practical learning reference:
1. **Low-Level TCP Sockets (`socket` module)**: Employs standard IPv4 (`socket.AF_INET`) and TCP (`socket.SOCK_STREAM`) abstractions. Uses the non-blocking connection attempt API `socket.connect_ex()`, showing how standard TCP handshakes work without triggering system exceptions.
2. **Multi-Threaded Concurrency (`threading` module)**: Implements worker pooling using `queue.Queue`. Teaches how dividing network tasks across thread workers improves inspection speeds up to 50x without blocking main process executions.
3. **Information Gathering & Protocol Design (`banner.py`)**: Demonstrates the difference between *Server-Speaks-First* protocols (e.g. SSH, FTP, SMTP which greet immediately) and *Client-Speaks-First* protocols (e.g. HTTP, which require a compliant TCP probe to release headers), alongside safe byte decoding routines.
4. **Thread-Safe GUI Updates**: Shows how to maintain UI responsiveness and avoid interface freezing by orchestrating background threads and reading updates via thread-safe FIFO queues on the main event loop.

---

## ✨ Features

- **Host DNS Resolver**: Supports both IP addresses (`127.0.0.1`, `10.0.0.1`) and domains (`scanme.nmap.org`, `localhost`), resolving them using system-level DNS calls.
- **Port Bounds Checks**: Custom validators that catch typing errors, invalid boundaries, or characters before connections launch.
- **Multi-Threaded Scanner**: Configurable thread levels (up to 250 threads) with safe workers to protect system resources.
- **Responsive Table Tree**: Displays Port, Status, Service type, and Banner information. Features ascending/descending sorting for all columns.
- **Live Search & Filter**: Real-time filtering allowing users to view only `Open` ports or match keyword substrings across any field.
- **Academic Logs Panel**: A live scrolling debugging console showing timestamps, connection attempts, socket warnings, and thread events.
- **Persisted Local History**: Autoloads list views of completed scans with their targets and discovered port counts. Double-clicking history items auto-completes the input forms.
- **CSV & JSON Exporters**: Integrates native file saving dialogs to export audits.
- **Theme Customizer Toggle**: Instantly switch between the Cybersecurity Dark Theme and the high-contrast Light Theme.
- **Built-in Reference Guide**: A modal containing clear summaries of network theories.

---

## 🛠️ Technology Stack & Dependencies

To make it as accessible as possible, SecurePort Scanner relies **entirely on Python 3's built-in standard library**:
- **`tkinter`**: Graphical User Interface engine.
- **`socket`**: Low-level network connections and host resolution.
- **`threading`**: Parallel executor orchestration.
- **`queue`**: Thread-safe memory queues.
- **`csv` & `json`**: Serializing and reading log formats.
- **`re` & `os`**: System actions and validation.

**Prerequisites:**
- Python `3.8` or newer.
- No external packages required! (Zero `pip install` setups needed).

---

## 🚀 Installation & How to Run

1. Clone or download this project folder.
2. Open a command prompt or terminal in the project directory.
3. Execute the entry point:
   ```bash
   python main.py
   ```

*(Note: On headless Linux systems, you might need to install Tkinter libraries using your package manager, e.g. `sudo apt-get install python3-tk` or `sudo dnf install python3-tkinter`).*

---

## 📐 Project Structure

```
secureport-scanner/
│
├── main.py                   # Environment verifier and window launcher
├── scanner.py                # Thread pooling and connect_ex TCP engine
├── banner.py                 # Protocol banner grabber (SSH greetings & HTTP probes)
├── exporter.py               # CSV and JSON file export functions
├── ui.py                     # Responsive Tkinter custom styled interface
├── utils.py                  # Validator regexes, history loader, configurations
├── requirements.txt          # Academic package prerequisites listing
├── scan_history.json         # Persisted local history entries (Auto-generated)
├── sample_scan_results.csv   # Reference of CSV format exports
├── sample_scan_results.json  # Reference of JSON format exports
└── assets/                   # App logos and aesthetic visual assets folder
```

---

## 🛡️ Educational & Legal Disclaimer

> [!WARNING]
> **IMPORTANT SAFETY NOTICE**
> SecurePort Scanner is designed solely for educational, academic classroom, and authorized local systems auditing. 
> Sending connection probes generates real network traffic. Inspecting ports on third-party computers, servers, or networks without explicit, written prior permission is illegal and violates standard computer abuse acts.
> **Only inspect localhost (`127.0.0.1`), your own personal sandbox routers, or approved educational endpoints such as `scanme.nmap.org`.**

---

## 🔮 Future Improvements & Portfolio Additions

This repository is designed to be easily extensible. Excellent options for student portfolio expansions include:
1. **CVE Lookup API Integration**: Query online databases (e.g. NIST NVD) with service names and version banners to fetch vulnerabilities.
2. **OS Detection (Banner Analysis)**: Parse welcome banners to guess target Operating System variants (e.g., Ubuntu, Debian, CentOS, Windows Server).
3. **Async Scanning Integration**: Rewrite scanner operations utilizing modern Python `asyncio` streams for lighter memory loads.
4. **SQL History Database**: Swap the lightweight JSON log files with SQLite modules (`sqlite3`) to enable full sorting, deletion, and advanced statistics storage.
5. **Network Visualizer Maps**: Draw live connection graphs using Python standard canvas widgets or export Node configurations to visual diagrams.
