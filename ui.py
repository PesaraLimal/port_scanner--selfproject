"""
SecurePort Scanner - High-Fidelity Tkinter GUI
File: ui.py

This module implements a professional, highly responsive Tkinter GUI dashboard.
It adheres to strict design guidelines, featuring a dark cybersecurity theme,
an optional clean light theme toggle, real-time logging, live search/filtering,
historical records viewing, and clear visual tooltips of networking concepts.

Designed for maximum robustness, portability, and beginner readability.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import queue
import time
from datetime import datetime
import scanner
import utils
import exporter

# ==============================================================================
# Color Palettes
# ==============================================================================
DARK_THEME = {
    "bg_main": "#0B0F19",       # Deep Charcoal Blue
    "bg_panel": "#161B26",      # Steel Gray Blue
    "bg_input": "#222A3B",      # Deep Muted Blue for textboxes
    "accent_cyan": "#00F5FF",   # Bright Cyan
    "accent_green": "#00FF87",  # Bright Neon Green (Success/Open)
    "accent_red": "#FF4B4B",    # Coral Red (Danger/Stop)
    "text_primary": "#E5E9F0", # Off-white
    "text_muted": "#8892B0",    # Cool Gray
    "border": "#2E3A52",        # Frame borders
    "terminal_bg": "#070A10",   # Extremely dark color for logs
    "tree_selected": "#1F2D40"  # Tree selected item highlight
}

LIGHT_THEME = {
    "bg_main": "#F0F2F5",       # Soft Light Gray
    "bg_panel": "#FFFFFF",      # Pure White
    "bg_input": "#E4E6EB",      # Very Light Gray for inputs
    "accent_cyan": "#007A99",   # Rich Cyan
    "accent_green": "#107C41",  # Dark Forest Green (Open)
    "accent_red": "#C42B1C",    # Rich Dark Red (Stop)
    "text_primary": "#1A202C",  # Charcoal/Off-black
    "text_muted": "#5A6578",    # Slate Muted Gray
    "border": "#D2D6DC",        # Light borders
    "terminal_bg": "#1E222B",   # Keep log terminal dark even in light mode (looks cooler)
    "tree_selected": "#E2E8F0"
}

# ==============================================================================
# Main GUI Window Class
# ==============================================================================
class SecurePortScannerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Configure main window traits
        self.title("SecurePort Scanner - Educational Cybersecurity Suite")
        self.geometry("1150x750")
        self.min_width = 1100
        self.min_height = 700
        self.minsize(self.min_width, self.min_height)
        
        # Theme Mode State
        self.current_theme = DARK_THEME
        
        # Scanner Core Engine variables
        self.scanner_engine = None
        self.ui_queue = queue.Queue()
        self.scan_start_time = None
        self.is_scanning = False
        
        # Scan Results Cache for live searches and exports
        # Every entry will be a dict: {port, status, service, banner}
        self.raw_scan_results = []
        
        # Define Tkinter Variables
        self.var_target = tk.StringVar(value="127.0.0.1")
        self.var_start_port = tk.StringVar(value="1")
        self.var_end_port = tk.StringVar(value="1024")
        self.var_threads = tk.StringVar(value="50")
        self.var_timeout = tk.StringVar(value="0.5")
        
        # Filter States
        self.filter_text = tk.StringVar()
        self.filter_text.trace_add("write", lambda *args: self.apply_filters())
        self.filter_show_open_only = tk.BooleanVar(value=False)
        
        # Initialize UI Grid & styling elements
        self.setup_styles()
        self.build_ui()
        
        # Load initial historical logs into listbox
        self.reload_history_list()
        
        # Start a periodic theme enforcement and window sizing
        self.apply_current_colors()

    # ==========================================================================
    # Theme Setup & Styling Configuration
    # ==========================================================================
    def setup_styles(self):
        """Initializes ttk styling properties for scrollbars and progress bars."""
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Clam theme is cross-platform and highly customizable
        
        # Configure standard Treeview font and general layout
        self.style.configure("Treeview",
                             font=("Consolas", 10),
                             rowheight=26,
                             fieldbackground=self.current_theme["bg_panel"])
        self.style.configure("Treeview.Heading",
                             font=("Segoe UI", 10, "bold"))

    def toggle_theme(self):
        """Toggles interface colors between cybersecurity dark and accessibility light modes."""
        if self.current_theme == DARK_THEME:
            self.current_theme = LIGHT_THEME
            self.btn_theme.config(text="🌙 Dark Mode")
        else:
            self.current_theme = DARK_THEME
            self.btn_theme.config(text="☀️ Light Mode")
            
        self.apply_current_colors()
        self.log_to_terminal(f"[THEME] Interface theme toggled to {'Light' if self.current_theme == LIGHT_THEME else 'Dark'} Mode.")

    def apply_current_colors(self):
        """Recursively parses all UI widgets and assigns styling properties from current theme."""
        c = self.current_theme
        
        # Backgrounds of main root and structural components
        self.configure(bg=c["bg_main"])
        
        # Update Styles for treeview
        self.style.configure("Treeview",
                             background=c["bg_panel"],
                             foreground=c["text_primary"],
                             fieldbackground=c["bg_panel"])
        
        self.style.configure("Treeview.Heading",
                             background=c["bg_main"],
                             foreground=c["text_primary"])
        
        self.style.map("Treeview",
                       background=[('selected', c["tree_selected"])],
                       foreground=[('selected', c["accent_cyan"])])
        
        # Update styling tags inside treeview
        self.tree_results.tag_configure("open", foreground=c["accent_green"])
        self.tree_results.tag_configure("closed", foreground=c["text_muted"])
        
        # Recurse update Tkinter standard components
        self._colorize_widgets(self)

    def _colorize_widgets(self, parent):
        """Recursively apply colors to traditional Tkinter widgets."""
        c = self.current_theme
        for child in parent.winfo_children():
            widget_type = child.winfo_class()
            
            # Identify individual Tk classes and assign colors
            if widget_type in ("Frame", "LabelFrame"):
                # Structural frames take panel background
                if hasattr(child, "custom_bg"):
                    child.configure(bg=child.custom_bg)
                else:
                    child.configure(bg=c["bg_panel"])
                    
                if widget_type == "LabelFrame":
                    child.configure(fg=c["text_primary"], font=("Segoe UI", 10, "bold"))
                
                self._colorize_widgets(child)  # Recurse sub-children
                
            elif widget_type == "Label":
                # Check for special label roles (e.g. Header Title)
                if hasattr(child, "special_role"):
                    role = child.special_role
                    if role == "title":
                        child.configure(bg=c["bg_panel"], fg=c["accent_cyan"])
                    elif role == "subtitle":
                        child.configure(bg=c["bg_panel"], fg=c["text_muted"])
                    elif role == "footer":
                        child.configure(bg=c["bg_main"], fg=c["text_muted"])
                else:
                    child.configure(bg=c["bg_panel"], fg=c["text_primary"])
                    
            elif widget_type == "Button":
                if hasattr(child, "btn_type"):
                    btype = child.btn_type
                    if btype == "start":
                        child.configure(bg=c["accent_green"], fg=c["bg_main"], activebackground=c["accent_cyan"])
                    elif btype == "stop":
                        child.configure(bg=c["accent_red"], fg="#FFFFFF", activebackground="#FF7F7F")
                    elif btype == "action":
                        child.configure(bg=c["bg_input"], fg=c["text_primary"], activebackground=c["border"])
                    elif btype == "clear":
                        child.configure(bg=c["bg_input"], fg=c["text_muted"], activebackground=c["border"])
                else:
                    child.configure(bg=c["bg_input"], fg=c["text_primary"], activebackground=c["border"])
                child.configure(bd=0, highlightthickness=0, font=("Segoe UI", 9, "bold"), relief="flat")
                
            elif widget_type == "Entry":
                child.configure(bg=c["bg_input"], fg=c["text_primary"], insertbackground=c["text_primary"],
                                bd=1, relief="flat", highlightbackground=c["border"], highlightcolor=c["accent_cyan"])
                
            elif widget_type == "Text":
                # Log Box Terminal
                if hasattr(child, "log_terminal"):
                    child.configure(bg=c["terminal_bg"], fg=c["accent_green"], insertbackground=c["accent_green"],
                                    bd=1, relief="flat", highlightbackground=c["border"])
                else:
                    child.configure(bg=c["bg_input"], fg=c["text_primary"])
                    
            elif widget_type == "Listbox":
                child.configure(bg=c["bg_input"], fg=c["text_primary"], selectbackground=c["tree_selected"],
                                selectforeground=c["accent_cyan"], bd=0, highlightthickness=0)
                
            elif widget_type == "Checkbutton":
                child.configure(bg=c["bg_panel"], fg=c["text_primary"], activebackground=c["bg_panel"],
                                activeforeground=c["accent_cyan"], selectcolor=c["bg_input"])

    # ==========================================================================
    # Graphical Interface Layout Construction
    # ==========================================================================
    def build_ui(self):
        """Constructs the high-fidelity UI panel elements and grids."""
        c = self.current_theme
        
        # Configure global grid rows/columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # TOP HEADER BAR
        self.rowconfigure(1, weight=1)  # MAIN BODY CONTAINER
        self.rowconfigure(2, weight=0)  # PROGRESS SECTION
        self.rowconfigure(3, weight=0)  # LEGAL FOOTER
        
        # ----------------------------------------------------------------------
        # 1. TOP HEADER SECTION
        # ----------------------------------------------------------------------
        frame_header = tk.Frame(self, bg=c["bg_panel"], height=80, relief="solid", bd=0)
        frame_header.grid(row=0, column=0, sticky="ew")
        frame_header.columnconfigure(0, weight=1)
        frame_header.columnconfigure(1, weight=0)
        
        # Internal title texts
        inner_title = tk.Frame(frame_header, bg=c["bg_panel"])
        inner_title.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        lbl_title = tk.Label(inner_title, text="⚡ SECUREPORT SCANNER", font=("Segoe UI", 18, "bold"))
        lbl_title.special_role = "title"
        lbl_title.pack(anchor="w")
        
        lbl_sub = tk.Label(inner_title, text="Multi-Threaded TCP Network Exploration & Academic Audit Console", font=("Segoe UI", 9, "italic"))
        lbl_sub.special_role = "subtitle"
        lbl_sub.pack(anchor="w")
        
        # Theme and Mode Controllers
        frame_header_buttons = tk.Frame(frame_header, bg=c["bg_panel"])
        frame_header_buttons.grid(row=0, column=1, sticky="e", padx=20)
        
        self.btn_theme = tk.Button(frame_header_buttons, text="☀️ Light Mode", command=self.toggle_theme, width=12, height=1)
        self.btn_theme.btn_type = "action"
        self.btn_theme.grid(row=0, column=0, padx=5, ipady=4)
        
        btn_guide = tk.Button(frame_header_buttons, text="📚 Quick Guide", command=self.show_quick_guide, width=12, height=1)
        btn_guide.btn_type = "action"
        btn_guide.grid(row=0, column=1, padx=5, ipady=4)

        # ----------------------------------------------------------------------
        # 2. MAIN BODY SECTION (Divided left / right)
        # ----------------------------------------------------------------------
        # Workspace grid container
        frame_body = tk.Frame(self, bg=c["bg_main"])
        frame_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame_body.columnconfigure(0, weight=0)  # Left Sidebar: Inputs & History
        frame_body.columnconfigure(1, weight=1)  # Right Main Area: Results Grid & Logs
        frame_body.rowconfigure(0, weight=1)
        
        # Left Panel (Inputs & History)
        panel_left = tk.Frame(frame_body, width=320, bg=c["bg_panel"])
        panel_left.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        panel_left.columnconfigure(0, weight=1)
        panel_left.rowconfigure(0, weight=0) # Inputs Frame
        panel_left.rowconfigure(1, weight=1) # History Frame
        
        # Target Inputs Frame
        frame_inputs = tk.LabelFrame(panel_left, text=" SCAN SCANNER PARAMETERS ", padx=15, pady=15, relief="solid", bd=1)
        frame_inputs.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        frame_inputs.columnconfigure(0, weight=1)
        frame_inputs.columnconfigure(1, weight=1)
        
        # Hostname field
        tk.Label(frame_inputs, text="Target Host (IP or Domain):", anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        self.entry_target = tk.Entry(frame_inputs, textvariable=self.var_target, font=("Consolas", 11), justify="center")
        self.entry_target.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=3)
        
        # Start Port & End Port
        tk.Label(frame_inputs, text="Start Port:", anchor="w").grid(row=2, column=0, sticky="ew", pady=(0, 2))
        tk.Label(frame_inputs, text="End Port:", anchor="w").grid(row=2, column=1, sticky="ew", pady=(0, 2), padx=(10, 0))
        
        self.entry_start_port = tk.Entry(frame_inputs, textvariable=self.var_start_port, font=("Consolas", 11), justify="center", width=10)
        self.entry_start_port.grid(row=3, column=0, sticky="ew", pady=(0, 10), ipady=3)
        
        self.entry_end_port = tk.Entry(frame_inputs, textvariable=self.var_end_port, font=("Consolas", 11), justify="center", width=10)
        self.entry_end_port.grid(row=3, column=1, sticky="ew", pady=(0, 10), padx=(10, 0), ipady=3)
        
        # Thread count & Connection Timeout
        tk.Label(frame_inputs, text="Thread Count (Max 250):", anchor="w").grid(row=4, column=0, sticky="ew", pady=(0, 2))
        tk.Label(frame_inputs, text="Timeout (Seconds):", anchor="w").grid(row=4, column=1, sticky="ew", pady=(0, 2), padx=(10, 0))
        
        self.entry_threads = tk.Entry(frame_inputs, textvariable=self.var_threads, font=("Consolas", 11), justify="center", width=10)
        self.entry_threads.grid(row=5, column=0, sticky="ew", pady=(0, 15), ipady=3)
        
        self.entry_timeout = tk.Entry(frame_inputs, textvariable=self.var_timeout, font=("Consolas", 11), justify="center", width=10)
        self.entry_timeout.grid(row=5, column=1, sticky="ew", pady=(0, 15), padx=(10, 0), ipady=3)
        
        # Operational Buttons: Start & Stop Scan
        self.btn_start = tk.Button(frame_inputs, text="🚀 START SCAN", command=self.action_start_scan, height=2)
        self.btn_start.btn_type = "start"
        self.btn_start.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        
        self.btn_stop = tk.Button(frame_inputs, text="🛑 STOP SCAN", command=self.action_stop_scan, height=2, state="disabled")
        self.btn_stop.btn_type = "stop"
        self.btn_stop.grid(row=7, column=0, columnspan=2, sticky="ew")
        
        # History Frame
        frame_history = tk.LabelFrame(panel_left, text=" SCAN HISTORY LOGS ", padx=10, pady=10, relief="solid", bd=1)
        frame_history.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        frame_history.columnconfigure(0, weight=1)
        frame_history.rowconfigure(0, weight=1)
        frame_history.rowconfigure(1, weight=0)
        
        # List of historical entries
        self.listbox_history = tk.Listbox(frame_history, font=("Consolas", 9))
        self.listbox_history.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.listbox_history.bind("<<ListboxSelect>>", self.action_select_history)
        
        btn_clear_history = tk.Button(frame_history, text="🗑️ Clear Scan History", command=self.action_clear_history, height=1)
        btn_clear_history.btn_type = "clear"
        btn_clear_history.grid(row=1, column=0, sticky="ew", ipady=3)
        
        # Right Area (Tabs / Split between Scan Grid Results and Real-time Logs)
        panel_right = tk.Frame(frame_body, bg=c["bg_main"])
        panel_right.grid(row=0, column=1, sticky="nsew")
        panel_right.columnconfigure(0, weight=1)
        panel_right.rowconfigure(0, weight=3)  # Grid Section (larger weight)
        panel_right.rowconfigure(1, weight=2)  # Log Terminal Section
        
        # A. Results Grid Section
        frame_results = tk.Frame(panel_right, bg=c["bg_panel"], relief="solid", bd=1)
        frame_results.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        frame_results.rowconfigure(0, weight=0)  # Filter control header
        frame_results.rowconfigure(1, weight=1)  # Grid Treeview
        frame_results.rowconfigure(2, weight=0)  # Action panel
        frame_results.columnconfigure(0, weight=1)
        
        # Filter controls
        frame_filters = tk.Frame(frame_results, bg=c["bg_panel"], height=40)
        frame_filters.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame_filters.columnconfigure(0, weight=0)  # Label
        frame_filters.columnconfigure(1, weight=1)  # Search input
        frame_filters.columnconfigure(2, weight=0)  # Checkbox
        
        tk.Label(frame_filters, text="🔍 Search/Filter Results:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.entry_search = tk.Entry(frame_filters, textvariable=self.filter_text, font=("Consolas", 10))
        self.entry_search.grid(row=0, column=1, sticky="ew", ipady=3)
        
        self.chk_open_only = tk.Checkbutton(
            frame_filters,
            text="Show OPEN Ports Only",
            variable=self.filter_show_open_only,
            command=self.apply_filters
        )
        self.chk_open_only.grid(row=0, column=2, padx=(10, 0))
        
        # Table of Results (ttk.Treeview)
        frame_tree = tk.Frame(frame_results, bg=c["bg_panel"])
        frame_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        frame_tree.columnconfigure(0, weight=1)
        frame_tree.rowconfigure(0, weight=1)
        
        self.tree_results = ttk.Treeview(
            frame_tree, 
            columns=("port", "status", "service", "banner"), 
            show="headings",
            selectmode="browse"
        )
        self.tree_results.grid(row=0, column=0, sticky="nsew")
        
        # Setup scrollbars
        scroll_y = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_results.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree_results.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.tree_results.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Configure headings with sorting events
        self.tree_results.heading("port", text="Port ↕", command=lambda: self.sort_column("port", False))
        self.tree_results.heading("status", text="Status ↕", command=lambda: self.sort_column("status", False))
        self.tree_results.heading("service", text="Resolved Service ↕", command=lambda: self.sort_column("service", False))
        self.tree_results.heading("banner", text="Grabbed Welcome Banner / Connection Response Headers ↕", command=lambda: self.sort_column("banner", False))
        
        # Set column widths
        self.tree_results.column("port", width=80, anchor="center", stretch=False)
        self.tree_results.column("status", width=90, anchor="center", stretch=False)
        self.tree_results.column("service", width=150, anchor="center", stretch=False)
        self.tree_results.column("banner", width=500, anchor="w", stretch=True)
        
        # Action Panel (Clear Table, Export CSV/JSON)
        frame_grid_actions = tk.Frame(frame_results, bg=c["bg_panel"], height=40)
        frame_grid_actions.grid(row=2, column=0, sticky="ew", padx=10, pady=8)
        frame_grid_actions.columnconfigure(0, weight=0)
        frame_grid_actions.columnconfigure(1, weight=1)
        frame_grid_actions.columnconfigure(2, weight=0)
        frame_grid_actions.columnconfigure(3, weight=0)
        
        btn_clear_table = tk.Button(frame_grid_actions, text="🧹 Clear Results Table", command=self.action_clear_results, width=20)
        btn_clear_table.btn_type = "clear"
        btn_clear_table.grid(row=0, column=0, sticky="w", ipady=3)
        
        # Spacer
        tk.Label(frame_grid_actions, bg=c["bg_panel"]).grid(row=0, column=1, sticky="ew")
        
        self.btn_export_csv = tk.Button(frame_grid_actions, text="📥 Export CSV", command=self.action_export_csv, width=15)
        self.btn_export_csv.btn_type = "action"
        self.btn_export_csv.grid(row=0, column=2, padx=5, ipady=3)
        
        self.btn_export_json = tk.Button(frame_grid_actions, text="📥 Export JSON", command=self.action_export_json, width=15)
        self.btn_export_json.btn_type = "action"
        self.btn_export_json.grid(row=0, column=3, ipady=3)
        
        # B. Real-Time Terminal Log Section
        frame_logs = tk.Frame(panel_right, bg=c["bg_panel"], relief="solid", bd=1)
        frame_logs.grid(row=1, column=0, sticky="nsew")
        frame_logs.rowconfigure(0, weight=0)  # Log label header
        frame_logs.rowconfigure(1, weight=1)  # Logs text box
        frame_logs.columnconfigure(0, weight=1)
        
        frame_log_header = tk.Frame(frame_logs, bg=c["bg_panel"])
        frame_log_header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame_log_header.columnconfigure(0, weight=1)
        frame_log_header.columnconfigure(1, weight=0)
        
        tk.Label(frame_log_header, text="💻 Real-Time Verbose Scanning Logs (Academic Debug Console):", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        
        btn_clear_terminal = tk.Button(frame_log_header, text="Clear Terminal Logs", command=self.action_clear_logs, width=18)
        btn_clear_terminal.btn_type = "clear"
        btn_clear_terminal.grid(row=0, column=1, sticky="e", ipady=1)
        
        self.text_terminal = tk.Text(frame_logs, font=("Consolas", 10), height=8)
        self.text_terminal.log_terminal = True
        self.text_terminal.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Add scrollbar to logs
        scroll_logs = ttk.Scrollbar(frame_logs, orient="vertical", command=self.text_terminal.yview)
        scroll_logs.grid(row=1, column=0, sticky="nse", padx=10, pady=(0, 10))
        self.text_terminal.configure(yscrollcommand=scroll_logs.set)
        
        # Ensure user can't type directly in read-only terminal, but can copy
        self.text_terminal.bind("<Key>", lambda e: "break" if e.state != 4 else None) # Allow Ctrl+C

        # ----------------------------------------------------------------------
        # 3. BOTTOM PROGRESS & STATISTICS SECTION
        # ----------------------------------------------------------------------
        self.frame_progress = tk.Frame(self, bg=c["bg_panel"], relief="solid", bd=0, height=80)
        self.frame_progress.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.frame_progress.columnconfigure(0, weight=1)
        
        progress_content = tk.Frame(self.frame_progress, bg=c["bg_panel"], padx=15, pady=10)
        progress_content.pack(fill="both", expand=True)
        progress_content.columnconfigure(0, weight=1)
        progress_content.columnconfigure(1, weight=0)
        
        # Metas and speed info labels
        meta_labels = tk.Frame(progress_content, bg=c["bg_panel"])
        meta_labels.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        meta_labels.columnconfigure(0, weight=1)  # Left stats
        meta_labels.columnconfigure(1, weight=1)  # Right stats
        
        self.lbl_progress_status = tk.Label(meta_labels, text="System Idle | Ready for instruction", font=("Segoe UI", 9, "bold"))
        self.lbl_progress_status.grid(row=0, column=0, sticky="w")
        
        self.lbl_active_scan = tk.Label(meta_labels, text="", font=("Consolas", 9, "italic"))
        self.lbl_active_scan.grid(row=0, column=1, sticky="e")
        
        # Progressbar
        self.progressbar = ttk.Progressbar(progress_content, orient="horizontal", mode="determinate")
        self.progressbar.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        # Numerical metrics layout (Ports Scanned, Open Ports, Elapsed Time)
        stats_frame = tk.Frame(progress_content, bg=c["bg_panel"])
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.lbl_scanned_count = tk.Label(stats_frame, text="Scanned: 0 / 0 ports (0.00%)", font=("Segoe UI", 9))
        self.lbl_scanned_count.pack(side="left", padx=(0, 20))
        
        self.lbl_open_count = tk.Label(stats_frame, text="Discovered Open: 0", font=("Segoe UI", 9, "bold"))
        self.lbl_open_count.pack(side="left", padx=(0, 20))
        
        self.lbl_elapsed_time = tk.Label(stats_frame, text="Elapsed Time: 0.00s", font=("Segoe UI", 9))
        self.lbl_elapsed_time.pack(side="left", padx=(0, 20))
        
        self.lbl_time_remaining = tk.Label(stats_frame, text="Estimated Remaining: --", font=("Segoe UI", 9))
        self.lbl_time_remaining.pack(side="left")

        # ----------------------------------------------------------------------
        # 4. BOTTOM LEGAL DISCLAIMER FOOTER
        # ----------------------------------------------------------------------
        disclaimer_frame = tk.Frame(self, bg=c["bg_main"], height=30)
        disclaimer_frame.grid(row=3, column=0, sticky="ew")
        
        lbl_disclaimer = tk.Label(
            disclaimer_frame, 
            text="⚠️ EDUCATIONAL DISCLAIMER: This tool is strictly for educational, lab use, and authorized local systems auditing only. "
                 "Scan only ports on systems you own or have explicit written permission to audit.", 
            font=("Segoe UI", 8, "bold")
        )
        lbl_disclaimer.special_role = "footer"
        lbl_disclaimer.pack(fill="both", expand=True, pady=5)

    # ==========================================================================
    # Real-Time Log Printing & Queue Polling Loop
    # ==========================================================================
    def log_to_terminal(self, message):
        """Appends a timestamped message into the read-only visual log terminal."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        self.text_terminal.configure(state="normal")
        self.text_terminal.insert("end", formatted)
        self.text_terminal.see("end")  # Automatic scroll to bottom
        self.text_terminal.configure(state="disabled")

    def poll_queue(self):
        """
        Periodically checks the scanner enqueued items to update progress counters,
        append discovered items, and gracefully handle thread exit states.
        Runs recursively via tk.after to prevent thread locking.
        """
        if not self.is_scanning:
            return

        try:
            # Process as many enqueued messages as possible in one cycle
            while True:
                # Retrieve an event without blocking the event loop
                event = self.ui_queue.get_nowait()
                etype = event.get("type")
                
                if etype == "progress":
                    scanned = event.get("scanned")
                    percent = event.get("percent")
                    open_cnt = event.get("open_count")
                    
                    # Update progress bars and statistics labels
                    self.progressbar["value"] = percent
                    total_ports = int(self.var_end_port.get()) - int(self.var_start_port.get()) + 1
                    self.lbl_scanned_count.config(text=f"Scanned: {scanned} / {total_ports} ports ({percent:.1f}%)")
                    self.lbl_open_count.config(text=f"Discovered Open: {open_cnt}")
                    
                    # Calculate Elapsed and Estimated remaining times
                    if self.scan_start_time:
                        elapsed = time.time() - self.scan_start_time
                        self.lbl_elapsed_time.config(text=f"Elapsed Time: {elapsed:.2f}s")
                        
                        if scanned > 0 and percent < 100:
                            avg_time_per_port = elapsed / scanned
                            remaining_ports = total_ports - scanned
                            est_rem = avg_time_per_port * remaining_ports
                            self.lbl_time_remaining.config(text=f"Estimated Remaining: {est_rem:.1f}s")
                        else:
                            self.lbl_time_remaining.config(text="Estimated Remaining: --")

                elif etype == "result":
                    # Discovered ports result (open or closed depending on user options)
                    port = event.get("port")
                    status = event.get("status")
                    service = event.get("service")
                    banner = event.get("banner")
                    
                    # Append item to raw results list
                    res_dict = {
                        "port": port,
                        "status": status,
                        "service": service,
                        "banner": banner
                    }
                    self.raw_scan_results.append(res_dict)
                    
                    # Insert into Treeview if it matches current filter conditions
                    self.insert_treeview_row(res_dict)

                elif etype == "active_port":
                    # Update label showing which port is being actively checked
                    port = event.get("port")
                    tid = event.get("thread")
                    self.lbl_active_scan.config(text=f"Thread-{tid} scanning Port {port}...")

                elif etype == "log":
                    text = event.get("text")
                    self.log_to_terminal(text)

                elif etype == "status":
                    text = event.get("text")
                    self.lbl_progress_status.config(text=text)

                elif etype == "finished":
                    self.finalize_scan_state(event)
                    break
                    
                self.ui_queue.task_done()
        except queue.Empty:
            pass

        # Schedule the next poll iteration (e.g., in 50 milliseconds)
        if self.is_scanning:
            self.after(50, self.poll_queue)

    def insert_treeview_row(self, r):
        """Safely inserts a single result item into the visible treeview if it matches filters."""
        # Check Open Ports Only Filter
        if self.filter_show_open_only.get() and r["status"] != "Open":
            return
            
        # Check Text Search Filter
        query = self.filter_text.get().strip().lower()
        if query:
            match = (
                query in str(r["port"]) or
                query in r["status"].lower() or
                query in r["service"].lower() or
                query in r["banner"].lower()
            )
            if not match:
                return

        # Insert item and configure background tags
        tag = "open" if r["status"] == "Open" else "closed"
        self.tree_results.insert("", "end", values=(
            r["port"],
            r["status"],
            r["service"],
            r["banner"]
        ), tags=(tag,))

    def apply_filters(self):
        """Clears the treeview and re-populates entries that match current filter/search terms."""
        # Clear Treeview rows
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
            
        # Insert all matches from cache
        for r in self.raw_scan_results:
            self.insert_treeview_row(r)

    # ==========================================================================
    # Action Click Operations & Control Handlers
    # ==========================================================================
    def action_start_scan(self):
        """Processes validations and launches the background scanner thread."""
        target_raw = self.var_target.get()
        start_raw = self.var_start_port.get()
        end_raw = self.var_end_port.get()
        threads_raw = self.var_threads.get()
        timeout_raw = self.var_timeout.get()
        
        # 1. Validation checks
        # A. Host
        self.lbl_progress_status.config(text="Resolving host address...")
        self.update_idletasks() # Refresh UI instantly
        
        resolved_ip, err_host = utils.validate_host(target_raw)
        if err_host:
            self.lbl_progress_status.config(text="Resolution failed.")
            messagebox.showerror("Invalid Target", err_host, parent=self)
            return
            
        # B. Port Bounds
        start_port, end_port, err_ports = utils.validate_ports(start_raw, end_raw)
        if err_ports:
            self.lbl_progress_status.config(text="Invalid ports.")
            messagebox.showerror("Invalid Ports", err_ports, parent=self)
            return
            
        # C. Thread Range
        thread_cnt, err_threads = utils.validate_threads(threads_raw)
        if err_threads:
            self.lbl_progress_status.config(text="Invalid thread count.")
            messagebox.showerror("Invalid Thread Count", err_threads, parent=self)
            return
            
        # D. Timeout bounds
        try:
            timeout_val = float(timeout_raw)
            if timeout_val <= 0 or timeout_val > 5.0:
                raise ValueError
        except ValueError:
            self.lbl_progress_status.config(text="Invalid timeout.")
            messagebox.showerror("Invalid Timeout", "Timeout must be a decimal between 0.05 and 5.0 seconds.", parent=self)
            return

        # 2. Reset Scan states and clean table
        self.is_scanning = True
        self.raw_scan_results.clear()
        self.apply_filters() # Empties treeview rows
        
        # Toggle state of entry fields
        self.toggle_input_states("disabled")
        
        # Initialize engine
        # Empty the communication queue
        while not self.ui_queue.empty():
            try:
                self.ui_queue.get_nowait()
            except queue.Empty:
                break
                
        self.scan_start_time = time.time()
        self.progressbar["value"] = 0
        self.lbl_open_count.config(text="Discovered Open: 0")
        self.lbl_scanned_count.config(text="Scanned: 0 / 0 ports (0.0%)")
        self.lbl_elapsed_time.config(text="Elapsed Time: 0.00s")
        self.lbl_time_remaining.config(text="Estimated Remaining: Calc...")
        
        self.scanner_engine = scanner.PortScannerEngine(
            target_ip=resolved_ip,
            start_port=start_port,
            end_port=end_port,
            thread_count=thread_cnt,
            timeout=timeout_val,
            ui_queue=self.ui_queue
        )
        
        # Start scanning threads
        self.scanner_engine.start()
        
        # Start checking queue recursively
        self.after(50, self.poll_queue)

    def action_stop_scan(self):
        """Requests background engine termination."""
        if self.scanner_engine and self.is_scanning:
            self.btn_stop.config(state="disabled")
            self.lbl_progress_status.config(text="Stopping scan threads...")
            self.scanner_engine.stop()

    def finalize_scan_state(self, finished_event):
        """Enables interface inputs, records statistics, and saves state logs."""
        self.is_scanning = False
        self.scanner_engine = None
        self.toggle_input_states("normal")
        
        open_cnt = finished_event.get("open_count", 0)
        duration = finished_event.get("duration", 0.0)
        cancelled = finished_event.get("cancelled", False)
        
        # Refresh history panel items list
        self.reload_history_list()
        
        # Final visual confirmation
        self.lbl_active_scan.config(text="")
        if cancelled:
            self.lbl_progress_status.config(text="Scan stopped by user.")
            messagebox.showwarning("Scan Stopped", f"Scan cancelled mid-way.\nOpen Ports Found: {open_cnt}\nTime Elapsed: {duration:.2f}s", parent=self)
        else:
            self.lbl_progress_status.config(text="Scan finished successfully.")
            messagebox.showinfo("Scan Completed", f"Successfully audited host!\nOpen Ports Found: {open_cnt}\nTotal Time: {duration:.2f}s", parent=self)

    def toggle_input_states(self, state):
        """Utility to lock or unlock entry parameters during live scan threads."""
        self.entry_target.config(state=state)
        self.entry_start_port.config(state=state)
        self.entry_end_port.config(state=state)
        self.entry_threads.config(state=state)
        self.entry_timeout.config(state=state)
        
        if state == "disabled":
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.btn_export_csv.config(state="disabled")
            self.btn_export_json.config(state="disabled")
        else:
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.btn_export_csv.config(state="normal")
            self.btn_export_json.config(state="normal")

    def action_clear_results(self):
        """Deletes all cached results and visual rows from the Treeview."""
        if self.is_scanning:
            return
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the results table?", parent=self):
            self.raw_scan_results.clear()
            self.apply_filters()
            self.log_to_terminal("[SYSTEM] Scan results table cleared.")

    def action_clear_logs(self):
        """Wipes visual logs clean."""
        self.text_terminal.configure(state="normal")
        self.text_terminal.delete("1.0", "end")
        self.text_terminal.configure(state="disabled")

    # ==========================================================================
    # Exports Dispatchers
    # ==========================================================================
    def action_export_csv(self):
        """Triggers the CSV writer tool."""
        exporter.export_to_csv(self.raw_scan_results, parent_window=self)

    def action_export_json(self):
        """Triggers the JSON writer tool."""
        exporter.export_to_json(self.raw_scan_results, parent_window=self)

    # ==========================================================================
    # History Persistent Operations
    # ==========================================================================
    def reload_history_list(self):
        """Reloads history array and prints visual summaries in the sidebar Listbox."""
        self.listbox_history.delete(0, "end")
        history = utils.load_history()
        
        for record in history:
            line = f"{record['timestamp']} | {record['target']} (Open: {record['open_count']})"
            self.listbox_history.insert("end", line)

    def action_select_history(self, event):
        """Callback for selected historical entries. Fills target parameter values automatically."""
        selection = self.listbox_history.curselection()
        if not selection:
            return
            
        index = selection[0]
        history = utils.load_history()
        if index < len(history):
            record = history[index]
            target_host = record.get("target")
            ports_range = record.get("ports", "1-1024")
            
            # Autocomplete inputs
            self.var_target.set(target_host)
            
            try:
                start_p, end_p = ports_range.split("-")
                self.var_start_port.set(start_p)
                self.var_end_port.set(end_p)
            except Exception:
                pass
                
            self.log_to_terminal(f"[HISTORY] Autocompleted parameters for target '{target_host}' from historical records.")

    def action_clear_history(self):
        """Deletes history JSON log database."""
        if messagebox.askyesno("Confirm Clear", "Do you want to permanently delete all local scan history?", parent=self):
            if os.path.exists(utils.HISTORY_FILE):
                try:
                    os.remove(utils.HISTORY_FILE)
                except Exception:
                    pass
            self.reload_history_list()
            self.log_to_terminal("[HISTORY] Local history database deleted.")

    # ==========================================================================
    # Column Sorting Logic
    # ==========================================================================
    def sort_column(self, col, reverse):
        """
        Sorts the treeview by column. Handles numerical values correctly.
        
        Parameters:
            col (str): Column index to sort.
            reverse (bool): Reverse boolean.
        """
        # Retrieve all items from treeview
        items = [(self.tree_results.set(k, col), k) for k in self.tree_results.get_children('')]
        
        # Sort items. If port, convert to integer to sort numerically
        if col == "port":
            try:
                items.sort(key=lambda t: int(t[0]), reverse=reverse)
            except ValueError:
                items.sort(reverse=reverse)
        else:
            items.sort(reverse=reverse)
            
        # Re-arrange elements in Treeview
        for index, (val, k) in enumerate(items):
            self.tree_results.move(k, '', index)
            
        # Reverse sort next time user clicks this column heading
        self.tree_results.heading(col, command=lambda: self.sort_column(col, not reverse))

    # ==========================================================================
    # Educational Guides Modals
    # ==========================================================================
    def show_quick_guide(self):
        """Displays a clean informational guide summarizing core cyber networking concepts."""
        guide_text = (
            "========================================================\n"
            "   📚 SECUREPORT SCANNER - EDUCATIONAL GUIDE\n"
            "========================================================\n\n"
            "This software is an educational tool designed to demonstrate socket\n"
            "programming, thread concurrency, and port inspection. Here are the keys:\n\n"
            "1. Target Host\n"
            "   An IP address (e.g. 127.0.0.1) or a Domain (e.g. scanme.nmap.org).\n"
            "   DNS resolution translates domains into IP addresses before scanning.\n\n"
            "2. Port Scanning & TCP Handshake\n"
            "   We use standard socket.connect_ex() to send a TCP SYN packet.\n"
            "   - If the system replies with SYN-ACK, connect_ex returns 0 (OPEN).\n"
            "   - If it replies with RST or silent drop, port is CLOSED/FILTERED.\n\n"
            "3. Multi-Threading Concurrency\n"
            "   Threads let us run scans in parallel. If we scan 1000 ports with a 0.5s\n"
            "   timeout, 1 thread takes 500s. 50 threads reduce that to just 10s!\n\n"
            "4. Service Resolution\n"
            "   We query standard registers (via getservbyport) to map common ports\n"
            "   to human services (e.g. 22 -> SSH, 80 -> HTTP, 443 -> HTTPS).\n\n"
            "5. Safe Banner Grabbing\n"
            "   When a port is OPEN, we attempt to read welcoming strings (like the SSH\n"
            "   version or HTTP headers). The response is safely read up to 1024 bytes.\n\n"
            "6. Security & Ethics\n"
            "   Scanning causes traffic. Scanning unauthorized devices is illegal or\n"
            "   violates terms of service. Practice ONLY on localhost or authorized targets.\n"
        )
        
        # Display as a clean popup scrollable window for the user
        guide_win = tk.Toplevel(self)
        guide_win.title("Educational Cybersecurity Guide")
        guide_win.geometry("560x520")
        guide_win.resizable(False, False)
        guide_win.configure(bg=self.current_theme["bg_main"])
        guide_win.transient(self) # Keep relative to main parent
        guide_win.grab_set() # Modal lock
        
        txt = tk.Text(guide_win, font=("Consolas", 10), bg=self.current_theme["terminal_bg"], fg=self.current_theme["text_primary"], padx=15, pady=15)
        txt.pack(fill="both", expand=True, padx=15, pady=(15, 10))
        
        txt.insert("1.0", guide_text)
        txt.configure(state="disabled")
        
        btn_close = tk.Button(guide_win, text="Got it! Close Guide", command=guide_win.destroy, height=1, bg=self.current_theme["accent_cyan"], fg=self.current_theme["bg_main"])
        btn_close.btn_type = "start"
        btn_close.pack(pady=10, ipady=4, ipadx=10)
        self._colorize_widgets(guide_win)

import os
