import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models.order import CanceledBy, Order, OrderStatus
from app.models.order_status_log import OrderStatusLog
from app.services import bottle_service
from config import Config

logger = logging.getLogger("orders")

VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELED],
    OrderStatus.IN_PROGRESS: [
        OrderStatus.DELIVERED,
        OrderStatus.CANCELED,
        OrderStatus.PENDING,  # reassignment by global admin
    ],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELED: [],
}


def can_create_order(
    session: Session, customer_id: int, bottle_count: int
) -> tuple[bool, str]:
    active_count = (
        session.query(func.count(Order.id))
        .filter(
            Order.customer_id == customer_id,
            Order.status.in_(
                [OrderStatus.PENDING.value, OrderStatus.IN_PROGRESS.value]
            ),
        )
        .scalar()
    )
    if active_count >= Config.MAX_PENDING_ORDERS_PER_CUSTOMER:
        return (
            False,
            f"You already have {active_count} active orders. Please wait or cancel one.",
        )

    cooldown = datetime.now(timezone.utc) - timedelta(
        seconds=Config.DUPLICATE_ORDER_COOLDOWN_SECONDS
    )
    recent = (
        session.query(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.bottle_count == bottle_count,
            Order.created_at > cooldown,
        )
        .first()
    )
    if recent:
        return False, f"You just placed a similar order (#{recent.id}). Please wait."

    return True, ""


def create_order(
    session: Session,
    customer_id: int,
    bottle_count: int,
    delivery_address: str,
    delivery_notes: str | None = None,
) -> Order:
    ok, msg = can_create_order(session, customer_id, bottle_count)
    if not ok:
        raise ValueError(msg)

    order = Order(
        customer_id=customer_id,
        bottle_count=bottle_count,
        delivery_address=delivery_address.strip(),
        delivery_notes=delivery_notes.strip() if delivery_notes else None,
        status=OrderStatus.PENDING.value,
    )
    session.add(order)
    session.flush()

    log = OrderStatusLog(
        order_id=order.id,
        old_status=None,
        new_status=OrderStatus.PENDING.value,
        changed_by_customer_id=customer_id,
    )
    session.add(log)
    session.flush()
    logger.info("ORDER_CREATED | order_id=%d | customer_id=%d | bottles=%d | address=%s",
                order.id, customer_id, bottle_count, delivery_address.strip())
    return order


def claim_order(
    session: Session, order_id: int, admin_id: int, expected_version: int
) -> Order | None:
    now = datetime.now(timezone.utc)
    result = session.execute(
        update(Order)
        .where(
            Order.id == order_id,
            Order.status == OrderStatus.PENDING.value,
            Order.version == expected_version,
        )
        .values(
            status=OrderStatus.IN_PROGRESS.value,
            admin_id=admin_id,
            version=Order.version + 1,
            status_changed_at=now,
            updated_at=now,
        )
    )
    if result.rowcount == 0:
        return None

    session.add(
        OrderStatusLog(
            order_id=order_id,
            old_status=OrderStatus.PENDING.value,
            new_status=OrderStatus.IN_PROGRESS.value,
            changed_by_admin_id=admin_id,
        )
    )
    session.flush()
    logger.info("ORDER_CLAIMED | order_id=%d | admin_id=%d", order_id, admin_id)

    return session.get(Order, order_id)


def mark_delivered(
    session: Session, order_id: int, admin_id: int, expected_version: int
) -> Order | None:
    order = session.get(Order, order_id)
    if not order or order.admin_id != admin_id:
        return None

    stock = bottle_service.get_admin_stock(session, admin_id)
    if stock < order.bottle_count:
        raise ValueError(
            f"Insufficient stock. You have {stock} bottles but need {order.bottle_count}. "
            "Use /receive to restock."
        )

    now = datetime.now(timezone.utc)
    result = session.execute(
        update(Order)
        .where(
            Order.id == order_id,
            Order.status == OrderStatus.IN_PROGRESS.value,
            Order.admin_id == admin_id,
            Order.version == expected_version,
        )
        .values(
            status=OrderStatus.DELIVERED.value,
            version=Order.version + 1,
            status_changed_at=now,
            updated_at=now,
        )
    )
    if result.rowcount == 0:
        return None

    session.add(
        OrderStatusLog(
            order_id=order_id,
            old_status=OrderStatus.IN_PROGRESS.value,
            new_status=OrderStatus.DELIVERED.value,
            changed_by_admin_id=admin_id,
        )
    )
    session.flush()
    logger.info("ORDER_DELIVERED | order_id=%d | admin_id=%d | bottles=%d",
                order_id, admin_id, order.bottle_count)
    return session.get(Order, order_id)


