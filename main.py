"""
SecurePort Scanner - Entry Point
File: main.py

This is the main entry point to start the SecurePort Scanner application.
It validates the environment (checking that Tkinter is available) and starts
the visual auditing dashboard.

Designed for:
- University student portfolios
- Cybersecurity classroom labs
- Local authorized network auditing

Usage:
    python main.py
"""

import sys

def main():
    try:
        # Step 1: Attempt to import Tkinter
        # Tkinter is the standard Python GUI package. It is built-in on Windows/macOS,
        # but on some headless Linux distributions, it might require 'apt install python3-tk'.
        import tkinter as tk
        from ui import SecurePortScannerUI
    except ImportError as e:
        print("[!] ERROR: Failed to load GUI modules.")
        print(f"Details: {str(e)}")
        print("Please ensure Python 3 is installed with Tkinter support.")
        print("On Debian/Ubuntu: sudo apt-get install python3-tk")
        print("On Fedora/RHEL: sudo dnf install python3-tkinter")
        sys.exit(1)

    # Step 2: Initialize the visual interface and execute loop
    try:
        app = SecurePortScannerUI()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[!] Keyboard interruption detected. Shutting down application gracefully.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected application crash: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
