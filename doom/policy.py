"""DOOM data classification and trust-boundary policy."""
from __future__ import annotations
from enum import Enum

class DataClass(str, Enum):
    PROTECTED = "protected"
    CONTROLLED = "controlled"
    NORMAL = "normal"

PROTECTED_TAGS = {
    "password", "passwords", "secret", "secrets", "pin", "bank_pin",
    "upi_pin", "recovery_code", "api_key", "private_key", "credential",
    "bank_account", "financial", "legal", "authentication_token",
}

def classify(tags: set[str] | None = None, *, explicit: DataClass | None = None) -> DataClass:
    if explicit is not None:
        return explicit
    normalized = {tag.strip().lower() for tag in (tags or set())}
    return DataClass.PROTECTED if normalized & PROTECTED_TAGS else DataClass.NORMAL

def can_leave_local_device(data_class: DataClass, *, explicitly_authorized: bool = False) -> bool:
    if data_class == DataClass.PROTECTED:
        return explicitly_authorized
    return True
