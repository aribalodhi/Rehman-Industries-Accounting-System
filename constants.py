"""
Constants and configuration for the RIAS (Rehman Industries Accounting System).
Centralizes all magic numbers, strings, fonts, themes, and paths.
"""

import os
import sys
from typing import Dict, Final

# ============================================================================
# PATHS & DIRECTORIES
# ============================================================================
APP_DIR: Final[str] = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
DATA_DIR: Final[str] = os.path.join(os.path.expanduser("~"), "RIAS_Data")
DB_PATH: Final[str] = os.path.join(DATA_DIR, "rehman_industries.db")
SEED_DIR: Final[str] = getattr(sys, "_MEIPASS", APP_DIR)
SEED_DB_PATH: Final[str] = os.path.join(SEED_DIR, "rehman_industries.db")
LOG_FILE: Final[str] = os.path.join(DATA_DIR, "rias.log")
BACKUP_DIR: Final[str] = os.path.join(DATA_DIR, "db_backups")
SETTINGS_FILE: Final[str] = os.path.join(DATA_DIR, "settings.json")

# ============================================================================
# APPLICATION METADATA
# ============================================================================
APP_TITLE: Final[str] = "Rehman Industries Accounting System (RIAS)"
APP_NAME: Final[str] = "RIAS"
APP_TAGLINE: Final[str] = "Professional Ledger Workspace"
DEFAULT_WINDOW_WIDTH: Final[int] = 1400
DEFAULT_WINDOW_HEIGHT: Final[int] = 850
MIN_WINDOW_WIDTH: Final[int] = 1180
MIN_WINDOW_HEIGHT: Final[int] = 720

# ============================================================================
# ACCOUNT TYPES & DATABASE CONSTRAINTS
# ============================================================================
ACCOUNT_TYPES: Final[tuple] = ("Asset", "Liability", "Income", "Expense")
VALID_ACCOUNT_TYPES_SQL: Final[str] = ", ".join(f"'{t}'" for t in ACCOUNT_TYPES)
MIN_TRANSACTION_LINES: Final[int] = 2
FLOAT_PRECISION: Final[int] = 2

# ============================================================================
# DATE & TIME
# ============================================================================
DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
HEADER_DATE_FORMAT: Final[str] = "%A, %B %d, %Y"
DEFAULT_START_DATE: Final[str] = "2000-01-01"

# ============================================================================
# FONTS
# ============================================================================
FONT_BODY: Final[tuple] = ("Segoe UI", 10)
FONT_SMALL: Final[tuple] = ("Segoe UI", 9)
FONT_HEADER: Final[tuple] = ("Segoe UI Semibold", 20)
FONT_SUBHEADER: Final[tuple] = ("Segoe UI Semibold", 10)
FONT_CARD_VALUE: Final[tuple] = ("Segoe UI Semibold", 16)
FONT_BRAND_MAIN: Final[tuple] = ("Segoe UI Semibold", 22)
FONT_BRAND_CHIP: Final[tuple] = ("Segoe UI Semibold", 9)
FONT_SIDEBAR: Final[tuple] = ("Segoe UI Semibold", 12)

# ============================================================================
# THEMES
# ============================================================================
THEMES: Final[Dict[str, Dict[str, str]]] = {
    "Professional Dark": {
        "PRIMARY": "#e2e8f0",
        "PRIMARY_SOFT": "#475569",
        "ACCENT": "#3b82f6",
        "ACCENT_HOVER": "#2563eb",
        "ACCENT_SOFT": "#1e3a8a",
        "SURFACE": "#0f172a",
        "SURFACE_ALT": "#111827",
        "SURFACE_SOFT": "#1f2937",
        "MUTED": "#94a3b8",
        "LINE": "#334155",
        "SIDEBAR_BG": "#0b1220",
        "HEADING_BG": "#1e293b",
        "ROW_EVEN": "#0b1220",
        "GOOD": "#34d399",
        "WARN": "#fbbf24",
        "BAD": "#f87171",
    },
    "Slate Light": {
        "PRIMARY": "#0f172a",
        "PRIMARY_SOFT": "#334155",
        "ACCENT": "#2563eb",
        "ACCENT_HOVER": "#1d4ed8",
        "ACCENT_SOFT": "#dbeafe",
        "SURFACE": "#eef2f7",
        "SURFACE_ALT": "#ffffff",
        "SURFACE_SOFT": "#e2e8f0",
        "MUTED": "#64748b",
        "LINE": "#cbd5e1",
        "SIDEBAR_BG": "#0f172a",
        "HEADING_BG": "#1e293b",
        "ROW_EVEN": "#f8fafc",
        "GOOD": "#059669",
        "WARN": "#b45309",
        "BAD": "#b91c1c",
    },
}

