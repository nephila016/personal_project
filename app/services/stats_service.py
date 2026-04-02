from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.services import bottle_service


def get_global_stats(session: Session) -> dict:
    total_orders = session.query(func.count(Order.id)).scalar()
    pending = (
        session.query(func.count(Order.id))
        .filter(Order.status == OrderStatus.PENDING.value)
        .scalar()
    )
    in_progress = (
        session.query(func.count(Order.id))
        .filter(Order.status == OrderStatus.IN_PROGRESS.value)
        .scalar()
    )
    delivered = (
        session.query(func.count(Order.id))
        .filter(Order.status == OrderStatus.DELIVERED.value)
        .scalar()
    )
    canceled = (
        session.query(func.count(Order.id))
        .filter(Order.status == OrderStatus.CANCELED.value)
        .scalar()
    )
    total_customers = (
        session.query(func.count(Customer.id))
        .filter(Customer.is_active == True)
        .scalar()
    )
    active_admins = (
        session.query(func.count(Admin.id))
        .filter(Admin.is_active == True)
        .scalar()
    )
    bottles = bottle_service.get_global_bottle_stats(session)

    return {
        "total_orders": total_orders,
        "pending_orders": pending,
        "in_progress_orders": in_progress,
        "delivered_orders": delivered,
        "canceled_orders": canceled,
        "total_customers": total_customers,
        "active_admins": active_admins,
        "bottles": bottles,
    }


def get_orders_by_day(session: Session, days: int = 30) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        session.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("count"),
        )
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    return [{"date": str(r.day), "count": r.count} for r in rows]


def get_orders_by_status(session: Session) -> dict:
    rows = (
        session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    return {status: count for status, count in rows}


def get_stale_orders(session: Session, hours: int | None = None) -> list[Order]:
    from config import Config

    h = hours or Config.STALE_ORDER_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=h)
    return (
        session.query(Order)
        .filter(
            Order.status == OrderStatus.IN_PROGRESS.value,
            Order.status_changed_at < cutoff,
        )
        .order_by(Order.status_changed_at.asc())
        .all()
    )


def get_recent_activity(session: Session, limit: int = 10):
    from app.models.order_status_log import OrderStatusLog

    return (
        session.query(OrderStatusLog)
        .order_by(OrderStatusLog.changed_at.desc())
        .limit(limit)
        .all()
    )
