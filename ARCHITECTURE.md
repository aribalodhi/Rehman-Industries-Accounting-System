# RIAS Architecture Overview

## Project Structure

```
RIAS/
│
├── 📄 rehman_accounting.py        Main application
│   ├── UI Layout & Widgets
│   ├── Event Handlers
│   ├── Business Logic
│   └── Report Generation
│
├── 📄 constants.py                Configuration & Constants
│   ├── Paths & Directories
│   ├── UI Constants (fonts, sizes, padding)
│   ├── Themes & Colors
│   ├── Database Schemas
│   └── Message Strings
│
├── 📄 validators.py               Input Validation & Formatting
│   ├── Date Validation
│   ├── Amount Validation
│   ├── Account Validation
│   ├── Data Formatting
│   └── Parsing Utilities
│
├── 📄 database.py                 Database Abstraction Layer
│   ├── Connection Management
│   ├── Schema Initialization
│   ├── Query Helpers
│   ├── Integrity Checking
│   └── Transaction Management
│
├── 📄 settings_manager.py         Settings Persistence
│   ├── JSON Storage
│   ├── Theme Management
│   ├── Preference Caching
│   └── Default Settings
│
├── 📄 requirements.txt            Dependencies
│   ├── reportlab>=3.6.0
│   └── Pillow>=8.0.0
│
├── 📄 README.md                   User Documentation
├── 📄 IMPROVEMENTS.md             Improvement Summary
├── 📄 QUICK_REFERENCE.md          Developer Quick Guide
├── 📄 ARCHITECTURE.md             This File
│
└── 📂 Other files
    ├── RIAS.spec                  PyInstaller Config
    ├── installer.iss              InnoSetup Config
    ├── icon.ico / icon.png        Application Icons
    └── ...
```

---

## Layered Architecture

```
┌─────────────────────────────────────────┐
│         UI Layer (Tkinter)              │
│  • Windows & Dialogs                    │
│  • Widget Management                    │
│  • Event Handling                       │
│  • Theme Application                    │
└─────────────────────────────────────────┘
        ↓              ↓             ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Reports    │ │   Validators │ │   Settings   │
│   Module     │ │   Module     │ │   Manager    │
└──────────────┘ └──────────────┘ └──────────────┘
        ↓              ↓             ↓
┌─────────────────────────────────────────┐
│         Business Logic Layer            │
│  • Voucher Entry Processing             │
│  • Financial Calculations               │
│  • Data Transformation                  │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│        Database Layer (SQLite)          │
│  • Accounts Table                       │
│  • Vouchers Table                       │
│  • Transactions Table                   │
│  • Triggers & Constraints               │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│        Constants Layer                  │
│  • Configuration Values                 │
│  • Message Strings                      │
│  • Theme Definitions                    │
└─────────────────────────────────────────┘
```

---

## Data Flow

### 1. Account Management
```
User Input
    ↓
validators.validate_account_data()
    ↓
db.execute("INSERT/UPDATE/DELETE accounts")
    ↓
Database
    ↓
UI Updated (refresh_accounts())
```

### 2. Voucher Entry
```
User Input (Date, Debit, Credit, Account)
    ↓
validators.validate_debit_credit_pair()
    ↓
Entries Accumulated in Memory
    ↓
validators.validate_date_range()
    ↓
db.execute("INSERT vouchers + transactions")
    ↓
Database (with triggers)
    ↓
UI Updated (refresh_voucher_history())
```

### 3. Report Generation
```
User Selects Report Type + Filters
    ↓
validators.validate_date_range()
    ↓
db.fetch_all() - SQL Query
    ↓
Business Logic - Calculations
    ↓
Report Generation (ReportLab)
    ↓
Display on Screen / Export
```

### 4. Settings Persistence
```
User Changes Theme
    ↓
apply_theme(theme_name)
    ↓
settings_manager.set_theme(theme_name)
    ↓
Save to settings.json
    ↓
On Next Launch:
    settings_manager.get_theme() → Load from JSON
```