DEFAULT_THEME: Final[str] = "Slate Light"

# ============================================================================
# DASHBOARD CARDS
# ============================================================================
DASHBOARD_CARDS: Final[tuple] = ("Total Assets", "Total Liabilities", "Net Profit")

# ============================================================================
# ANIMATION SETTINGS
# ============================================================================
CARD_ANIMATION_DURATION: Final[int] = 360
CARD_ANIMATION_STEPS: Final[int] = 18
TREE_ANIMATION_DELAY_MS: Final[int] = 16
TREE_ANIMATION_THRESHOLD: Final[int] = 180
WINDOW_FADE_IN_DURATION: Final[int] = 280
WINDOW_FADE_IN_STEPS: Final[int] = 14
STATUS_MESSAGE_DURATION: Final[int] = 5000
MIN_FRAME_DELAY: Final[int] = 12

# ============================================================================
# UI SECTIONS
# ============================================================================
SIDEBAR_WIDTH: Final[int] = 250
SIDEBAR_PADDING: Final[int] = 20
CONTENT_PADDING: Final[int] = 24
HEADER_PADDING: Final[tuple] = (24, 18)
FORM_PADDING: Final[int] = 10
BUTTON_PADDING: Final[tuple] = (10, 6)
PRIMARY_BUTTON_PADDING: Final[tuple] = (12, 8)
NAV_BUTTON_PADDING: Final[tuple] = (12, 10)
CARD_PADDING: Final[int] = 15

# ============================================================================
# TREEVIEW SETTINGS
# ============================================================================
DEFAULT_TREEVIEW_HEIGHT: Final[int] = 15
TREEVIEW_ROW_HEIGHT: Final[int] = 28

# ============================================================================
# BACKUP TAGS
# ============================================================================
BACKUP_TAG_STARTUP: Final[str] = "startup"
BACKUP_TAG_PRE_SAVE: Final[str] = "pre_save"
BACKUP_TAG_MANUAL: Final[str] = "manual"

# ============================================================================
# MESSAGES & LABELS
# ============================================================================
MSG_READY: Final[str] = "Ready"
MSG_ACCOUNT_ADDED: Final[str] = "Account added"
MSG_ACCOUNT_UPDATED: Final[str] = "Account updated"
MSG_ACCOUNT_DELETED: Final[str] = "Account deleted"
MSG_FORM_CLEARED: Final[str] = "Form cleared"
MSG_DB_INTEGRITY_OK: Final[str] = "Database integrity OK"
MSG_VOUCHER_SAVED: Final[str] = "Voucher saved"
MSG_LINE_ADDED: Final[str] = "Line added."
MSG_LINE_REMOVED: Final[str] = "Line removed."
MSG_NEW_VOUCHER: Final[str] = "New voucher ready"

# Error messages
ERR_INVALID_DATE: Final[str] = "Date must be in YYYY-MM-DD format."
ERR_INVALID_AMOUNT: Final[str] = "Enter valid numbers for Debit/Credit."
ERR_NEGATIVE_AMOUNT: Final[str] = "Debit/Credit must be positive values."
ERR_BOTH_OR_NEITHER: Final[str] = (
    "Enter either debit or credit, not both or none."
)
ERR_INVALID_ACCOUNT: Final[str] = "Select a valid account."
ERR_ACCOUNT_EXISTS: Final[str] = "Account already exists"
ERR_REQUIRED_FIELDS: Final[str] = "All fields required"
ERR_NO_ACCOUNT_SELECTED: Final[str] = "Select an account to"
ERR_ACCOUNT_IN_USE: Final[str] = "Account is used in transactions"
ERR_UNBALANCED_VOUCHER: Final[str] = "Total Debit must equal Total Credit."
ERR_SELECT_ACCOUNT_GL: Final[str] = "Select an account for General Ledger."
ERR_NO_CASH_ACCOUNTS: Final[str] = (
    "No cash accounts found. Enter names in Cash Accts."
)
ERR_DEBIT_CREDIT_MISMATCH: Final[str] = (
    "Debit and credit totals must be equal before posting"
)
ERR_MIN_LINES: Final[str] = "Voucher must contain at least two lines before posting"
ERR_CANNOT_MODIFY_POSTED: Final[str] = "Cannot modify a posted voucher"
