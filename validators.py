"""
Input validation utilities for RIAS.
Centralizes all validation logic for dates, amounts, and account data.
"""

from datetime import datetime
from typing import Optional, Tuple
from constants import DATE_FORMAT, FLOAT_PRECISION, ACCOUNT_TYPES


def validate_date(value: str) -> bool:
    """
    Validate if a string is a valid date in YYYY-MM-DD format.

    Args:
        value: Date string to validate.

    Returns:
        True if valid date, False otherwise.
    """
    try:
        datetime.strptime(value.strip(), DATE_FORMAT)
        return True
    except (ValueError, AttributeError):
        return False


def validate_amount(value: str) -> Optional[float]:
    """
    Parse and validate an amount string.

    Args:
        value: Amount string to parse (e.g., "100.50").

    Returns:
        Rounded float if valid, None if invalid.
    """
    try:
        amount = float((value or "").strip() or 0)
        return round(amount, FLOAT_PRECISION)
    except (TypeError, ValueError):
        return None


def validate_positive_amount(value: str) -> Optional[float]:
    """
    Parse and validate a positive amount.

    Args:
        value: Amount string to validate.

    Returns:
        Rounded float if valid and positive, None otherwise.
    """
    amount = validate_amount(value)
    if amount is not None and amount >= 0:
        return amount
    return None


def validate_debit_credit_pair(
    debit_str: str, credit_str: str
) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Validate debit/credit pair: one must be > 0, the other = 0.

    Args:
        debit_str: Debit amount string.
        credit_str: Credit amount string.

    Returns:
        Tuple of (is_valid, debit, credit). Valid pairs have exactly one > 0.
    """
    debit = validate_positive_amount(debit_str)
    credit = validate_positive_amount(credit_str)

    if debit is None or credit is None:
        return False, None, None

    # Valid: exactly one must be > 0
    if (debit > 0 and credit == 0) or (credit > 0 and debit == 0):
        return True, debit, credit

    return False, debit, credit


def validate_date_range(start_str: str, end_str: str) -> Tuple[bool, Optional[Tuple[str, str]]]:
    """
    Validate a date range.

    Args:
        start_str: Start date string.
        end_str: End date string.

    Returns:
        Tuple of (is_valid, (start, end)) if valid, (False, None) otherwise.
    """
    if not validate_date(start_str) or not validate_date(end_str):
        return False, None

    start = start_str.strip()
    end = end_str.strip()

    if start > end:
        return False, None

    return True, (start, end)


def validate_account_name(name: str) -> bool:
    """
    Validate an account name (non-empty, not too long).

    Args:
        name: Account name to validate.

    Returns:
        True if valid, False otherwise.
    """
    name = (name or "").strip()
    return len(name) > 0 and len(name) <= 255


def validate_account_type(account_type: str) -> bool:
    """
    Validate that account type is one of the allowed types.

    Args:
        account_type: Account type to validate.

    Returns:
        True if valid, False otherwise.
    """
    return (account_type or "").strip() in ACCOUNT_TYPES


def validate_account_data(
    name: str, account_type: str
) -> Tuple[bool, str]:
    """
    Validate complete account data.

    Args:
        name: Account name.
        account_type: Account type.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not validate_account_name(name):
        return False, "Account name is required"

    if not validate_account_type(account_type):
        return False, f"Invalid account type. Must be one of: {', '.join(ACCOUNT_TYPES)}"

    return True, ""


def format_amount(amount: float) -> str:
    """
    Format a float amount as currency string with thousands separator.

    Args:
        amount: Numeric amount.

    Returns:
        Formatted string (e.g., "1,234.56").
    """
    return f"{amount:,.2f}"


def parse_cash_account_names(raw_input: str) -> list[str]:
    """
    Parse comma-separated cash account names from user input.

    Args:
        raw_input: Comma-separated account names.

    Returns:
        List of trimmed account names.
    """
    return [n.strip() for n in raw_input.split(",") if n.strip()]
