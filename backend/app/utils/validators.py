"""
Input Validation Utilities
"""

import re

CUSTOMER_ID_REGEX = re.compile(r"^CUST_\d{4}$")


def is_valid_customer_id(customer_id: str) -> bool:
    """Validates that customer_id adheres to standard format (e.g. CUST_0001)."""
    if not isinstance(customer_id, str):
        return False
    return bool(CUSTOMER_ID_REGEX.match(customer_id.strip()))
