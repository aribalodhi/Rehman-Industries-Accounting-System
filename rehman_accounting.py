"""
RIAS - Rehman Industries Accounting System.
A professional double-entry bookkeeping desktop application using Python, Tkinter, and SQLite.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv
import os
import shutil
import logging
import tempfile
import sys
from typing import Optional, List, Dict, Any, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Import from project modules
from database import Database
from constants import *
from validators import (
    validate_date,
    validate_amount,
    validate_positive_amount,
    validate_debit_credit_pair,
    validate_date_range,
    validate_account_name,
    validate_account_type,
    validate_account_data,
    format_amount,
    parse_cash_account_names,
)
from settings_manager import SettingsManager

# ================= DATABASE =================
# Database class is now imported from database.py

# ================= INITIALIZATION =================
# Initialize data directory and database
os.makedirs(DATA_DIR, exist_ok=True)

# Copy seed database if local one doesn't exist
if not os.path.exists(DB_PATH) and os.path.exists(SEED_DB_PATH):
    shutil.copy2(SEED_DB_PATH, DB_PATH)

# Initialize database connection
db = Database(DB_PATH)

# Initialize settings manager
settings_manager = SettingsManager()

# ================= LOGGING SETUP =================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


# ================= BACKUP & INTEGRITY FUNCTIONS =================
def backup_database(tag: str = BACKUP_TAG_MANUAL) -> None:
    """
    Create a backup copy of the database.

    Args:
        tag: Backup tag identifier (startup, pre_save, manual).
    """
    if not os.path.exists(db.path):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime(DATETIME_FORMAT)
    backup_name = f"rehman_industries_{tag}_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(db.path, backup_path)
    logging.info(f"Database backup created: {backup_name}")


def check_db_integrity() -> None:
    """Check database integrity and display warning if issues found."""
    try:
        is_ok, msg = db.check_integrity()
        if is_ok:
            set_status(MSG_DB_INTEGRITY_OK)
        else:
            messagebox.showwarning("Database Check", msg)
    except Exception as e:
        logging.exception("Integrity check failed")
        messagebox.showwarning("Database Check", f"Integrity check failed. See rias.log.\n{str(e)}")


def check_unbalanced_vouchers() -> None:
    """Check for unbalanced vouchers in the database."""
    try:
        rows = fetch_all("""
            SELECT v.id, v.date, ROUND(SUM(t.debit), 2), ROUND(SUM(t.credit), 2)
            FROM vouchers v
            JOIN transactions t ON v.id = t.voucher_id
            GROUP BY v.id, v.date
            HAVING ROUND(SUM(t.debit), 2) <> ROUND(SUM(t.credit), 2)
            ORDER BY v.id
        """)
        if rows:
            messagebox.showwarning(
                "Unbalanced Vouchers Found",
                f"{len(rows)} existing voucher(s) are unbalanced. Review Voucher History before reporting.",
            )
    except Exception as e:
        logging.exception("Unbalanced voucher check failed")


# ================= MAIN WINDOW =================
root = tk.Tk()
root.title(APP_TITLE)
root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

# ================= STYLING =================
style = ttk.Style()
style.theme_use("clam")

# Load current theme from settings
CURRENT_THEME: str = settings_manager.get_theme()

# Theme color variables (will be updated by apply_theme)
PRIMARY: str = ""
PRIMARY_SOFT: str = ""
ACCENT: str = ""
ACCENT_HOVER: str = ""
ACCENT_SOFT: str = ""
SURFACE: str = ""
SURFACE_ALT: str = ""
SURFACE_SOFT: str = ""
MUTED: str = ""
LINE: str = ""
SIDEBAR_BG: str = ""
HEADING_BG: str = ""
ROW_EVEN: str = ""
GOOD: str = ""
WARN: str = ""
BAD: str = ""


def set_theme_palette(theme_name: str) -> None:
    """
    Update global color variables from a theme.

    Args:
        theme_name: Name of the theme to apply.
    """
    global CURRENT_THEME, PRIMARY, PRIMARY_SOFT, ACCENT, ACCENT_HOVER, ACCENT_SOFT
    global SURFACE, SURFACE_ALT, SURFACE_SOFT, MUTED, LINE, SIDEBAR_BG, HEADING_BG
    global ROW_EVEN, GOOD, WARN, BAD
    
    palette = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    CURRENT_THEME = theme_name if theme_name in THEMES else DEFAULT_THEME
    PRIMARY = palette["PRIMARY"]
    PRIMARY_SOFT = palette["PRIMARY_SOFT"]
    ACCENT = palette["ACCENT"]
    ACCENT_HOVER = palette["ACCENT_HOVER"]
    ACCENT_SOFT = palette["ACCENT_SOFT"]
    SURFACE = palette["SURFACE"]
    SURFACE_ALT = palette["SURFACE_ALT"]
    SURFACE_SOFT = palette["SURFACE_SOFT"]
    MUTED = palette["MUTED"]
    LINE = palette["LINE"]
    SIDEBAR_BG = palette["SIDEBAR_BG"]
    HEADING_BG = palette["HEADING_BG"]
    ROW_EVEN = palette["ROW_EVEN"]
    GOOD = palette["GOOD"]
    WARN = palette["WARN"]
    BAD = palette["BAD"]


def apply_theme(theme_name: Optional[str] = None) -> None:
    """
    Apply a theme to the entire UI.

    Args:
        theme_name: Theme name to apply. Uses current theme if None.
    """
    set_theme_palette(theme_name or CURRENT_THEME)
    root.configure(bg=SURFACE)
    style.configure("TFrame", background=SURFACE)
    style.configure("TLabel", background=SURFACE, foreground=PRIMARY, font=FONT_BODY)
    style.configure("TButton", font=FONT_BODY, padding=BUTTON_PADDING, borderwidth=1, relief="flat", background=SURFACE_ALT, foreground=PRIMARY)
    style.map("TButton", background=[("active", SURFACE_SOFT)])
    style.configure("Primary.TButton", font=FONT_BODY, background=ACCENT, foreground="white", borderwidth=0, padding=PRIMARY_BUTTON_PADDING)
    style.map("Primary.TButton", background=[("active", ACCENT_HOVER)], foreground=[("active", "white")])
    style.configure("Header.TLabel", font=FONT_HEADER, foreground=PRIMARY)
    style.configure("SubHeader.TLabel", font=FONT_SUBHEADER, foreground=MUTED)
    style.configure("Muted.TLabel", font=FONT_SMALL, foreground=MUTED)
    style.configure("Good.TLabel", font=FONT_SUBHEADER, foreground=GOOD)
    style.configure("Warn.TLabel", font=FONT_SUBHEADER, foreground=WARN)
    style.configure("Bad.TLabel", font=FONT_SUBHEADER, foreground=BAD)
    style.configure("HeaderBar.TFrame", background=SURFACE_ALT)
    style.configure("HeaderBar.TLabel", background=SURFACE_ALT, foreground=PRIMARY)
    style.configure("HeaderDate.TLabel", background=SURFACE_ALT, foreground=MUTED, font=FONT_SMALL)
    style.configure("BrandMain.TLabel", background=SURFACE_ALT, foreground=PRIMARY, font=FONT_BRAND_MAIN)
    style.configure("BrandSub.TLabel", background=SURFACE_ALT, foreground=MUTED, font=FONT_SMALL)
    style.configure("BrandChip.TLabel", background=ACCENT, foreground="white", font=FONT_BRAND_CHIP, padding=(10, 3))
    style.configure("Card.TFrame", background=SURFACE_ALT, borderwidth=1, relief="solid")
    style.configure("CardTitle.TLabel", background=SURFACE_ALT, foreground=MUTED, font=FONT_SUBHEADER)
    style.configure("CardValue.TLabel", background=SURFACE_ALT, foreground=PRIMARY, font=FONT_CARD_VALUE)
    style.configure("Sidebar.TFrame", background=SIDEBAR_BG)
    style.configure("Sidebar.TLabel", background=SIDEBAR_BG, foreground="white", font=FONT_SIDEBAR)
    style.configure("Nav.TButton", background=SIDEBAR_BG, foreground="white", anchor="w", padding=NAV_BUTTON_PADDING, borderwidth=0)
    style.map("Nav.TButton", background=[("active", PRIMARY_SOFT), ("selected", ACCENT)], foreground=[("active", "white"), ("selected", "white")])
    style.configure("TEntry", fieldbackground=SURFACE_ALT, foreground=PRIMARY)
    style.configure("TCombobox", fieldbackground=SURFACE_ALT, foreground=PRIMARY)
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE_ALT)], foreground=[("readonly", PRIMARY)])
    style.configure("Treeview", font=FONT_BODY, rowheight=TREEVIEW_ROW_HEIGHT, background=SURFACE_ALT, fieldbackground=SURFACE_ALT)
    style.configure("Treeview.Heading", font=FONT_SUBHEADER, background=HEADING_BG, foreground="white")
    style.map("Treeview.Heading", background=[("active", PRIMARY_SOFT)])
    style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", PRIMARY)])

    status_bar.configure(foreground=MUTED)
    if "sidebar_subtitle" in globals():
        sidebar_subtitle.configure(background=SIDEBAR_BG, foreground=MUTED)
    for tree_name in ("accounts_tree", "voucher_tree", "report_tree", "vouchers_tree", "lines_tree"):
        tree = globals().get(tree_name)
        if tree is not None:
            tree.tag_configure("odd", background=SURFACE_ALT)
            tree.tag_configure("even", background=ROW_EVEN)


set_theme_palette(CURRENT_THEME)

# ================= STATUS BAR =================
status_var = tk.StringVar(value=MSG_READY)
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", padding=(12, 6), style="Muted.TLabel")
status_bar.pack(side="bottom", fill="x")
card_anim_jobs: Dict[str, Any] = {}
tree_anim_jobs: Dict[str, Any] = {}
apply_theme(CURRENT_THEME)


def set_status(msg: str, duration: int = STATUS_MESSAGE_DURATION) -> None:
    """
    Display a status message that auto-reverts after a duration.

    Args:
        msg: Status message to display.
        duration: Duration in milliseconds before reverting to "Ready".
    """
    status_var.set(msg)
    status_bar.configure(foreground=PRIMARY)
    root.after(duration, lambda: (status_var.set(MSG_READY), status_bar.configure(foreground=MUTED)))


# ================= MAIN LAYOUT =================
main = ttk.Frame(root)
main.pack(fill="both", expand=True)

sidebar = ttk.Frame(main, width=SIDEBAR_WIDTH, padding=SIDEBAR_PADDING, style="Sidebar.TFrame")
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

content = ttk.Frame(main, padding=0)
content.pack(side="right", fill="both", expand=True)

content_header = ttk.Frame(content, padding=HEADER_PADDING, style="HeaderBar.TFrame")
content_header.pack(fill="x")
header_row = ttk.Frame(content_header, style="HeaderBar.TFrame")
header_row.pack(fill="x")

brand_block = ttk.Frame(header_row, style="HeaderBar.TFrame")
brand_block.pack(side="left", anchor="w")
ttk.Label(brand_block, text=APP_TITLE, style="BrandMain.TLabel").pack(anchor="w")

meta_row = ttk.Frame(brand_block, style="HeaderBar.TFrame")
meta_row.pack(anchor="w", pady=(2, 0))
ttk.Label(meta_row, text=APP_NAME, style="BrandChip.TLabel").pack(side="left")
ttk.Label(meta_row, text=APP_TAGLINE, style="BrandSub.TLabel").pack(side="left", padx=(10, 0))

ttk.Label(header_row, text=datetime.now().strftime(HEADER_DATE_FORMAT), style="HeaderDate.TLabel").pack(side="right", anchor="e")

content_area = ttk.Frame(content, padding=CONTENT_PADDING)
content_area.pack(fill="both", expand=True)

# ================= NAVIGATION =================
frames: Dict[str, tk.Widget] = {}
nav_buttons: Dict[str, tk.Widget] = {}
current_frame_name: Optional[str] = None


def show_frame(name: str, frame: tk.Widget) -> None:
    """
    Show a frame and update navigation state.

    Args:
        name: Frame name/title.
        frame: Frame widget to display.
    """
    global current_frame_name
    for f in frames.values():
        f.pack_forget()
    frame.pack(fill="both", expand=True)
    set_active_nav(name)
    current_frame_name = name


def nav_button(text: str, frame: tk.Widget) -> None:
    """
    Create and register a navigation button.

    Args:
        text: Button label.
        frame: Frame this button navigates to.
    """
    btn = ttk.Button(sidebar, text=text, style="Nav.TButton", command=lambda: show_frame(text, frame))
    btn.pack(fill="x", pady=6)
    nav_buttons[text] = btn


def set_active_nav(name: str) -> None:
    """
    Update navigation button states to show active section.

    Args:
        name: Name of the currently active section.
    """
    for key, btn in nav_buttons.items():
        btn.state(["!selected"])
        if key == name:
            btn.state(["selected"])


# ================= UTILITY FUNCTIONS =================
def execute_query(query: str, params: Tuple[Any, ...] = (), commit: bool = True) -> sqlite3.Cursor:
    """Execute a database query."""
    return db.execute(query, params, commit=commit)


def fetch_one(query: str, params: Tuple[Any, ...] = ()) -> Optional[Tuple[Any, ...]]:
    """Fetch a single row from the database."""
    return db.fetch_one(query, params)


def fetch_all(query: str, params: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
    """Fetch all matching rows from the database."""
    return db.fetch_all(query, params)



# ================= REUSABLE TREEVIEW =================
def create_treeview(
    parent: tk.Widget,
    columns: Tuple[str, ...],
    headings: Tuple[str, ...],
    height: int = DEFAULT_TREEVIEW_HEIGHT,
    numeric_cols: Optional[set] = None,
    pack: bool = True,
) -> ttk.Treeview:
    """
    Create a themed treeview widget.

    Args:
        parent: Parent widget.
        columns: Column identifiers.
        headings: Column heading labels.
        height: Number of visible rows.
        numeric_cols: Set of column names to right-align.
        pack: Whether to automatically pack the widget.

    Returns:
        Configured Treeview widget.
    """
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=height)
    numeric_cols = set(numeric_cols or [])
    tree.tag_configure("odd", background=SURFACE_ALT)
    tree.tag_configure("even", background=ROW_EVEN)
    for col, hd in zip(columns, headings):
        is_numeric = col in numeric_cols
        anchor = "e" if is_numeric else "w"
        tree.heading(col, text=hd, anchor=anchor)
        tree.column(col, anchor=anchor)
    if pack:
        tree.pack(fill="both", expand=True, pady=12)
    return tree


def animate_number_label(
    label: ttk.Label, target: float, duration: int = CARD_ANIMATION_DURATION, steps: int = CARD_ANIMATION_STEPS
) -> None:
    """
    Animate a label number from current to target value.

    Args:
        label: Label widget to animate.
        target: Target numeric value.
        duration: Animation duration in milliseconds.
        steps: Number of animation frames.
    """
    key = str(label)
    current_job = card_anim_jobs.get(key)
    if current_job:
        try:
            root.after_cancel(current_job)
        except Exception:
            pass
    try:
        start = float(str(label.cget("text")).replace(",", ""))
    except Exception:
        start = 0.0
    target = round(float(target), FLOAT_PRECISION)
    if steps <= 1:
        label.config(text=format_amount(target))
        return
    delta = target - start

    def tick(i: int = 1) -> None:
        if i >= steps:
            label.config(text=format_amount(target))
            card_anim_jobs.pop(key, None)
            return
        t = i / steps
        eased = 1 - (1 - t) * (1 - t)
        label.config(text=format_amount(start + delta * eased))
        card_anim_jobs[key] = root.after(max(MIN_FRAME_DELAY, duration // steps), lambda: tick(i + 1))

    card_anim_jobs[key] = root.after(0, tick)


def animate_tree_rows(tree: ttk.Treeview, rows: List[Tuple[Any, ...]], delay_ms: int = TREE_ANIMATION_DELAY_MS) -> None:
    """
    Animate insertion of rows into a treeview.

    Args:
        tree: Treeview widget.
        rows: List of row tuples to insert.
        delay_ms: Delay between row insertions in milliseconds.
    """
    key = str(tree)
    current_job = tree_anim_jobs.get(key)
    if current_job:
        try:
            root.after_cancel(current_job)
        except Exception:
            pass
    tree.delete(*tree.get_children())
    if not rows:
        return
    # Skip animation for large datasets
    if len(rows) > TREE_ANIMATION_THRESHOLD:
        for idx, values in enumerate(rows):
            insert_tree_row(tree, values, idx)
        return

    def insert_next(idx: int = 0) -> None:
        insert_tree_row(tree, rows[idx], idx)
        if idx + 1 < len(rows):
            tree_anim_jobs[key] = root.after(delay_ms, lambda: insert_next(idx + 1))
        else:
            tree_anim_jobs.pop(key, None)

    tree_anim_jobs[key] = root.after(0, insert_next)


def animate_window_fade_in(duration: int = WINDOW_FADE_IN_DURATION, steps: int = WINDOW_FADE_IN_STEPS) -> None:
    """
    Fade in the main window on startup.

    Args:
        duration: Fade duration in milliseconds.
        steps: Number of fade animation frames.
    """
    try:
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        return
    step = 1.0 / steps

    def tick(i: int = 0) -> None:
        value = min(1.0, i * step)
        try:
            root.attributes("-alpha", value)
        except tk.TclError:
            return
        if i < steps:
            root.after(max(MIN_FRAME_DELAY, duration // steps), lambda: tick(i + 1))

    tick(0)


def insert_tree_row(tree: ttk.Treeview, values: Tuple[Any, ...], row_index: int) -> None:
    """
    Insert a row into a treeview with alternating row coloring.

    Args:
        tree: Treeview widget.
        values: Row values as tuple.
        row_index: Zero-based row index (for alternating colors).
    """
    tag = "even" if row_index % 2 == 0 else "odd"
    tree.insert("", "end", values=values, tags=(tag,))


# Note: validate_date is imported from validators module
def is_valid_date(value: str) -> bool:
    """Wrapper for validate_date from validators module."""
    return validate_date(value)

# ================= CHART OF ACCOUNTS =================
frame_accounts = ttk.Frame(content_area)
frames["Accounts"] = frame_accounts
ttk.Label(frame_accounts, text="Chart of Accounts", style="Header.TLabel").pack(anchor="w")
ttk.Label(frame_accounts, text="Manage your accounts list", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 12))

form_acc = ttk.Frame(frame_accounts)
form_acc.pack(fill="x", pady=10)
form_acc.grid_columnconfigure(1, weight=1)
form_acc.grid_columnconfigure(3, weight=1)

ttk.Label(form_acc, text="Account Name").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
ttk.Label(form_acc, text="Account Type").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

acc_name = ttk.Entry(form_acc, width=40)
acc_type = ttk.Combobox(form_acc, values=["Asset", "Liability", "Income", "Expense"], state="readonly", width=37)
acc_name.grid(row=0, column=1, pady=4, sticky="ew")
acc_type.grid(row=1, column=1, pady=4, sticky="ew")

ttk.Label(form_acc, text="Search").grid(row=0, column=2, sticky="w", padx=(20, 6), pady=4)
search_acc = ttk.Entry(form_acc, width=26)
search_acc.grid(row=0, column=3, pady=4, sticky="ew")
ttk.Label(form_acc, text="Type Filter").grid(row=1, column=2, sticky="w", padx=(20, 6), pady=4)
type_filter = ttk.Combobox(form_acc, values=["All", "Asset", "Liability", "Income", "Expense"], state="readonly", width=23)
type_filter.grid(row=1, column=3, pady=4, sticky="ew")
type_filter.set("All")

accounts_tree = create_treeview(frame_accounts, ["Name", "Type"], ["Account Name", "Type"])
selected_account_name = None

def refresh_accounts(filter_text=""):
    accounts_tree.delete(*accounts_tree.get_children())
    filter_type = type_filter.get()
    if filter_type and filter_type != "All":
        rows = fetch_all(
            "SELECT name, type FROM accounts WHERE name LIKE ? AND type=? ORDER BY name",
            (f"%{filter_text}%", filter_type),
        )
    else:
        rows = fetch_all(
            "SELECT name, type FROM accounts WHERE name LIKE ? ORDER BY name",
            (f"%{filter_text}%",),
        )
    for i, r in enumerate(rows):
        insert_tree_row(accounts_tree, r, i)
    refresh_dropdowns()

def add_account():
    name = acc_name.get().strip()
    acc_type_value = acc_type.get().strip()
    if not name or not acc_type_value:
        messagebox.showerror("Error", "All fields required")
        return
    try:
        existing = fetch_one("SELECT 1 FROM accounts WHERE LOWER(name)=LOWER(?)", (name,))
        if existing:
            messagebox.showerror("Error", "Account already exists")
            return
        execute_query("INSERT INTO accounts (name, type) VALUES (?, ?)", (name, acc_type_value))
        acc_name.delete(0, tk.END)
        acc_type.set("")
        refresh_accounts()
        acc_name.focus_set()
        set_status("Account added")
    except Exception:
        logging.exception("Add account failed")
        messagebox.showerror("Error", "Account already exists")

def clear_account_form():
    global selected_account_name
    selected_account_name = None
    acc_name.delete(0, tk.END)
    acc_type.set("")
    acc_name.focus_set()
    set_status("Form cleared")

def update_account():
    global selected_account_name
    if not selected_account_name:
        messagebox.showerror("Error", "Select an account to update")
        return
    name = acc_name.get().strip()
    acc_type_value = acc_type.get().strip()
    if not name or not acc_type_value:
        messagebox.showerror("Error", "All fields required")
        return
    try:
        existing = fetch_one(
            "SELECT 1 FROM accounts WHERE LOWER(name)=LOWER(?) AND name<>?",
            (name, selected_account_name),
        )
        if existing:
            messagebox.showerror("Error", "Account name already exists")
            return
        execute_query(
            "UPDATE accounts SET name=?, type=? WHERE name=?",
            (name, acc_type_value, selected_account_name),
        )
        selected_account_name = name
        refresh_accounts()
        acc_name.focus_set()
        set_status("Account updated")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Account name already exists")
    except Exception:
        logging.exception("Update account failed")
        messagebox.showerror("Error", "Failed to update account")

def delete_account():
    global selected_account_name
    if not selected_account_name:
        messagebox.showerror("Error", "Select an account to delete")
        return
    if not messagebox.askyesno("Confirm", "Delete selected account?"):
        return
    try:
        execute_query("DELETE FROM accounts WHERE name=?", (selected_account_name,))
        selected_account_name = None
        refresh_accounts()
        clear_account_form()
        acc_name.focus_set()
        set_status("Account deleted")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Account is used in transactions")
    except Exception:
        logging.exception("Delete account failed")
        messagebox.showerror("Error", "Failed to delete account")

def on_account_select(event):
    global selected_account_name
    selection = accounts_tree.selection()
    if not selection:
        return
    values = accounts_tree.item(selection[0], "values")
    if not values:
        return
    selected_account_name = values[0]
    acc_name.delete(0, tk.END)
    acc_name.insert(0, values[0])
    acc_type.set(values[1])

accounts_tree.bind("<<TreeviewSelect>>", on_account_select)
accounts_tree.bind("<Delete>", lambda e: delete_account())

def on_account_search(event=None):
    refresh_accounts(search_acc.get().strip())

search_acc.bind("<KeyRelease>", on_account_search)
type_filter.bind("<<ComboboxSelected>>", lambda e: refresh_accounts(search_acc.get().strip()))
search_acc.bind("<Escape>", lambda e: (search_acc.delete(0, tk.END), refresh_accounts()))

actions_acc = ttk.Frame(frame_accounts)
actions_acc.pack(anchor="w", pady=6)
ttk.Button(actions_acc, text="Add Account", command=add_account, style="Primary.TButton").grid(row=0, column=0, padx=(0, 8))
ttk.Button(actions_acc, text="Update Selected", command=update_account).grid(row=0, column=1, padx=(0, 8))
ttk.Button(actions_acc, text="Delete Selected", command=delete_account).grid(row=0, column=2, padx=(0, 8))
ttk.Button(actions_acc, text="Clear", command=clear_account_form).grid(row=0, column=3)
ttk.Button(actions_acc, text="Clear Search", command=lambda: (search_acc.delete(0, tk.END), refresh_accounts())).grid(row=0, column=4, padx=(8, 0))

# Make primary action visible near inputs
actions_acc_top = ttk.Frame(form_acc)
actions_acc_top.grid(row=2, column=1, sticky="w", pady=(6, 0))
ttk.Button(actions_acc_top, text="Add Account", command=add_account, style="Primary.TButton").grid(row=0, column=0, padx=(0, 8))
ttk.Button(actions_acc_top, text="Delete Selected", command=delete_account).grid(row=0, column=1, padx=(0, 8))

# ================= VOUCHER ENTRY =================
frame_voucher = ttk.Frame(content_area)
frames["Voucher Entry"] = frame_voucher
ttk.Label(frame_voucher, text="Voucher Entry", style="Header.TLabel").pack(anchor="w")
ttk.Label(frame_voucher, text="Record balanced debit and credit lines", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 12))
voucher_mode_var = tk.StringVar(value="New Voucher")
ttk.Label(frame_voucher, textvariable=voucher_mode_var, style="Muted.TLabel").pack(anchor="w")

form_voucher = ttk.Frame(frame_voucher)
form_voucher.pack(fill="x", pady=10)
form_voucher.grid_columnconfigure(0, weight=2)
form_voucher.grid_columnconfigure(1, weight=1)
form_voucher.grid_columnconfigure(2, weight=1)
form_voucher.grid_columnconfigure(3, weight=0)

ttk.Label(form_voucher, text="Date").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
ttk.Label(form_voucher, text="Description").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
ttk.Label(form_voucher, text="Account").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)
ttk.Label(form_voucher, text="Debit").grid(row=2, column=1, sticky="w", padx=(0, 10), pady=4)
ttk.Label(form_voucher, text="Credit").grid(row=2, column=2, sticky="w", padx=(0, 10), pady=4)

date_entry = ttk.Entry(form_voucher, width=20)
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
desc_entry = ttk.Entry(form_voucher, width=60)
account_cb = ttk.Combobox(form_voucher, state="readonly", width=30)
debit_entry = ttk.Entry(form_voucher, width=15)
credit_entry = ttk.Entry(form_voucher, width=15)

date_entry.grid(row=0, column=1, pady=4, sticky="w")
desc_entry.grid(row=1, column=1, columnspan=3, pady=4, sticky="ew")
account_cb.grid(row=2, column=0, pady=4, sticky="ew")
debit_entry.grid(row=2, column=1, pady=4, sticky="ew")
credit_entry.grid(row=2, column=2, pady=4, sticky="ew")

ttk.Button(form_voucher, text="Today", command=lambda: date_entry.delete(0, tk.END) or date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))).grid(row=0, column=2, padx=(6, 0), sticky="w")

voucher_hint = ttk.Label(frame_voucher, text="", style="Muted.TLabel")
voucher_hint.pack(anchor="w")

voucher_tree = create_treeview(
    frame_voucher,
    ["Account", "Debit", "Credit"],
    ["Account", "Debit", "Credit"],
    height=12,
    numeric_cols=["Debit", "Credit"],
)
entries = []
current_voucher_id = None
voucher_tree.bind("<Delete>", lambda e: remove_selected_line())

totals_frame = ttk.Frame(frame_voucher)
totals_frame.pack(anchor="w", pady=(6, 0))
total_debit_var = tk.StringVar(value="0.00")
total_credit_var = tk.StringVar(value="0.00")
balance_diff_var = tk.StringVar(value="0.00")
ttk.Label(totals_frame, text="Total Debit:", style="Muted.TLabel").grid(row=0, column=0, padx=(0, 6))
ttk.Label(totals_frame, textvariable=total_debit_var, style="SubHeader.TLabel").grid(row=0, column=1, padx=(0, 12))
ttk.Label(totals_frame, text="Total Credit:", style="Muted.TLabel").grid(row=0, column=2, padx=(0, 6))
ttk.Label(totals_frame, textvariable=total_credit_var, style="SubHeader.TLabel").grid(row=0, column=3, padx=(0, 12))
ttk.Label(totals_frame, text="Difference:", style="Muted.TLabel").grid(row=0, column=4, padx=(0, 6))
balance_diff_label = ttk.Label(totals_frame, textvariable=balance_diff_var, style="SubHeader.TLabel")
balance_diff_label.grid(row=0, column=5)

def update_voucher_totals():
    total_debit = sum(e[2] for e in entries)
    total_credit = sum(e[3] for e in entries)
    diff = round(total_debit - total_credit, 2)
    total_debit_var.set(format_amount(total_debit))
    total_credit_var.set(format_amount(total_credit))
    balance_diff_var.set(format_amount(abs(diff)))
    if not entries:
        balance_diff_label.configure(style="SubHeader.TLabel")
        voucher_hint.configure(style="Muted.TLabel")
        return
    if diff == 0:
        balance_diff_label.configure(style="Good.TLabel")
        voucher_hint.configure(style="Muted.TLabel")
    elif abs(diff) <= 10:
        balance_diff_label.configure(style="Warn.TLabel")
        voucher_hint.configure(style="Warn.TLabel")
    else:
        balance_diff_label.configure(style="Bad.TLabel")
        voucher_hint.configure(style="Bad.TLabel")
    if entries and round(total_debit, 2) != round(total_credit, 2):
        voucher_hint.config(text="Totals must balance to save.")
    elif entries:
        voucher_hint.config(text="")

def set_voucher_mode(editing):
    voucher_mode_var.set("Edit Voucher" if editing else "New Voucher")
    label = "Update Voucher" if editing else "Save Voucher"
    save_btn.config(text=label)
    top_save_btn.config(text=label)

def clear_voucher_form():
    global current_voucher_id
    current_voucher_id = None
    entries.clear()
    voucher_tree.delete(*voucher_tree.get_children())
    date_entry.delete(0, tk.END)
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    desc_entry.delete(0, tk.END)
    account_cb.set("")
    debit_entry.delete(0, tk.END)
    credit_entry.delete(0, tk.END)
    voucher_hint.config(text="")
    set_voucher_mode(False)
    update_voucher_totals()
    set_status("New voucher ready")

def rebuild_voucher_tree():
    voucher_tree.delete(*voucher_tree.get_children())
    for i, e in enumerate(entries):
        insert_tree_row(voucher_tree, (e[1], format_amount(e[2]), format_amount(e[3])), i)

def remove_selected_line():
    selection = voucher_tree.selection()
    if not selection:
        voucher_hint.config(text="Select a line to remove.")
        return
    idx = voucher_tree.index(selection[0])
    if idx < 0 or idx >= len(entries):
        return
    entries.pop(idx)
    rebuild_voucher_tree()
    update_voucher_totals()
    voucher_hint.config(text="Line removed.")

def add_line():
    if not is_valid_date(date_entry.get().strip()):
        voucher_hint.config(text="Date must be in YYYY-MM-DD format.")
        return
    d = parse_amount(debit_entry.get())
    c = parse_amount(credit_entry.get())
    if d is None or c is None:
        voucher_hint.config(text="Enter valid numbers for Debit/Credit.")
        return
    if d < 0 or c < 0:
        voucher_hint.config(text="Debit/Credit must be positive values.")
        return
    if (d > 0 and c > 0) or (d == 0 and c == 0):
        voucher_hint.config(text="Enter either debit or credit, not both or none.")
        return
    row = fetch_one("SELECT id FROM accounts WHERE name=?", (account_cb.get(),))
    if not row:
        voucher_hint.config(text="Select a valid account.")
        return
    acc_id = row[0]
    entries.append((acc_id, account_cb.get(), d, c))
    insert_tree_row(voucher_tree, (account_cb.get(), format_amount(d), format_amount(c)), len(entries) - 1)
    debit_entry.delete(0, tk.END)
    credit_entry.delete(0, tk.END)
    voucher_hint.config(text="Line added.")
    update_voucher_totals()
    account_cb.focus_set()

def add_balancing_line():
    if not entries:
        voucher_hint.config(text="Add at least one line first.")
        return
    row = fetch_one("SELECT id FROM accounts WHERE name=?", (account_cb.get(),))
    if not row:
        voucher_hint.config(text="Select an account for the balancing line.")
        return
    total_debit = round(sum(round(e[2], 2) for e in entries), 2)
    total_credit = round(sum(round(e[3], 2) for e in entries), 2)
    diff = round(total_debit - total_credit, 2)
    if diff == 0:
        voucher_hint.config(text="Voucher is already balanced.")
        return
    d = 0.0
    c = 0.0
    if diff > 0:
        c = diff
    else:
        d = abs(diff)
    acc_id = row[0]
    entries.append((acc_id, account_cb.get(), d, c))
    insert_tree_row(voucher_tree, (account_cb.get(), format_amount(d), format_amount(c)), len(entries) - 1)
    update_voucher_totals()
    voucher_hint.config(text="Balancing line added.")

def save_voucher():
    if not entries:
        voucher_hint.config(text="Add at least one line before saving.")
        return
    total_debit = round(sum(round(e[2], 2) for e in entries), 2)
    total_credit = round(sum(round(e[3], 2) for e in entries), 2)
    if total_debit != total_credit:
        voucher_hint.config(text="Total Debit must equal Total Credit.")
        messagebox.showerror(
            "Unbalanced Voucher",
            f"Total Debit ({format_amount(total_debit)}) does not equal Total Credit ({format_amount(total_credit)}).",
        )
        return
    if not is_valid_date(date_entry.get().strip()):
        voucher_hint.config(text="Date must be in YYYY-MM-DD format.")
        return
    try:
        backup_database("pre_save")
        with db.conn:
            if current_voucher_id is None:
                db.cur.execute(
                    "INSERT INTO vouchers (date, description, posted) VALUES (?, ?, 0)",
                    (date_entry.get().strip(), desc_entry.get().strip()),
                )
                vid = db.cur.lastrowid
            else:
                vid = current_voucher_id
                db.cur.execute(
                    "UPDATE vouchers SET date=?, description=?, posted=0 WHERE id=?",
                    (date_entry.get().strip(), desc_entry.get().strip(), vid),
                )
                db.cur.execute("DELETE FROM transactions WHERE voucher_id=?", (vid,))
            for e in entries:
                d = round(e[2], 2)
                c = round(e[3], 2)
                db.cur.execute(
                    "INSERT INTO transactions (voucher_id, account_id, debit, credit) VALUES (?, ?, ?, ?)",
                    (vid, e[0], d, c),
                )
            db.cur.execute("UPDATE vouchers SET posted=1 WHERE id=?", (vid,))
    except sqlite3.Error as err:
        logging.exception("Save voucher failed")
        voucher_hint.config(text=f"Failed to save voucher: {err}")
        return
    set_status("Voucher saved")
    voucher_hint.config(text="Voucher saved successfully.")
    refresh_dashboard()
    refresh_voucher_history()
    clear_voucher_form()

ttk.Button(form_voucher, text="Add Line", command=add_line).grid(row=2, column=3, padx=(6, 0))
top_save_btn = ttk.Button(form_voucher, text="Save Voucher", command=save_voucher, style="Primary.TButton")
top_save_btn.grid(row=0, column=3, padx=(6, 0))
voucher_actions = ttk.Frame(frame_voucher)
voucher_actions.pack(anchor="w", pady=10)
ttk.Button(voucher_actions, text="Remove Selected Line", command=remove_selected_line).grid(row=0, column=0, padx=(0, 8))
ttk.Button(voucher_actions, text="Add Balancing Line", command=add_balancing_line).grid(row=0, column=1, padx=(0, 8))
save_btn = ttk.Button(voucher_actions, text="Save Voucher", command=save_voucher, style="Primary.TButton")
save_btn.grid(row=0, column=2, padx=(0, 8))
ttk.Button(voucher_actions, text="New Voucher", command=clear_voucher_form).grid(row=0, column=3, padx=(0, 8))

# ================= REPORTS =================
frame_reports = ttk.Frame(content_area)
frames["Reports"] = frame_reports
ttk.Label(frame_reports, text="Financial Reports", style="Header.TLabel").pack(anchor="w")
ttk.Label(frame_reports, text="Quick insights and statements", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 12))
current_report_title = tk.StringVar(value="Report")

# Dashboard cards
card_frame = ttk.Frame(frame_reports)
card_frame.pack(fill="x", pady=10)

cards = {}
for i, text in enumerate(["Total Assets", "Total Liabilities", "Net Profit"]):
    f = ttk.Frame(card_frame, style="Card.TFrame", padding=15)
    f.grid(row=0, column=i, padx=10, sticky="nsew")
    ttk.Label(f, text=text, style="CardTitle.TLabel").pack(anchor="w")
    lbl = ttk.Label(f, text="0.00", style="CardValue.TLabel")
    lbl.pack()
    cards[text] = lbl

for idx in range(3):
    card_frame.columnconfigure(idx, weight=1)

ttk.Separator(frame_reports, orient="horizontal").pack(fill="x", pady=8)

# Date filter
filter_frame = ttk.Frame(frame_reports)
filter_frame.pack(fill="x", pady=8)
ttk.Label(filter_frame, text="From:").pack(side="left")
date_from = ttk.Entry(filter_frame, width=12)
date_from.pack(side="left", padx=5)
date_from.insert(0, "2000-01-01")
ttk.Label(filter_frame, text="To:").pack(side="left")
date_to = ttk.Entry(filter_frame, width=12)
date_to.pack(side="left", padx=5)
date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
ttk.Button(filter_frame, text="Today", command=lambda: date_to.delete(0, tk.END) or date_to.insert(0, datetime.now().strftime("%Y-%m-%d"))).pack(side="left", padx=6)
ttk.Label(filter_frame, text="Account:").pack(side="left", padx=(12, 4))
report_account_cb = ttk.Combobox(filter_frame, state="readonly", width=28)
report_account_cb.pack(side="left")
ttk.Label(filter_frame, text="Cash Accts:").pack(side="left", padx=(12, 4))
cash_accounts_entry = ttk.Entry(filter_frame, width=28)
cash_accounts_entry.pack(side="left")
ttk.Button(filter_frame, text="Clear Filters", command=lambda: (date_from.delete(0, tk.END), date_from.insert(0, "2000-01-01"), date_to.delete(0, tk.END), date_to.insert(0, datetime.now().strftime("%Y-%m-%d")), report_account_cb.set(""), cash_accounts_entry.delete(0, tk.END))).pack(side="left", padx=6)

def set_report_view(columns, headings, numeric_cols=None):
    numeric_cols = set(numeric_cols or [])
    report_tree["columns"] = columns
    for col in columns:
        report_tree.heading(col, text="")
        report_tree.column(col, anchor="w")
    for col, hd in zip(columns, headings):
        anchor = "e" if col in numeric_cols else "w"
        report_tree.heading(col, text=hd, anchor=anchor)
        report_tree.column(col, anchor=anchor)

def get_report_dates():
    start = date_from.get().strip()
    end = date_to.get().strip()
    if not is_valid_date(start) or not is_valid_date(end):
        messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format.")
        return None
    if start > end:
        messagebox.showerror("Error", "From date must be before To date.")
        return None
    return start, end

def refresh_dashboard():
    assets = fetch_one("""
        SELECT SUM(t.debit - t.credit) FROM transactions t
        JOIN accounts a ON t.account_id=a.id WHERE a.type='Asset'
    """)[0] or 0

    liabilities = fetch_one("""
        SELECT SUM(t.credit - t.debit) FROM transactions t
        JOIN accounts a ON t.account_id=a.id WHERE a.type='Liability'
    """)[0] or 0

    income = fetch_one("""
        SELECT SUM(t.credit - t.debit) FROM transactions t
        JOIN accounts a ON t.account_id=a.id WHERE a.type='Income'
    """)[0] or 0

    expense = fetch_one("""
        SELECT SUM(t.debit - t.credit) FROM transactions t
        JOIN accounts a ON t.account_id=a.id WHERE a.type='Expense'
    """)[0] or 0

    animate_number_label(cards["Total Assets"], assets)
    animate_number_label(cards["Total Liabilities"], liabilities)
    animate_number_label(cards["Net Profit"], income - expense)

def generate_trial_balance():
    dates = get_report_dates()
    if not dates:
        return
    start, end = dates
    current_report_title.set("Trial Balance")
    set_report_view(["Account", "Debit", "Credit"], ["Account", "Debit", "Credit"], numeric_cols=["Debit", "Credit"])
    rows = fetch_all("""
        SELECT a.name, SUM(t.debit), SUM(t.credit)
        FROM transactions t JOIN accounts a ON t.account_id = a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE v.date BETWEEN ? AND ?
        GROUP BY a.name
        ORDER BY a.name
    """, (start, end))
    table_rows = [(r[0], format_amount(r[1] or 0), format_amount(r[2] or 0)) for r in rows]
    animate_tree_rows(report_tree, table_rows, delay_ms=14)
    set_status("Trial Balance generated")

def generate_pl():
    dates = get_report_dates()
    if not dates:
        return
    start, end = dates
    current_report_title.set("Profit & Loss")
    set_report_view(["Account", "Debit", "Credit"], ["Account", "Debit", "Credit"], numeric_cols=["Debit", "Credit"])
    income = fetch_all("""
        SELECT a.name, SUM(t.credit - t.debit)
        FROM transactions t JOIN accounts a ON t.account_id=a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE a.type='Income' AND v.date BETWEEN ? AND ?
        GROUP BY a.name
    """, (start, end))
    expense = fetch_all("""
        SELECT a.name, SUM(t.debit - t.credit)
        FROM transactions t JOIN accounts a ON t.account_id=a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE a.type='Expense' AND v.date BETWEEN ? AND ?
        GROUP BY a.name
    """, (start, end))
    total_income = sum([r[1] or 0 for r in income])
    total_expense = sum([r[1] or 0 for r in expense])
    table_rows = []
    for r in income:
        table_rows.append((r[0], "0.00", format_amount(r[1] or 0)))
    for r in expense:
        table_rows.append((r[0], format_amount(r[1] or 0), "0.00"))
    net = total_income - total_expense
    if net >= 0:
        table_rows.append(("Net Profit", "0.00", format_amount(net)))
    else:
        table_rows.append(("Net Loss", format_amount(abs(net)), "0.00"))
    animate_tree_rows(report_tree, table_rows, delay_ms=14)
    set_status("Profit & Loss generated")

def generate_bs():
    dates = get_report_dates()
    if not dates:
        return
    _, end = dates
    current_report_title.set("Balance Sheet")
    set_report_view(["Account", "Debit", "Credit"], ["Account", "Debit", "Credit"], numeric_cols=["Debit", "Credit"])
    assets = fetch_all("""
        SELECT a.name, SUM(t.debit - t.credit)
        FROM transactions t JOIN accounts a ON t.account_id=a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE a.type='Asset' AND v.date <= ?
        GROUP BY a.name
    """, (end,))
    liabilities = fetch_all("""
        SELECT a.name, SUM(t.credit - t.debit)
        FROM transactions t JOIN accounts a ON t.account_id=a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE a.type='Liability' AND v.date <= ?
        GROUP BY a.name
    """, (end,))
    table_rows = []
    for r in assets:
        table_rows.append((r[0], format_amount(r[1] or 0), "0.00"))
    for r in liabilities:
        table_rows.append((r[0], "0.00", format_amount(r[1] or 0)))
    animate_tree_rows(report_tree, table_rows, delay_ms=14)
    set_status("Balance Sheet generated")

def generate_general_ledger():
    dates = get_report_dates()
    if not dates:
        return
    start, end = dates
    current_report_title.set("General Ledger")
    account_name = report_account_cb.get().strip()
    if not account_name:
        messagebox.showerror("Error", "Select an account for General Ledger.")
        return
    row = fetch_one("SELECT id, type FROM accounts WHERE name=?", (account_name,))
    if not row:
        messagebox.showerror("Error", "Selected account not found.")
        return
    account_id, account_type = row
    rows = fetch_all("""
        SELECT v.date, v.description, t.debit, t.credit
        FROM transactions t
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE t.account_id = ? AND v.date BETWEEN ? AND ?
        ORDER BY v.date, v.id, t.id
    """, (account_id, start, end))
    set_report_view(
        ["Date", "Description", "Debit", "Credit", "Balance"],
        ["Date", "Description", "Debit", "Credit", "Balance"],
        numeric_cols=["Debit", "Credit", "Balance"],
    )
    opening = fetch_one("""
        SELECT
            CASE
                WHEN ? IN ('Asset', 'Expense') THEN COALESCE(SUM(t.debit - t.credit), 0)
                ELSE COALESCE(SUM(t.credit - t.debit), 0)
            END
        FROM transactions t
        JOIN vouchers v ON t.voucher_id = v.id
        WHERE t.account_id = ? AND v.date < ?
    """, (account_type, account_id, start))[0] or 0.0
    balance = round(opening, 2)
    table_rows = []
    for r in rows:
        debit = r[2] or 0
        credit = r[3] or 0
        delta = (debit - credit) if account_type in ("Asset", "Expense") else (credit - debit)
        balance += delta
        table_rows.append((r[0], r[1] or "", format_amount(debit), format_amount(credit), format_amount(balance)))
    animate_tree_rows(report_tree, table_rows, delay_ms=12)
    set_status("General Ledger generated")

def generate_cash_flow():
    dates = get_report_dates()
    if not dates:
        return
    start, end = dates
    current_report_title.set("Cash Flow")
    raw_cash = cash_accounts_entry.get().strip()
    cash_names = [n.strip() for n in raw_cash.split(",") if n.strip()]
    if not cash_names:
        cash_names = [
            r[0] for r in fetch_all(
                "SELECT name FROM accounts WHERE LOWER(name) LIKE '%cash%' OR LOWER(name) LIKE '%bank%'"
            )
        ]
    if not cash_names:
        messagebox.showerror("Error", "No cash accounts found. Enter names in Cash Accts.")
        return
    set_report_view(
        ["Account", "Inflow", "Outflow"],
        ["Account", "Inflow", "Outflow"],
        numeric_cols=["Inflow", "Outflow"],
    )
    placeholders = ",".join(["?"] * len(cash_names))
    rows = fetch_all(f"""
        SELECT a.name, SUM(t.debit), SUM(t.credit)
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        JOIN vouchers v ON t.voucher_id=v.id
        WHERE a.name IN ({placeholders})
          AND v.date BETWEEN ? AND ?
        GROUP BY a.name
        ORDER BY a.name
    """, (*cash_names, start, end))
    total_in = 0
    total_out = 0
    table_rows = []
    for r in rows:
        inflow = r[1] or 0
        outflow = r[2] or 0
        total_in += inflow
        total_out += outflow
        table_rows.append((r[0], format_amount(inflow), format_amount(outflow)))
    table_rows.append(("Net Cash", format_amount(total_in), format_amount(total_out)))
    animate_tree_rows(report_tree, table_rows, delay_ms=14)
    set_status("Cash Flow generated")

def export_csv():
    path = filedialog.asksaveasfilename(defaultextension=".csv")
    if not path:
        return
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(list(report_tree["columns"]))
        for row in report_tree.get_children():
            writer.writerow(report_tree.item(row)["values"])
    set_status("Exported to Excel (CSV)")

def get_report_table_data():
    columns = list(report_tree["columns"])
    if not columns:
        return None, None, None
    headings = [report_tree.heading(col)["text"] for col in columns]
    rows = [report_tree.item(row)["values"] for row in report_tree.get_children()]
    return columns, headings, rows

def build_report_pdf(path):
    _, headings, rows = get_report_table_data()
    if not headings:
        messagebox.showerror("Error", "No report data to export.")
        return False
    data = [headings] + rows
    doc = SimpleDocTemplate(path, pagesize=landscape(LETTER), title=current_report_title.get())
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(current_report_title.get(), styles["Title"]))
    dates = get_report_dates()
    if dates:
        elements.append(Paragraph(f"From {dates[0]} To {dates[1]}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b1220")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    doc.build(elements)
    return True

def export_pdf():
    path = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not path:
        return
    try:
        if build_report_pdf(path):
            set_status("PDF exported")
    except Exception:
        logging.exception("PDF export failed")
        messagebox.showerror("Error", "Failed to export PDF. See rias.log.")

def print_report():
    try:
        tmp_path = os.path.join(tempfile.gettempdir(), "rias_report_print.pdf")
        if not build_report_pdf(tmp_path):
            return
        try:
            os.startfile(tmp_path, "print")
            set_status("Print job sent")
        except Exception:
            os.startfile(tmp_path, "open")
            set_status("Opened PDF for printing")
    except Exception:
        logging.exception("Print failed")
        messagebox.showerror("Error", "Failed to print report. See rias.log.")

actions = ttk.Frame(frame_reports)
actions.pack(side="bottom", fill="x", pady=10)
for col in range(5):
    actions.grid_columnconfigure(col, weight=1)
ttk.Button(actions, text="Trial Balance", command=generate_trial_balance).grid(row=0, column=0, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Profit & Loss", command=generate_pl).grid(row=0, column=1, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Balance Sheet", command=generate_bs).grid(row=0, column=2, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="General Ledger", command=generate_general_ledger).grid(row=0, column=3, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Cash Flow", command=generate_cash_flow).grid(row=0, column=4, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Export CSV", command=export_csv).grid(row=1, column=0, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Refresh Dashboard", command=refresh_dashboard, style="Primary.TButton").grid(row=1, column=1, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Export PDF", command=export_pdf).grid(row=1, column=2, padx=5, pady=4, sticky="ew")
ttk.Button(actions, text="Print", command=print_report).grid(row=1, column=3, padx=5, pady=4, sticky="ew")

# Reports Treeview
report_tree = create_treeview(
    frame_reports,
    ["Account", "Debit", "Credit"],
    ["Account", "Debit", "Credit"],
    height=15,
    numeric_cols=["Debit", "Credit"],
    pack=False,
)
report_tree.pack(fill="both", expand=True, pady=12)

# ================= VOUCHER HISTORY =================
frame_history = ttk.Frame(content_area)
frames["Voucher History"] = frame_history
ttk.Label(frame_history, text="Voucher History", style="Header.TLabel").pack(anchor="w")
ttk.Label(frame_history, text="Review saved vouchers and their lines", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 12))

history_filter = ttk.Frame(frame_history)
history_filter.pack(fill="x", pady=6)
ttk.Label(history_filter, text="From:").pack(side="left")
hist_from = ttk.Entry(history_filter, width=12)
hist_from.pack(side="left", padx=5)
hist_from.insert(0, "2000-01-01")
ttk.Label(history_filter, text="To:").pack(side="left")
hist_to = ttk.Entry(history_filter, width=12)
hist_to.pack(side="left", padx=5)
hist_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
ttk.Button(history_filter, text="Today", command=lambda: hist_to.delete(0, tk.END) or hist_to.insert(0, datetime.now().strftime("%Y-%m-%d"))).pack(side="left", padx=6)

ttk.Label(history_filter, text="Search").pack(side="left", padx=(12, 4))
hist_search = ttk.Entry(history_filter, width=24)
hist_search.pack(side="left")

history_actions = ttk.Frame(frame_history)
history_actions.pack(fill="x", pady=6)
history_unbalanced_only = False

vouchers_tree = create_treeview(
    frame_history,
    ["ID", "Date", "Description", "Status", "Debit", "Credit"],
    ["Voucher ID", "Date", "Description", "Status", "Total Debit", "Total Credit"],
    height=10,
    numeric_cols=["Debit", "Credit"],
)

ttk.Label(frame_history, text="Voucher Lines", style="SubHeader.TLabel").pack(anchor="w", pady=(8, 4))
lines_tree = create_treeview(
    frame_history,
    ["Account", "Debit", "Credit"],
    ["Account", "Debit", "Credit"],
    height=10,
    numeric_cols=["Debit", "Credit"],
)

def refresh_voucher_history():
    lines_tree.delete(*lines_tree.get_children())
    if not is_valid_date(hist_from.get().strip()) or not is_valid_date(hist_to.get().strip()):
        messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format.")
        return
    search_text = hist_search.get().strip()
    having_clause = ""
    if history_unbalanced_only:
        having_clause = "HAVING ROUND(SUM(t.debit), 2) <> ROUND(SUM(t.credit), 2)"
    rows = fetch_all(
        f"""
        SELECT v.id, v.date, v.description, v.posted, SUM(t.debit) AS total_debit, SUM(t.credit) AS total_credit
        FROM vouchers v
        JOIN transactions t ON v.id = t.voucher_id
        WHERE v.date BETWEEN ? AND ?
          AND (v.description LIKE ? OR v.id LIKE ?)
        GROUP BY v.id, v.date, v.description, v.posted
        {having_clause}
        ORDER BY v.date DESC, v.id DESC
        """,
        (hist_from.get(), hist_to.get(), f"%{search_text}%", f"%{search_text}%"),
    )
    table_rows = []
    for r in rows:
        total_debit = round(r[4] or 0, 2)
        total_credit = round(r[5] or 0, 2)
        status = "Posted" if r[3] == 1 else "Draft"
        if total_debit != total_credit:
            status = "Unbalanced"
        table_rows.append((r[0], r[1], r[2] or "", status, format_amount(total_debit), format_amount(total_credit)))
    animate_tree_rows(vouchers_tree, table_rows, delay_ms=10)
    set_status("Voucher history refreshed")

def show_unbalanced_vouchers():
    global history_unbalanced_only
    history_unbalanced_only = True
    show_frame("Voucher History", frame_history)
    hist_from.delete(0, tk.END)
    hist_from.insert(0, "2000-01-01")
    hist_to.delete(0, tk.END)
    hist_to.insert(0, datetime.now().strftime("%Y-%m-%d"))
    refresh_voucher_history()
    count = len(vouchers_tree.get_children())
    if count == 0:
        messagebox.showinfo("Unbalanced Vouchers", "No unbalanced vouchers found.")
    else:
        messagebox.showwarning("Unbalanced Vouchers", f"Found {count} unbalanced voucher(s). Open one to repair.")

def show_all_vouchers():
    global history_unbalanced_only
    history_unbalanced_only = False
    refresh_voucher_history()

def on_voucher_select(event):
    selection = vouchers_tree.selection()
    if not selection:
        return
    values = vouchers_tree.item(selection[0], "values")
    if not values:
        return
    voucher_id = values[0]
    lines_tree.delete(*lines_tree.get_children())
    rows = fetch_all(
        """
        SELECT a.name, t.debit, t.credit
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.voucher_id = ?
        """,
        (voucher_id,),
    )
    for i, r in enumerate(rows):
        insert_tree_row(lines_tree, (r[0], format_amount(r[1] or 0), format_amount(r[2] or 0)), i)

vouchers_tree.bind("<<TreeviewSelect>>", on_voucher_select)
vouchers_tree.bind("<Double-1>", lambda e: load_voucher_for_edit())
vouchers_tree.bind("<Delete>", lambda e: delete_selected_voucher())
def load_voucher_for_edit():
    global current_voucher_id
    selection = vouchers_tree.selection()
    if not selection:
        set_status("Select a voucher to edit")
        return
    values = vouchers_tree.item(selection[0], "values")
    if not values:
        return
    voucher_id = values[0]
    row = fetch_one("SELECT date, description FROM vouchers WHERE id=?", (voucher_id,))
    if not row:
        set_status("Voucher not found")
        return
    date_entry.delete(0, tk.END)
    date_entry.insert(0, row[0])
    desc_entry.delete(0, tk.END)
    desc_entry.insert(0, row[1] or "")
    entries.clear()
    tx_rows = fetch_all("""
        SELECT a.id, a.name, t.debit, t.credit
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        WHERE t.voucher_id = ?
        ORDER BY t.id
    """, (voucher_id,))
    for r in tx_rows:
        entries.append((r[0], r[1], r[2] or 0, r[3] or 0))
    rebuild_voucher_tree()
    update_voucher_totals()
    current_voucher_id = voucher_id
    set_voucher_mode(True)
    show_frame("Voucher Entry", frame_voucher)
    set_status(f"Editing voucher {voucher_id}")

def delete_selected_voucher():
    selection = vouchers_tree.selection()
    if not selection:
        set_status("Select a voucher to delete")
        return
    values = vouchers_tree.item(selection[0], "values")
    if not values:
        return
    voucher_id = values[0]
    if not messagebox.askyesno("Confirm", f"Delete voucher {voucher_id}?"):
        return
    try:
        with db.conn:
            db.cur.execute("UPDATE vouchers SET posted=0 WHERE id=?", (voucher_id,))
            db.cur.execute("DELETE FROM vouchers WHERE id=?", (voucher_id,))
    except sqlite3.Error:
        set_status("Failed to delete voucher")
        return
    refresh_voucher_history()
    refresh_dashboard()
    set_status("Voucher deleted")

ttk.Button(history_actions, text="Refresh", command=refresh_voucher_history).pack(side="left", padx=5)
ttk.Button(history_actions, text="Edit Voucher", command=load_voucher_for_edit).pack(side="left", padx=5)
ttk.Button(history_actions, text="Delete Voucher", command=delete_selected_voucher).pack(side="left", padx=5)
ttk.Button(history_actions, text="Show Unbalanced", command=show_unbalanced_vouchers).pack(side="left", padx=5)
ttk.Button(history_actions, text="Show All", command=show_all_vouchers).pack(side="left", padx=5)
ttk.Button(history_actions, text="Clear Search", command=lambda: (hist_search.delete(0, tk.END), refresh_voucher_history())).pack(side="left", padx=5)
hist_search.bind("<KeyRelease>", lambda e: refresh_voucher_history())

# ================= SETTINGS =================
frame_settings = ttk.Frame(content_area)
frames["Settings"] = frame_settings
ttk.Label(frame_settings, text="Settings", style="Header.TLabel").pack(anchor="w")
ttk.Label(frame_settings, text="Customize visual appearance", style="SubHeader.TLabel").pack(anchor="w", pady=(2, 12))

settings_form = ttk.Frame(frame_settings)
settings_form.pack(anchor="w", pady=8)
ttk.Label(settings_form, text="Theme").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
theme_var = tk.StringVar(value=CURRENT_THEME)
theme_cb = ttk.Combobox(settings_form, values=list(THEMES.keys()), textvariable=theme_var, state="readonly", width=28)
theme_cb.grid(row=0, column=1, sticky="w", pady=4)

def apply_selected_theme():
    apply_theme(theme_var.get())
    set_status(f"Theme changed to {theme_var.get()}")

ttk.Button(settings_form, text="Apply Theme", command=apply_selected_theme, style="Primary.TButton").grid(row=0, column=2, padx=(10, 0), pady=4)
theme_cb.bind("<<ComboboxSelected>>", lambda e: apply_selected_theme())

# ================= NAVIGATION =================
ttk.Label(sidebar, text="RIAS", style="Sidebar.TLabel").pack(anchor="w")
sidebar_subtitle = ttk.Label(sidebar, text="Accounting Suite", background=SIDEBAR_BG, foreground=MUTED, font=("Segoe UI", 9))
sidebar_subtitle.pack(anchor="w", pady=(2, 18))
nav_button("Accounts", frame_accounts)
nav_button("Voucher Entry", frame_voucher)
nav_button("Reports", frame_reports)
nav_button("Voucher History", frame_history)
nav_button("Settings", frame_settings)

# ================= DROPDOWNS =================
def refresh_dropdowns():
    names = [r[0] for r in fetch_all("SELECT name FROM accounts")]
    current_acc = account_cb.get()
    current_report = report_account_cb.get()
    account_cb["values"] = names
    report_account_cb["values"] = names
    if current_acc in names:
        account_cb.set(current_acc)
    if current_report in names:
        report_account_cb.set(current_report)

refresh_accounts()
refresh_dashboard()
refresh_voucher_history()
show_frame("Accounts", frame_accounts)
backup_database("startup")
check_db_integrity()
check_unbalanced_vouchers()

def focus_search():
    if current_frame_name == "Accounts":
        search_acc.focus_set()
    elif current_frame_name == "Voucher History":
        hist_search.focus_set()

def on_ctrl_s(event=None):
    if current_frame_name == "Voucher Entry":
        save_voucher()
        return "break"

def on_ctrl_l(event=None):
    if current_frame_name == "Voucher Entry":
        add_line()
        return "break"

def on_ctrl_n(event=None):
    if current_frame_name == "Voucher Entry":
        clear_voucher_form()
        return "break"

def on_ctrl_f(event=None):
    focus_search()
    return "break"

def on_enter(event=None):
    focus = root.focus_get()
    if current_frame_name == "Accounts":
        if focus in (acc_name, acc_type):
            add_account()
            return "break"
        if focus == search_acc:
            refresh_accounts(search_acc.get().strip())
            return "break"
    if current_frame_name == "Voucher Entry":
        if focus in (account_cb, debit_entry, credit_entry):
            add_line()
            return "break"
    if current_frame_name == "Reports":
        if focus in (date_from, date_to):
            generate_trial_balance()
            return "break"
    if current_frame_name == "Voucher History":
        if focus == hist_search:
            refresh_voucher_history()
            return "break"

def run_if_frame(frame_name, action):
    if current_frame_name == frame_name:
        action()
        return "break"

root.bind("<Control-s>", on_ctrl_s)
root.bind("<Control-l>", on_ctrl_l)
root.bind("<Control-f>", on_ctrl_f)
root.bind("<Control-n>", on_ctrl_n)
root.bind("<Return>", on_enter)
root.bind("<Control-1>", lambda e: (show_frame("Accounts", frame_accounts), "break"))
root.bind("<Control-2>", lambda e: (show_frame("Voucher Entry", frame_voucher), "break"))
root.bind("<Control-3>", lambda e: (show_frame("Reports", frame_reports), "break"))
root.bind("<Control-4>", lambda e: (show_frame("Voucher History", frame_history), "break"))
root.bind("<Control-5>", lambda e: (show_frame("Settings", frame_settings), "break"))
root.bind("<Control-u>", lambda e: run_if_frame("Accounts", update_account))
root.bind("<Control-d>", lambda e: run_if_frame("Accounts", delete_account))
root.bind("<Control-k>", lambda e: run_if_frame("Accounts", clear_account_form))
root.bind("<Control-r>", lambda e: run_if_frame("Reports", refresh_dashboard) or run_if_frame("Voucher History", refresh_voucher_history))
root.bind("<Control-e>", lambda e: run_if_frame("Reports", export_csv) or run_if_frame("Voucher History", load_voucher_for_edit))
root.bind("<Control-p>", lambda e: run_if_frame("Reports", print_report))
root.bind("<Control-Shift-E>", lambda e: run_if_frame("Reports", export_pdf))
root.bind("<Alt-t>", lambda e: run_if_frame("Reports", generate_trial_balance))
root.bind("<Alt-p>", lambda e: run_if_frame("Reports", generate_pl))
root.bind("<Alt-b>", lambda e: run_if_frame("Reports", generate_bs))
root.bind("<Alt-g>", lambda e: run_if_frame("Reports", generate_general_ledger))
root.bind("<Alt-c>", lambda e: run_if_frame("Reports", generate_cash_flow))

animate_window_fade_in()
root.mainloop()
db.close()
