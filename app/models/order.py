import enum
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class CanceledBy(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SYSTEM = "system"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("bottle_count > 0", name="ck_orders_bottle_count_positive"),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'delivered', 'canceled')",
            name="ck_orders_status_valid",
        ),
        CheckConstraint(
            "canceled_by IS NULL OR canceled_by IN ('customer', 'admin', 'system')",
            name="ck_orders_canceled_by_valid",
        ),
        Index("ix_orders_customer_status", "customer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id"), index=True
    )
    bottle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default=OrderStatus.PENDING.value, nullable=False, index=True
    )
    canceled_by: Mapped[str | None] = mapped_column(String(20))
    status_changed_at: Mapped[datetime | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    customer = relationship("Customer", back_populates="orders")
    admin = relationship("Admin", back_populates="orders")
    status_logs = relationship(
        "OrderStatusLog", back_populates="order", order_by="OrderStatusLog.changed_at"
    )

    @property
    def status_enum(self) -> OrderStatus:
        return OrderStatus(self.status)

    def __repr__(self):
        return f"<Order {self.id}: {self.bottle_count} bottles, {self.status}>"
