"""
SecurePort Scanner - File Exporter Utility
File: exporter.py

This module contains the exporting routines for saving scan results in either
CSV (Comma Separated Values) or JSON (JavaScript Object Notation) formats.

Key Educational Concepts Explained:
1. CSV Structuring: Uses Python's standard 'csv' module to write formatted rows.
   Guarantees that strings containing commas, quotes, or newlines are escaped correctly.
2. JSON Structuring: Uses Python's standard 'json' module to serialize Python lists/dicts
   into a standard text representation. Extremely useful for APIs or modern web tools.
"""

import csv
import json
from tkinter import filedialog, messagebox

def export_to_csv(results, parent_window=None):
    """
    Prompts the user to choose a file path and exports scan results to a CSV file.
    
    Parameters:
        results (list of dict): List containing results. Each dict has 'port', 'status', 'service', 'banner'.
        parent_window: The Tkinter root/window to center the dialog on.
    """
    if not results:
        messagebox.showwarning("No Data", "There are no scan results to export.", parent=parent_window)
        return False

    # Open system Save As dialog
    file_path = filedialog.asksaveasfilename(
        parent=parent_window,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Export Scan Results to CSV"
    )
    
    if not file_path:
        return False  # User cancelled the save dialog

    try:
        # Open file with UTF-8 encoding and newline='' to prevent blank lines on Windows
        with open(file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Write column header
            writer.writerow(["Port", "Status", "Service", "Banner"])
            
            # Write matching data rows
            for r in results:
                writer.writerow([
                    r.get("port"),
                    r.get("status"),
                    r.get("service"),
                    r.get("banner", "")
                ])
                
        messagebox.showinfo("Export Successful", f"Scan results successfully saved to:\n{file_path}", parent=parent_window)
        return True
    except Exception as e:
        messagebox.showerror("Export Failed", f"An error occurred while saving the CSV file:\n{str(e)}", parent=parent_window)
        return False

def export_to_json(results, parent_window=None):
    """
    Prompts the user to choose a file path and exports scan results to a JSON file.
    
    Parameters:
        results (list of dict): List containing results. Each dict has 'port', 'status', 'service', 'banner'.
        parent_window: The Tkinter root/window to center the dialog on.
    """
    if not results:
        messagebox.showwarning("No Data", "There are no scan results to export.", parent=parent_window)
        return False

    # Open system Save As dialog
    file_path = filedialog.asksaveasfilename(
        parent=parent_window,
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        title="Export Scan Results to JSON"
    )
    
    if not file_path:
        return False  # User cancelled

    try:
        # Write serialized JSON
        with open(file_path, mode='w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            
        messagebox.showinfo("Export Successful", f"Scan results successfully saved to:\n{file_path}", parent=parent_window)
        return True
    except Exception as e:
        messagebox.showerror("Export Failed", f"An error occurred while saving the JSON file:\n{str(e)}", parent=parent_window)
        return False