def cancel_order(
    session: Session,
    order_id: int,
    expected_version: int,
    canceled_by: str,
    reason: str | None = None,
    admin_id: int | None = None,
    customer_id: int | None = None,
) -> Order | None:
    order = session.get(Order, order_id)
    if not order:
        return None

    if order.status in (OrderStatus.DELIVERED.value, OrderStatus.CANCELED.value):
        return None

    if (
        order.status == OrderStatus.IN_PROGRESS.value
        and canceled_by == CanceledBy.CUSTOMER.value
    ):
        return None

    now = datetime.now(timezone.utc)
    result = session.execute(
        update(Order)
        .where(
            Order.id == order_id,
            Order.version == expected_version,
            Order.status.in_(
                [OrderStatus.PENDING.value, OrderStatus.IN_PROGRESS.value]
            ),
        )
        .values(
            status=OrderStatus.CANCELED.value,
            canceled_by=canceled_by,
            notes=reason,
            version=Order.version + 1,
            status_changed_at=now,
            updated_at=now,
        )
    )
    if result.rowcount == 0:
        return None

    session.add(
        OrderStatusLog(
            order_id=order_id,
            old_status=order.status,
            new_status=OrderStatus.CANCELED.value,
            changed_by_admin_id=admin_id,
            changed_by_customer_id=customer_id,
            note=reason,
        )
    )
    session.flush()
    logger.info("ORDER_CANCELED | order_id=%d | canceled_by=%s | reason=%s",
                order_id, canceled_by, reason or "N/A")
    return session.get(Order, order_id)


def reassign_order(session: Session, order_id: int, expected_version: int) -> Order | None:
    """Global admin reassigns an in_progress order back to pending."""
    now = datetime.now(timezone.utc)
    result = session.execute(
        update(Order)
        .where(
            Order.id == order_id,
            Order.status == OrderStatus.IN_PROGRESS.value,
            Order.version == expected_version,
        )
        .values(
            status=OrderStatus.PENDING.value,
            admin_id=None,
            version=Order.version + 1,
            status_changed_at=now,
            updated_at=now,
        )
    )
    if result.rowcount == 0:
        return None

    session.add(
        OrderStatusLog(
            order_id=order_id,
            old_status=OrderStatus.IN_PROGRESS.value,
            new_status=OrderStatus.PENDING.value,
            note="Reassigned by global admin",
        )
    )
    session.flush()
    return session.get(Order, order_id)


def get_pending_orders(session: Session, limit: int = 5, offset: int = 0):
    q = session.query(Order).filter(Order.status == OrderStatus.PENDING.value)
    total = q.count()
    items = q.order_by(Order.created_at.asc()).offset(offset).limit(limit).all()
    return items, total


def get_admin_active_orders(session: Session, admin_id: int) -> list[Order]:
    return (
        session.query(Order)
        .filter(
            Order.admin_id == admin_id,
            Order.status == OrderStatus.IN_PROGRESS.value,
        )
        .order_by(Order.created_at.asc())
        .all()
    )


def get_customer_orders(
    session: Session, customer_id: int, limit: int = 5, offset: int = 0
):
    q = session.query(Order).filter(Order.customer_id == customer_id)
    total = q.count()
    items = (
        q.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
    )
    return items, total


def get_customer_pending_orders(session: Session, customer_id: int) -> list[Order]:
    return (
        session.query(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.status == OrderStatus.PENDING.value,
        )
        .order_by(Order.created_at.desc())
        .all()
    )


def get_customer_last_delivered(session: Session, customer_id: int) -> Order | None:
    return (
        session.query(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.status == OrderStatus.DELIVERED.value,
        )
        .order_by(Order.updated_at.desc())
        .first()
    )


def get_order_with_logs(session: Session, order_id: int) -> Order | None:
    return session.get(Order, order_id)


def list_orders(
    session: Session,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    customer_id: int | None = None,
    admin_id: int | None = None,
    search: str | None = None,
):
    from app.models.customer import Customer

    q = session.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)
    if admin_id:
        q = q.filter(Order.admin_id == admin_id)
    if search:
        q = q.join(Customer).filter(
            Customer.full_name.ilike(f"%{search}%")
            | Customer.phone.like(f"%{search}%")
        )
    total = q.count()
    items = (
        q.order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total