---

## Module Responsibilities

### `rehman_accounting.py` - Main Application
**Responsibility:** UI Orchestration & Coordination

```
├── initialize()
│   ├── Create root window
│   ├── Load theme from settings
│   ├── Initialize database
│   └── Setup event bindings
│
├── UI Sections
│   ├── chart_of_accounts()
│   ├── voucher_entry()
│   ├── financial_reports()
│   ├── voucher_history()
│   └── settings()
│
├── Event Handlers
│   ├── on_add_account()
│   ├── on_save_voucher()
│   ├── on_generate_report()
│   └── on_apply_theme()
│
└── Business Logic
    ├── refresh_dashboard()
    ├── generate_trial_balance())
    ├── generate_profit_loss()
    └── export_csv() / export_pdf()
```

### `constants.py` - Configuration
**Responsibility:** Centralized Configuration

- ✅ Paths (DB, backups, logs)
- ✅ UI Dimensions & Spacing
- ✅ Font Definitions
- ✅ Theme Color Palettes
- ✅ Message Strings
- ✅ Animation Parameters
- ✅ Constraint Values (MIN_TRANSACTION_LINES, etc.)

### `validators.py` - Input Validation
**Responsibility:** Data Validation & Formatting

- ✅ Validate dates (YYYY-MM-DD format)
- ✅ Parse and validate amounts
- ✅ Enforce double-entry constraints
- ✅ Validate account data
- ✅ Format amounts for display
- ✅ Parse user input

### `database.py` - Data Persistence
**Responsibility:** Database Operations

- ✅ Connection management
- ✅ Schema initialization
- ✅ Query execution with parameters
- ✅ Transaction management
- ✅ Integrity checking
- ✅ Trigger definitions
- ✅ Foreign key enforcement

### `settings_manager.py` - Configuration State
**Responsibility:** Settings Persistence

- ✅ Load settings from JSON
- ✅ Save settings to JSON
- ✅ Get/Set key-value pairs
- ✅ Manage theme selection
- ✅ Error recovery with defaults

---

## Database Schema

```
accounts
├── id (PRIMARY KEY)
├── name (TEXT, UNIQUE)
└── type (TEXT: Asset|Liability|Income|Expense)

vouchers
├── id (PRIMARY KEY)
├── date (TEXT)
├── description (TEXT)
└── posted (BOOLEAN)

transactions
├── id (PRIMARY KEY)
├── voucher_id (FK → vouchers.id)
├── account_id (FK → accounts.id)
├── debit (REAL, ≥0)
└── credit (REAL, ≥0)
    ↳ Constraint: exactly one of debit/credit > 0

Indexes:
├── idx_tx_voucher (transactions.voucher_id)
├── idx_tx_account (transactions.account_id)
└── idx_voucher_date (vouchers.date)

Triggers:
├── trg_tx_no_insert_posted
├── trg_tx_no_update_posted
├── trg_tx_no_delete_posted
└── trg_voucher_post_balanced
```

---

## Key Design Decisions

### 1. **Modular Architecture**
- Separated concerns across 5 modules
- Each module has single responsibility
- Reduces coupling and improves testability

### 2. **Constants Over Magic Numbers**
- All hardcoded values extracted to `constants.py`
- Easier to maintain and update
- Consistent across application

### 3. **Validators Module**
- Centralized input validation
- Consistent error handling
- Single source of truth for validation rules

### 4. **Database Abstraction**
- `Database` class encapsulates SQLite operations
- Enables schema migration support
- Facilitates future database portability

### 5. **Settings Persistence**
- User preferences saved to JSON
- Automatic defaults on first run
- Theme choice remembered across sessions

### 6. **Type Hints Throughout**
- Improves IDE support
- Catches errors early
- Aids code documentation

---

## Call Flows

