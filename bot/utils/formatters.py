from datetime import datetime

from app.models.order import Order, OrderStatus

STATUS_LABELS = {
    OrderStatus.PENDING.value: "Pending",
    OrderStatus.IN_PROGRESS.value: "In Progress",
    OrderStatus.DELIVERED.value: "Delivered",
    OrderStatus.CANCELED.value: "Canceled",
}


def format_date(dt: datetime | None) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%b %d, %Y %H:%M")


def format_date_short(dt: datetime | None) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%b %d")


def format_order_short(order: Order) -> str:
    status = STATUS_LABELS.get(order.status, order.status)
    return (
        f"#{order.id} | {order.bottle_count} bottles | "
        f"{status} | {format_date_short(order.created_at)}"
    )


def format_order_detail(order: Order) -> str:
    status = STATUS_LABELS.get(order.status, order.status)
    lines = [
        f"Order #{order.id}",
        f"Status: {status}",
        f"Bottles: {order.bottle_count}",
        f"Address: {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Notes: {order.delivery_notes}")
    lines.append(f"Created: {format_date(order.created_at)}")
    if order.admin:
        lines.append(f"Admin: {order.admin.full_name}")
    if order.notes:
        lines.append(f"Admin notes: {order.notes}")
    return "\n".join(lines)


def format_order_for_admin(order: Order) -> str:
    customer = order.customer
    lines = [
        f"#{order.id} - {customer.full_name}",
        f"{order.bottle_count} bottles | {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Notes: {order.delivery_notes}")
    return "\n".join(lines)


def format_order_for_admin_detail(order: Order) -> str:
    customer = order.customer
    lines = [
        f"Order #{order.id}",
        f"Customer: {customer.full_name}",
        f"Phone: {customer.phone}",
        f"Address: {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Notes: {order.delivery_notes}")
    lines.append(f"Bottles: {order.bottle_count}")
    return "\n".join(lines)


def format_bottle_stats(stats: dict) -> str:
    return (
        f"Total ordered:     {stats['total_ordered']}\n"
        f"Total delivered:   {stats['total_delivered']}\n"
        f"Returned:          {stats['total_returned']}\n"
        f"Currently in hand: {stats['bottles_in_hand']}\n"
        f"Pending:           {stats['pending_bottles']}"
    )


def format_admin_inventory(inv: dict) -> str:
    lines = [
        "Your Bottle Inventory",
        "-----------------------------",
        f"Received from supplier:  {inv['total_received']}",
        f"Delivered to customers:  {inv['total_delivered']}",
        f"Current stock (full):    {inv['current_stock']}",
        "-----------------------------",
        f"Empties collected:       {inv['empties_collected']}",
        "-----------------------------",
        f"Pending: {inv['pending_bottles']} bottles across {inv['pending_orders']} orders",
    ]
    return "\n".join(lines)
