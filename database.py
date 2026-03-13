"""
Database module for RIAS.
Handles SQLite database initialization, schema management, and queries.
"""

import sqlite3
import logging
from typing import Any, List, Optional, Tuple
from constants import FLOAT_PRECISION


class Database:
    """
    SQLite database wrapper with schema initialization and query helpers.
    Manages double-entry bookkeeping database operations.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize database connection and create schema if needed.

        Args:
            db_path: Path to the SQLite database file.

        Raises:
            sqlite3.DatabaseError: If database connection fails.
        """
        self.path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cur = self.conn.cursor()
        self._init_schema()
        logging.info(f"Database initialized: {db_path}")

    def _init_schema(self) -> None:
        """
        Create database schema if it doesn't exist.
        Sets up accounts, vouchers, transactions tables and related triggers.
        """
        # Create accounts table
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('Asset','Liability','Income','Expense'))
        )
        """)

        # Create vouchers table
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT,
            posted INTEGER NOT NULL DEFAULT 0 CHECK (posted IN (0, 1))
        )
        """)

        # Create transactions table
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit REAL NOT NULL DEFAULT 0 CHECK (debit >= 0),
            credit REAL NOT NULL DEFAULT 0 CHECK (credit >= 0),
            CHECK (
                (debit > 0 AND credit = 0) OR
                (credit > 0 AND debit = 0)
            ),
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        """)

        # Create indexes for performance
        self.cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_voucher ON transactions(voucher_id)"
        )
        self.cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id)"
        )
        self.cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_voucher_date ON vouchers(date)"
        )

        # Add posted column if it doesn't exist (migration support)
        voucher_cols = [
            r[1] for r in self.cur.execute("PRAGMA table_info(vouchers)").fetchall()
        ]
        if "posted" not in voucher_cols:
            self.cur.execute(
                "ALTER TABLE vouchers ADD COLUMN posted INTEGER NOT NULL DEFAULT 0"
            )

        # Update posted status based on transaction balance
        self.cur.execute("""
        UPDATE vouchers
        SET posted = CASE
            WHEN EXISTS (SELECT 1 FROM transactions t WHERE t.voucher_id = vouchers.id)
             AND ROUND((SELECT COALESCE(SUM(t1.debit), 0) FROM transactions t1 WHERE t1.voucher_id = vouchers.id), 2)
                 = ROUND((SELECT COALESCE(SUM(t2.credit), 0) FROM transactions t2 WHERE t2.voucher_id = vouchers.id), 2)
            THEN 1 ELSE 0
        END
        """)

        # Trigger: Prevent inserting transactions into posted vouchers
        self.cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_tx_no_insert_posted
        BEFORE INSERT ON transactions
        FOR EACH ROW
        WHEN COALESCE((SELECT posted FROM vouchers WHERE id = NEW.voucher_id), 0) = 1
        BEGIN
            SELECT RAISE(ABORT, 'Cannot modify a posted voucher');
        END;
        """)

        # Trigger: Prevent updating transactions in posted vouchers
        self.cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_tx_no_update_posted
        BEFORE UPDATE ON transactions
        FOR EACH ROW
        WHEN COALESCE((SELECT posted FROM vouchers WHERE id = OLD.voucher_id), 0) = 1
             OR COALESCE((SELECT posted FROM vouchers WHERE id = NEW.voucher_id), 0) = 1
        BEGIN
            SELECT RAISE(ABORT, 'Cannot modify a posted voucher');
        END;
        """)

        # Trigger: Prevent deleting transactions from posted vouchers
        self.cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_tx_no_delete_posted
        BEFORE DELETE ON transactions
        FOR EACH ROW
        WHEN COALESCE((SELECT posted FROM vouchers WHERE id = OLD.voucher_id), 0) = 1
        BEGIN
            SELECT RAISE(ABORT, 'Cannot modify a posted voucher');
        END;
        """)

        # Trigger: Validate voucher balance before posting
        self.cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_voucher_post_balanced
        BEFORE UPDATE OF posted ON vouchers
        FOR EACH ROW
        WHEN NEW.posted = 1
        BEGIN
            SELECT CASE
                WHEN (SELECT COUNT(*) FROM transactions WHERE voucher_id = NEW.id) < 2
                THEN RAISE(ABORT, 'Voucher must contain at least two lines before posting')
            END;
            SELECT CASE
                WHEN ROUND((SELECT COALESCE(SUM(debit), 0) FROM transactions WHERE voucher_id = NEW.id), 2)
                   <> ROUND((SELECT COALESCE(SUM(credit), 0) FROM transactions WHERE voucher_id = NEW.id), 2)
                THEN RAISE(ABORT, 'Voucher debit and credit totals must be equal before posting')
            END;
        END;
        """)

        self.conn.commit()
        logging.info("Database schema initialized")

    def execute(
        self, query: str, params: Tuple[Any, ...] = (), commit: bool = True
    ) -> sqlite3.Cursor:
        """
        Execute a database query.

        Args:
            query: SQL query string.
            params: Query parameters (for parameterized queries).
            commit: Whether to commit changes immediately.

        Returns:
            Cursor object for result access.
        """
        self.cur.execute(query, params)
        if commit:
            self.conn.commit()
        return self.cur

    def fetch_one(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> Optional[Tuple[Any, ...]]:
        """
        Fetch a single row from the database.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Single row as tuple, or None if no results.
        """
        return self.cur.execute(query, params).fetchone()

    def fetch_all(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> List[Tuple[Any, ...]]:
        """
        Fetch all rows matching a query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            List of rows as tuples.
        """
        return self.cur.execute(query, params).fetchall()

    def commit(self) -> None:
        """Commit any pending transactions."""
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
        logging.info("Database connection closed")

    def check_integrity(self) -> Tuple[bool, str]:
        """
        Check database integrity using SQLite PRAGMA.

        Returns:
            Tuple of (is_ok, message).
        """
        try:
            result = self.fetch_one("PRAGMA integrity_check")
            if result and result[0].lower() == "ok":
                return True, "Database integrity OK"
            msg = result[0] if result else "Unknown error"
            return False, f"Integrity check failed: {msg}"
        except Exception as e:
            return False, f"Integrity check error: {str(e)}"