### Adding an Account
```
add_account()
├── validate_account_name()
├── validate_account_type()
├── db.fetch_one() [check duplicate]
├── db.execute() [INSERT]
├── refresh_accounts()
├── refresh_dropdowns()
└── set_status(MSG_ACCOUNT_ADDED)
```

### Saving a Voucher
```
save_voucher()
├── Validate entries list
├── Sum debits & credits
├── compare(total_debit, total_credit)
├── validate_date(date)
├── backup_database(BACKUP_TAG_PRE_SAVE)
├── db.conn [BEGIN TRANSACTION]
├── db.execute() [INSERT vouchers]
├── for each entry:
│   └── db.execute() [INSERT transactions]
├── db.conn [COMMIT]
├── refresh_dashboard()
├── refresh_voucher_history()
└── set_status(MSG_VOUCHER_SAVED)
```

### Switching Themes
```
apply_selected_theme()
├── theme_var.get()
├── validate_theme(theme_name)
├── settings_manager.set_theme()
├── apply_theme()
├── style.configure() [all widgets]
├── update_widget_styles()
└── set_status("Theme changed to...")
```

---

## Extension Points

### Add New Validation
```python
# In validators.py
def validate_new_field(value: str) -> bool:
    """Validate new field."""
    return True

# In rehman_accounting.py
if not validate_new_field(user_input):
    messagebox.showerror("Error", "Message")
```

### Add New Report Type
```python
# In rehman_accounting.py
def generate_custom_report():
    """Generate custom report."""
    rows = db.fetch_all("SELECT ...")
    # Process data
    # Display in tree
    set_status("Report generated")

# Register button
ttk.Button(..., command=generate_custom_report)
```

### Add New Setting
```python
# In rehman_accounting.py
value = settings_manager.get("new_setting", default="default")
settings_manager.set("new_setting", new_value)
```

### Add New Message
```python
# In constants.py
MSG_NEW_EVENT: Final[str] = "New event message"

# In rehman_accounting.py
set_status(MSG_NEW_EVENT)
```

---

## Performance Considerations

1. **Large Datasets**
   - Tree animation skipped for >180 rows
   - Indexes on frequently-queried columns
   - Limit report date ranges

2. **Database Operations**
   - Transactions for multi-statement operations
   - Foreign keys prevent orphaned records
   - Triggers enforce constraints at DB level

3. **UI Responsiveness**
   - Animations use easing functions
   - Status messages auto-revert
   - Background tasks can be added for long operations

---

## Future Improvements

### Phase 2: Advanced Architecture
```
├── Create UIFrame base class
├── Separate UI sections into classes
├── Add dependency injection
└── Implement service layer
```

### Phase 3: Testing Framework
```
├── Unit tests for validators
├── Integration tests for database
├── UI test framework setup
└── Mock database for tests
```

### Phase 4: Advanced Features
```
├── Multi-user support
├── Database encryption
├── Cloud sync
└── REST API
```

---

## Debugging Guide

### Enable Debug Logging
```python
# In rehman_accounting.py
logging.basicConfig(level=logging.DEBUG)
```

### Check Database State
```python
is_ok, msg = db.check_integrity()
print(msg)

# Or SQL
SELECT * FROM accounts;
SELECT * FROM vouchers WHERE posted = 1;
```

### Validate Settings File
```bash
cat "%USERPROFILE%\RIAS_Data\settings.json"
```

### Monitor Application Logs
```bash
tail -f "%USERPROFILE%\RIAS_Data\rias.log"
```

---

## Summary

This architecture provides:
- ✅ **Modularity** - Easy to maintain and extend
- ✅ **Separation of Concerns** - Each module has clear responsibility
- ✅ **Type Safety** - Type hints catch errors early
- ✅ **Consistency** - Centralized constants and messages
- ✅ **Persistence** - User preferences saved automatically
- ✅ **Reliability** - Database constraints and triggers
- ✅ **Maintainability** - Clear documentation and patterns

