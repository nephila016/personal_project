from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatusLog(Base):
    __tablename__ = "order_status_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))
    changed_by_customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id")
    )
    changed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text)

    order = relationship("Order", back_populates="status_logs")

    def __repr__(self):
        return f"<StatusLog order={self.order_id}: {self.old_status}->{self.new_status}>"
