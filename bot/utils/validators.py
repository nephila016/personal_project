import re


def normalize_phone(raw: str) -> str:
    return re.sub(r"[^\d+]", "", raw)


def validate_phone(phone: str) -> bool:
    normalized = normalize_phone(phone)
    return bool(re.match(r"^\+?\d{7,15}$", normalized))


def validate_name(name: str) -> bool:
    stripped = name.strip()
    return 2 <= len(stripped) <= 100


def validate_address(address: str) -> bool:
    stripped = address.strip()
    return 0 < len(stripped) <= 500


def validate_bottle_count(value: str, max_count: int = 50) -> int | None:
    try:
        n = int(value.strip())
        if 1 <= n <= max_count:
            return n
    except (ValueError, TypeError):
        pass
    return None


def validate_receipt_quantity(value: str, max_qty: int = 1000) -> int | None:
    try:
        n = int(value.strip())
        if n > 0:
            return n
    except (ValueError, TypeError):
        pass
    return None
