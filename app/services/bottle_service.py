from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.order import Order, OrderStatus


def get_admin_stock(session: Session, admin_id: int) -> int:
    received = (
        session.query(func.coalesce(func.sum(BottleReceipt.quantity), 0))
        .filter(BottleReceipt.admin_id == admin_id)
        .scalar()
    )
    delivered = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.admin_id == admin_id,
            Order.status == OrderStatus.DELIVERED.value,
        )
        .scalar()
    )
    return received - delivered


def get_admin_inventory(session: Session, admin_id: int) -> dict:
    received = (
        session.query(func.coalesce(func.sum(BottleReceipt.quantity), 0))
        .filter(BottleReceipt.admin_id == admin_id)
        .scalar()
    )
    delivered = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.admin_id == admin_id,
            Order.status == OrderStatus.DELIVERED.value,
        )
        .scalar()
    )
    empties = (
        session.query(func.coalesce(func.sum(BottleReturn.quantity), 0))
        .filter(BottleReturn.admin_id == admin_id)
        .scalar()
    )
    pending_q = (
        session.query(
            func.coalesce(func.sum(Order.bottle_count), 0),
            func.count(Order.id),
        )
        .filter(
            Order.admin_id == admin_id,
            Order.status == OrderStatus.IN_PROGRESS.value,
        )
        .first()
    )
    return {
        "total_received": received,
        "total_delivered": delivered,
        "current_stock": received - delivered,
        "empties_collected": empties,
        "pending_bottles": pending_q[0],
        "pending_orders": pending_q[1],
    }


def get_customer_bottles(session: Session, customer_id: int) -> dict:
    total_ordered = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.customer_id == customer_id,
            Order.status != OrderStatus.CANCELED.value,
        )
        .scalar()
    )
    total_delivered = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.customer_id == customer_id,
            Order.status == OrderStatus.DELIVERED.value,
        )
        .scalar()
    )
    total_returned = (
        session.query(func.coalesce(func.sum(BottleReturn.quantity), 0))
        .filter(BottleReturn.customer_id == customer_id)
        .scalar()
    )
    total_pending = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.customer_id == customer_id,
            Order.status.in_(
                [OrderStatus.PENDING.value, OrderStatus.IN_PROGRESS.value]
            ),
        )
        .scalar()
    )
    return {
        "total_ordered": total_ordered,
        "total_delivered": total_delivered,
        "total_returned": total_returned,
        "bottles_in_hand": total_delivered - total_returned,
        "pending_bottles": total_pending,
    }


def record_receipt(
    session: Session, admin_id: int, quantity: int, notes: str | None = None
) -> BottleReceipt:
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    receipt = BottleReceipt(
        admin_id=admin_id,
        quantity=quantity,
        notes=notes.strip() if notes else None,
    )
    session.add(receipt)
    session.flush()
    return receipt


def record_return(
    session: Session,
    customer_id: int,
    admin_id: int,
    quantity: int,
    notes: str | None = None,
) -> BottleReturn:
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

    stats = get_customer_bottles(session, customer_id)
    if quantity > stats["bottles_in_hand"]:
        raise ValueError(
            f"Cannot return {quantity} bottles. Customer only has "
            f"{stats['bottles_in_hand']} in hand."
        )

    bottle_return = BottleReturn(
        customer_id=customer_id,
        admin_id=admin_id,
        quantity=quantity,
        notes=notes.strip() if notes else None,
    )
    session.add(bottle_return)
    session.flush()
    return bottle_return


def get_global_bottle_stats(session: Session) -> dict:
    total_received = (
        session.query(func.coalesce(func.sum(BottleReceipt.quantity), 0)).scalar()
    )
    total_delivered = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(Order.status == OrderStatus.DELIVERED.value)
        .scalar()
    )
    total_returned = (
        session.query(func.coalesce(func.sum(BottleReturn.quantity), 0)).scalar()
    )
    total_pending = (
        session.query(func.coalesce(func.sum(Order.bottle_count), 0))
        .filter(
            Order.status.in_(
                [OrderStatus.PENDING.value, OrderStatus.IN_PROGRESS.value]
            )
        )
        .scalar()
    )
    return {
        "total_received": total_received,
        "total_delivered": total_delivered,
        "admin_stock": total_received - total_delivered,
        "total_returned": total_returned,
        "customer_in_hand": total_delivered - total_returned,
        "pending_delivery": total_pending,
    }
