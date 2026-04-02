from datetime import datetime

from app.models.order import Order, OrderStatus

STATUS_LABELS = {
    OrderStatus.PENDING.value: "Ожидание",
    OrderStatus.IN_PROGRESS.value: "В процессе",
    OrderStatus.DELIVERED.value: "Доставлен",
    OrderStatus.CANCELED.value: "Отменён",
}


def format_date(dt: datetime | None) -> str:
    if not dt:
        return "Н/Д"
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date_short(dt: datetime | None) -> str:
    if not dt:
        return "Н/Д"
    return dt.strftime("%d.%m")


def format_order_short(order: Order) -> str:
    status = STATUS_LABELS.get(order.status, order.status)
    return (
        f"#{order.id} | {order.bottle_count} бут. | "
        f"{status} | {format_date_short(order.created_at)}"
    )


def format_order_short_from_dict(data: dict) -> str:
    """Format order summary from a plain dict (no ORM access)."""
    status = STATUS_LABELS.get(data.get("status", ""), data.get("status", ""))
    created = data.get("created_at")
    date_str = format_date_short(created) if created else "Н/Д"
    return (
        f"#{data['id']} | {data['bottle_count']} бут. | "
        f"{status} | {date_str}"
    )


def format_order_detail(order: Order) -> str:
    status = STATUS_LABELS.get(order.status, order.status)
    lines = [
        f"Заказ #{order.id}",
        f"Статус: {status}",
        f"Бутылки: {order.bottle_count}",
        f"Адрес: {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Примечания: {order.delivery_notes}")
    lines.append(f"Создан: {format_date(order.created_at)}")
    if order.admin:
        lines.append(f"Администратор: {order.admin.full_name}")
    if order.notes:
        lines.append(f"Заметки администратора: {order.notes}")
    return "\n".join(lines)


def format_order_for_admin(order: Order) -> str:
    customer = order.customer
    lines = [
        f"#{order.id} - {customer.full_name}",
        f"{order.bottle_count} бут. | {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Примечания: {order.delivery_notes}")
    return "\n".join(lines)


def format_order_for_admin_detail(order: Order) -> str:
    customer = order.customer
    lines = [
        f"Заказ #{order.id}",
        f"Клиент: {customer.full_name}",
        f"Телефон: {customer.phone}",
        f"Адрес: {order.delivery_address}",
    ]
    if order.delivery_notes:
        lines.append(f"Примечания: {order.delivery_notes}")
    lines.append(f"Бутылки: {order.bottle_count}")
    return "\n".join(lines)


def format_bottle_stats(stats: dict) -> str:
    return (
        f"Всего заказано:      {stats['total_ordered']}\n"
        f"Всего доставлено:    {stats['total_delivered']}\n"
        f"Возвращено:          {stats['total_returned']}\n"
        f"Сейчас на руках:     {stats['bottles_in_hand']}\n"
        f"Ожидание:            {stats['pending_bottles']}"
    )


def format_admin_inventory(inv: dict) -> str:
    lines = [
        "Ваш инвентарь бутылок",
        "-----------------------------",
        f"Получено от поставщика:  {inv['total_received']}",
        f"Доставлено клиентам:     {inv['total_delivered']}",
        f"Текущий запас (полных):  {inv['current_stock']}",
        "-----------------------------",
        f"Собрано пустых:          {inv['empties_collected']}",
        "-----------------------------",
        f"Ожидание: {inv['pending_bottles']} бут. в {inv['pending_orders']} заказах",
    ]
    return "\n".join(lines)
