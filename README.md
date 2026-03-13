RIAS (Rehman Industries Accounting System)
==========================================

Desktop double-entry bookkeeping app for small teams. Built with Python, Tkinter, and SQLite. RIAS centers everything around vouchers, keeps the ledger balanced with strict validation, and ships with ready-made financial reports plus CSV/PDF exports.

Why RIAS
--------
- Voucher-first workflow: debits and credits must balance before posting.
- Built-in guardrails: integrity check, unbalanced-voucher scan, and timestamped local backups.
- Ready reports: Trial Balance, Profit & Loss, Balance Sheet, General Ledger, and Cash Flow.
- Friendly UI: resizable layout, light/dark themes, keyboard shortcuts for speed.
- Offline and portable: single SQLite file under your home directory.

Quick Start
-----------
1) Install Python 3.9+ with Tkinter available.
2) Clone and enter the repo:
   - `git clone https://github.com/aribalodhi/Rehman-Industries-Accounting-System.git`
   - `cd Rehman-Industries-Accounting-System`
3) (Recommended) Create and activate a virtual environment:
   - `python -m venv .venv`
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4) Install dependencies:
   - `pip install -r requirements.txt`
5) Launch the app:
   - `python rehman_accounting.py`

Data Locations
--------------
- App data root: `~/RIAS_Data`
- Live database: `~/RIAS_Data/rehman_industries.db`
- Backups: `~/RIAS_Data/db_backups/rehman_industries_<tag>_<timestamp>.db`
- Log: `~/RIAS_Data/rias.log`
- Settings: `~/RIAS_Data/settings.json`
- First run: if the live DB is missing and a bundled seed is present, it will auto-copy.

Keyboard Shortcuts (highlights)
-------------------------------
- Navigation: `Ctrl+1` Accounts, `Ctrl+2` Voucher Entry, `Ctrl+3` Reports, `Ctrl+4` Voucher History, `Ctrl+5` Settings
- Voucher entry: `Ctrl+L` add line, `Ctrl+S` save voucher, `Ctrl+N` new voucher
- Reports: `Alt+T` Trial Balance, `Alt+P` P&L, `Alt+B` Balance Sheet, `Alt+G` GL, `Alt+C` Cash Flow, `Ctrl+E` CSV export, `Ctrl+Shift+E` PDF export, `Ctrl+P` Print

Packaging (optional)
--------------------
- Build a Windows executable with PyInstaller:
  - `pyinstaller --noconsole --name RIAS rehman_accounting.py`
  - Add `--icon <path-to-ico>` if you have a custom icon.
- Include the seed database next to the executable so first-run seeding works, or update `SEED_DB_PATH` in `constants.py`.

Project Structure
-----------------
- `rehman_accounting.py` — UI, event handlers, reporting, and app bootstrap.
- `constants.py` — paths, UI constants, themes, and schema metadata.
- `validators.py` — input validation and formatting helpers.
- `database.py` — SQLite wrapper, schema initialization, and integrity checks.
- `settings_manager.py` — user preferences (theme, window state) stored in JSON.
- `ARCHITECTURE.md` — deeper architectural notes and data flow.

Troubleshooting
---------------
- UI fails to start: confirm Tkinter is available in your Python build.
- Reset preferences: delete `~/RIAS_Data/settings.json` (a fresh one will be created).
- Ledger looks off: run the integrity check from Settings; review voucher history for flagged entries.

