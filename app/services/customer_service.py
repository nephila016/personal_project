import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.customer import Customer


def normalize_phone(raw: str) -> str:
    """Strip spaces, dashes, parens from phone. Keep leading +."""
    stripped = re.sub(r"[^\d+]", "", raw)
    if not stripped.startswith("+"):
        stripped = stripped.lstrip("+")
    return stripped


def validate_phone(phone: str) -> bool:
    normalized = normalize_phone(phone)
    return bool(re.match(r"^\+?\d{7,15}$", normalized))


def register_customer(
    session: Session,
    telegram_id: int,
    full_name: str,
    address: str,
    phone: str,
    telegram_username: str | None = None,
) -> Customer:
    normalized = normalize_phone(phone)
    existing = session.query(Customer).filter(Customer.phone == normalized).first()
    if existing:
        raise ValueError(f"Phone number {normalized} is already registered.")

    customer = Customer(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        full_name=full_name.strip(),
        address=address.strip(),
        phone=normalized,
    )
    session.add(customer)
    session.flush()
    return customer


def get_by_telegram_id(session: Session, telegram_id: int) -> Customer | None:
    return (
        session.query(Customer).filter(Customer.telegram_id == telegram_id).first()
    )


def get_by_id(session: Session, customer_id: int) -> Customer | None:
    return session.get(Customer, customer_id)


def get_by_phone(session: Session, phone: str) -> Customer | None:
    normalized = normalize_phone(phone)
    return session.query(Customer).filter(Customer.phone == normalized).first()


def search_customers(session: Session, query: str, limit: int = 10) -> list[Customer]:
    normalized = normalize_phone(query)
    return (
        session.query(Customer)
        .filter(
            Customer.is_active == True,
            or_(
                Customer.full_name.ilike(f"%{query}%"),
                Customer.phone.like(f"%{normalized}%"),
            ),
        )
        .limit(limit)
        .all()
    )


def update_customer(session: Session, customer_id: int, **fields) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("Customer not found")
    if "phone" in fields:
        fields["phone"] = normalize_phone(fields["phone"])
    for key, value in fields.items():
        if hasattr(customer, key):
            setattr(customer, key, value.strip() if isinstance(value, str) else value)
    session.flush()
    return customer


def list_customers(
    session: Session,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
):
    q = session.query(Customer)
    if is_active is not None:
        q = q.filter(Customer.is_active == is_active)
    if search:
        normalized = normalize_phone(search)
        q = q.filter(
            or_(
                Customer.full_name.ilike(f"%{search}%"),
                Customer.phone.like(f"%{normalized}%"),
            )
        )
    total = q.count()
    items = (
        q.order_by(Customer.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total
